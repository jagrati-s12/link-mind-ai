import uuid
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Resource, UserProfile, Resume, UserSkill
from app.services.ai_adapter import call_llm_json

def _extract_user_skills(db: Session, user_id: int) -> set:
    user_skills_list = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    user_skill_names = set(us.skill.name.lower() for us in user_skills_list if us.skill)
    active_resume = db.query(Resume).filter(Resume.user_id == user_id, Resume.is_active == True).first()
    if active_resume and active_resume.parsed_data:
        parsed = active_resume.parsed_data
        for s in parsed.get("technical_skills", []) + parsed.get("frameworks", []) + parsed.get("tools", []):
            user_skill_names.add(s.lower())
    return user_skill_names

def _map_saved_courses(saved_courses: List[Resource], keywords: List[str]) -> List[Dict[str, Any]]:
    matched = []
    seen = set()
    for c in saved_courses:
        if c.id in seen:
            continue
        c_text = f"{c.title} {c.description or ''}".lower()
        if any(kw.lower() in c_text for kw in keywords):
            seen.add(c.id)
            matched.append({
                "title": c.title,
                "url": c.direct_url or c.source_url or "",
                "type": "saved_course",
                "resource_id": c.id
            })
    return matched

def get_roadmap_catalog() -> List[Dict[str, Any]]:
    """Returns official curated roadmap.sh catalog presets for 1-click loading."""
    return [
        {
            "id": "ai-engineer",
            "title": "AI Engineer",
            "category": "Artificial Intelligence",
            "badge": "AI / ML",
            "target_role": "AI Engineer / Generative AI Specialist",
            "description": "Learn to build practical AI applications using LLMs, prompt engineering, vector databases, RAG architectures, and autonomous agent loops.",
            "modules_count": 6,
            "popular_pair": "Data Structures & Algorithms",
            "icon": "bot"
        },
        {
            "id": "dsa",
            "title": "Data Structures & Algorithms",
            "category": "Computer Science",
            "badge": "DSA",
            "target_role": "Software Engineer (Algorithms & Problem Solving)",
            "description": "Master algorithmic complexity, dynamic arrays, two pointers, trees, graphs, dynamic programming, and high-yield interview patterns.",
            "modules_count": 7,
            "popular_pair": "AI Engineer",
            "icon": "binary"
        },
        {
            "id": "backend",
            "title": "Backend Developer",
            "category": "Web Development",
            "badge": "Backend",
            "target_role": "Core Backend Software Engineer",
            "description": "Deep-dive into language internals, relational databases (PostgreSQL), API design (REST & gRPC), caching (Redis), message queues (Kafka), and system design.",
            "modules_count": 6,
            "popular_pair": "DevOps & Cloud",
            "icon": "server"
        },
        {
            "id": "frontend",
            "title": "Frontend Developer",
            "category": "Web Development",
            "badge": "Frontend",
            "target_role": "Modern Frontend Software Engineer",
            "description": "Master modern HTML/CSS, TypeScript, React ecosystem, state architecture, Web Vitals performance, and production build tooling.",
            "modules_count": 6,
            "popular_pair": "Backend Developer",
            "icon": "layout"
        },
        {
            "id": "devops",
            "title": "DevOps & Cloud",
            "category": "Cloud & Infrastructure",
            "badge": "DevOps",
            "target_role": "DevOps / Site Reliability Engineer (SRE)",
            "description": "Master Linux systems, containerization with Docker, Kubernetes orchestration, CI/CD automation, Terraform IaC, and Prometheus/Grafana observability.",
            "modules_count": 5,
            "popular_pair": "Backend Developer",
            "icon": "cloud"
        },
        {
            "id": "full-stack",
            "title": "Full Stack Developer",
            "category": "Full Stack",
            "badge": "Full Stack",
            "target_role": "Full Stack Software Engineer",
            "description": "End-to-end modern stack from interactive UI design, type-safe API gateways, relational persistence, containerized deployments to production.",
            "modules_count": 6,
            "popular_pair": "AI Engineer",
            "icon": "layers"
        },
        {
            "id": "python",
            "title": "Python Developer",
            "category": "Programming Languages",
            "badge": "Python",
            "target_role": "Python Software Engineer",
            "description": "Comprehensive journey across Python 3.12+ runtime, OOP & typing, asynchronous asyncio, FastAPI microservices, and packaging ecosystems.",
            "modules_count": 5,
            "popular_pair": "AI Engineer",
            "icon": "code"
        },
        {
            "id": "cyber-security",
            "title": "Cyber Security",
            "category": "Security",
            "badge": "Security",
            "target_role": "Security Engineer / Ethical Hacker",
            "description": "Network forensics, cryptography primitives, OWASP Top 10 web vulnerabilities, penetration testing tools, and DevSecOps pipelines.",
            "modules_count": 5,
            "popular_pair": "DevOps & Cloud",
            "icon": "shield"
        }
    ]

async def generate_personalized_roadmap(db: Session, user_id: int, goal_title: str, target_role: str = "") -> Dict[str, Any]:
    """
    Builds a grounded, high-value career or technical roadmap using the structured logic
    of roadmap.sh (sequential modules, granular subtopics, importance levels, YouTube playlists, and clickable references).
    Tailored to user's saved courses, missing skills, and active resume.
    """
    user_skill_names = _extract_user_skills(db, user_id)

    # Get user's saved courses and opportunities
    saved_courses = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.type.in_(["course", "certification"]),
        Resource.is_archived == False
    ).all()

    goal_lower = goal_title.lower().strip()

    # -------------------------------------------------------------
    # 0. HYBRID MULTI-TRACK ROADMAP (Combine 2-3 Goals Together)
    # -------------------------------------------------------------
    sub_goals = []
    if "+" in goal_title:
        sub_goals = [s.strip() for s in goal_title.split("+") if s.strip()]
    elif "," in goal_title:
        sub_goals = [s.strip() for s in goal_title.split(",") if s.strip()]

    if len(sub_goals) >= 2:
        def _clean_track_name(g: str) -> str:
            clean = re.sub(r'(?i)^(hybrid\s+)?multi[- ]track:\s*', '', g)
            clean = re.sub(r'\(.*?\)', '', clean)
            return clean.strip().title()

        clean_track_names = [_clean_track_name(g) for g in sub_goals]
        resolved_title = f"Hybrid Multi-Track: {' + '.join(clean_track_names)}"
        resolved_role = target_role or f"Specialist ({' / '.join(clean_track_names[:2])})"
        track_str = ", ".join(clean_track_names)

        t1 = clean_track_names[0]
        t2 = clean_track_names[1]
        t3 = clean_track_names[2] if len(clean_track_names) > 2 else None

        youtube_playlists = [
            {
                "title": f"Complete {t1} Accelerated Bootcamp",
                "channel": "freeCodeCamp.org",
                "url": "https://www.youtube.com/@freecodecamp",
                "badge": "Free Course",
                "videos_count": "Full Course"
            },
            {
                "title": f"{t2} Practical Deep Dive",
                "channel": "Andrej Karpathy & DeepLearning.AI",
                "url": "https://www.youtube.com/@Deeplearningai",
                "badge": "Featured Series",
                "videos_count": "12 Videos"
            },
            {
                "title": "NeetCode & System Design Mastery",
                "channel": "NeetCode",
                "url": "https://www.youtube.com/@NeetCode",
                "badge": "Top Rated",
                "videos_count": "150 Videos"
            }
        ]

        related_roadmaps = [
            "Data Structures & Algorithms",
            "AI Engineer (roadmap.sh/ai)",
            "Backend Developer",
            "DevOps & Cloud",
            "System Design"
        ]

        modules = [
            {
                "order": 1,
                "title": f"1. Foundations: {t1} & {t2} Core Primitives",
                "description": f"Master the computational complexity, syntax fundamentals, and runtime architectures of both {t1} and {t2}.",
                "is_multitrack": True,
                "tracks": [t1, t2] + ([t3] if t3 else []),
                "topics": [
                    {
                        "name": f"[{t1}] Big-O Time & Space Complexity Analysis",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Analyze asymptotic upper and lower bounds, memory stack allocation, and runtime trade-offs.",
                        "references": [
                            {"title": "Big-O Cheat Sheet", "url": "https://www.bigocheatsheet.com/", "type": "tool"},
                            {"title": "MIT 6.006 Complexity Foundations", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "type": "course"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Foundation Model Architectures & API Inference",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Differentiate foundation model families, understand pricing economics, and establish secure client connections.",
                        "references": [
                            {"title": "Anthropic API Architecture Overview", "url": "https://docs.anthropic.com/", "type": "doc"},
                            {"title": "OpenAI API Reference", "url": "https://platform.openai.com/docs/api-reference", "type": "doc"}
                        ]
                    },
                    {
                        "name": f"[{t1}] Memory Layout, Pointers & Array Primitives",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Contiguous memory allocations, dynamic sizing amortized cost, and indexing fundamentals.",
                        "references": [
                            {"title": "NeetCode Dynamic Array Breakdown", "url": "https://neetcode.io/roadmap", "type": "practice"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Tokenization, Context Windows & Parameter Tuning",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Token counters, context limits, temperature, top-p sampling, and stop sequences.",
                        "references": [
                            {"title": "OpenAI Interactive Tokenizer", "url": "https://platform.openai.com/tokenizer", "type": "tool"}
                        ]
                    },
                    {
                        "name": f"[{t1}] Recursion Trees & Recurrence Relations",
                        "importance": "Recommended",
                        "completed": False,
                        "track": t1,
                        "description": "Call stack frames, base cases, and divide-and-conquer recurrence formulas.",
                        "references": [
                            {"title": "Recursion Trees & Master Theorem", "url": "https://en.wikipedia.org/wiki/Master_theorem_(analysis_of_algorithms)", "type": "article"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Closed vs Open-Source Models (GPT-4o, Claude, Llama 3)",
                        "importance": "Recommended",
                        "completed": False,
                        "track": t2,
                        "description": "Evaluating proprietary cloud endpoints vs self-hosted quantized models via Ollama/vLLM.",
                        "references": [
                            {"title": "Hugging Face Open LLM Leaderboard", "url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard", "type": "tool"}
                        ]
                    }
                ],
                "resources": [
                    {"title": f"roadmap.sh {t1} Guide", "url": "https://roadmap.sh", "type": "guide"},
                    {"title": f"roadmap.sh {t2} Guide", "url": "https://roadmap.sh", "type": "guide"}
                ]
            },
            {
                "order": 2,
                "title": "2. Parallel Core Competencies & Daily Drills",
                "description": f"Progress through fundamental structures of {t1} while building core modules in {t2}.",
                "is_multitrack": True,
                "tracks": [t1, t2] + ([t3] if t3 else []),
                "topics": [
                    {
                        "name": f"[{t1}] Linear Data Structures, Stacks & Complexity Limits",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Arrays, dynamic lists, linked chains, and monotonic stacks.",
                        "references": [
                            {"title": "NeetCode Linear DSA Sheet", "url": "https://neetcode.io/roadmap", "type": "practice"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Data Modeling, API Endpoints & Foundation Schemas",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Input validation schemas, database models, and RESTful routing.",
                        "references": [
                            {"title": "FastAPI & Pydantic Schema Guide", "url": "https://fastapi.tiangolo.com/tutorial/schema-extra-example/", "type": "doc"}
                        ]
                    },
                    {
                        "name": f"[{t1}] Two-Pointer & Binary Search Optimization Techniques",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Opposite-end navigation, sliding windows, and binary search on predicate functions.",
                        "references": [
                            {"title": "LeetCode Binary Search Study Plan", "url": "https://leetcode.com/studyplan/binary-search/", "type": "practice"}
                        ]
                    },
                    {
                        "name": f"[{t2}] State Management, Vector Stores, or Containerization",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Embeddings, vector indexing, and isolated container runs.",
                        "references": [
                            {"title": "Pinecone / ChromaDB Vector Indexing", "url": "https://docs.trychroma.com/", "type": "doc"}
                        ]
                    }
                ],
                "resources": []
            },
            {
                "order": 3,
                "title": "3. Intermediate Deep-Dives & System Scalability",
                "description": f"Scale complexity across both careers with non-linear patterns, caching tiers, and pipeline automation.",
                "is_multitrack": True,
                "tracks": [t1, t2] + ([t3] if t3 else []),
                "topics": [
                    {
                        "name": f"[{t1}] Hierarchical Trees, Heaps & Prefix Search Structures",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "BSTs, heap priority queues, and trie autocomplete dictionaries.",
                        "references": [
                            {"title": "VisuAlgo BST and Heap Interactive Visualizer", "url": "https://visualgo.net/en/bst", "type": "visualization"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Caching Tiers (Redis), RAG Pipelines, or Cloud Services",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Distributed cache-aside caching, chunking strategies, and hybrid vector search.",
                        "references": [
                            {"title": "Redis In-Memory Architecture", "url": "https://redis.io/docs/about/", "type": "doc"}
                        ]
                    },
                    {
                        "name": f"[{t1}] Sliding Window & Monotonic Stack Problem Sets",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Optimal sub-array windows and stock span monotonic stack patterns.",
                        "references": [
                            {"title": "Blind 75 LeetCode Collection", "url": "https://leetcode.com/discuss/general-discussion/460599/blind-75-leetcode-questions", "type": "practice"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Asynchronous Workers, Message Queues & Fault Tolerance",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Background worker queues, retry backoff, and async event processing.",
                        "references": [
                            {"title": "RabbitMQ / Celery Distributed Task Queue", "url": "https://docs.celeryq.dev/en/stable/", "type": "doc"}
                        ]
                    }
                ],
                "resources": []
            },
            {
                "order": 4,
                "title": "4. Advanced Graph Algorithms & Scalable Distributed Systems",
                "description": f"Synthesize graph traversal networks ({t1}) with microservice architectures or autonomous AI agents ({t2}).",
                "is_multitrack": True,
                "tracks": [t1, t2] + ([t3] if t3 else []),
                "topics": [
                    {
                        "name": f"[{t1}] Graph Connectivity: BFS, DFS, Topological Sort & Dijkstra",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Shortest path finding, dependency topological resolution, and cycle detection.",
                        "references": [
                            {"title": "Algorithms Part II (Princeton / Coursera)", "url": "https://www.coursera.org/learn/algorithms-part2", "type": "course"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Autonomous Agent Decision Loops & Tool Calling Schemas",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Construct ReAct loops, JSON tool calling, and long-term memory state.",
                        "references": [
                            {"title": "Anthropic Tool Use Curriculum", "url": "https://github.com/anthropics/courses/blob/master/tool_use/README.md", "type": "course"}
                        ]
                    },
                    {
                        "name": f"[{t1}] Dynamic Programming: 1D Knapsack & 2D Grid Memoization",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Overlapping subproblem memoization and bottom-up tabulation.",
                        "references": [
                            {"title": "LeetCode Dynamic Programming Patterns", "url": "https://leetcode.com/discuss/general-discussion/458695/Dynamic-Programming-Patterns", "type": "guide"}
                        ]
                    },
                    {
                        "name": f"[{t2}] Observability, Telemetry & Distributed Tracing",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Latency profiling, structured logging, and tracing instrumentation.",
                        "references": [
                            {"title": "OpenTelemetry Documentation", "url": "https://opentelemetry.io/docs/", "type": "doc"}
                        ]
                    }
                ],
                "resources": []
            },
            {
                "order": 5,
                "title": f"5. The Convergence Bridge: Unified Dual-Career Capstone ({t1} + {t2})",
                "description": f"Architect a single high-impact capstone project that leverages both {t1} and {t2} concurrently to stand out in recruitment.",
                "is_multitrack": True,
                "tracks": [t1, t2] + ([t3] if t3 else []),
                "topics": [
                    {
                        "name": f"Bridge Project: Intelligent Real-Time Platform merging {t1} & {t2}",
                        "importance": "Must Know",
                        "completed": False,
                        "track": "Capstone",
                        "description": f"Build a system demonstrating core competencies of {t1} and {t2} in an integrated production application.",
                        "references": [
                            {"title": "Building Production Web Apps Guide", "url": "https://roadmap.sh", "type": "guide"}
                        ]
                    },
                    {
                        "name": "Live Cloud Deployment with Docker, CI/CD & Automated Testing",
                        "importance": "Must Know",
                        "completed": False,
                        "track": "Engineering",
                        "description": "Deploy to public URL with GitHub Actions CI, unit tests, and health checks.",
                        "references": [
                            {"title": "GitHub Actions Documentation", "url": "https://docs.github.com/en/actions", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Interactive Demo Video, Benchmark Metrics & Technical Writeup",
                        "importance": "Must Know",
                        "completed": False,
                        "track": "Portfolio",
                        "description": "Record a 2-minute Loom walkthrough and write a markdown case study.",
                        "references": [
                            {"title": "How to Write a Great Engineering README", "url": "https://github.com/matiassingers/awesome-readme", "type": "guide"}
                        ]
                    }
                ],
                "resources": []
            },
            {
                "order": 6,
                "title": f"6. Dual-Career Technical Screenings & Strategic Applications",
                "description": f"Conduct timed coding drills and system design defenses tailored specifically for roles demanding {t1} and {t2}.",
                "is_multitrack": True,
                "tracks": [t1, t2] + ([t3] if t3 else []),
                "topics": [
                    {
                        "name": f"[{t1}] Timed 45-Minute Algorithmic Mock Coding Screenings",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t1,
                        "description": "Simulate real whiteboard rounds explaining Big-O tradeoffs aloud.",
                        "references": [
                            {"title": "Pramp Free Peer Mock Interviews", "url": "https://www.pramp.com/", "type": "practice"}
                        ]
                    },
                    {
                        "name": f"[{t2}] System Architecture & Production Tradeoffs Defense",
                        "importance": "Must Know",
                        "completed": False,
                        "track": t2,
                        "description": "Defend caching, database scaling, and latency bottlenecks under questioning.",
                        "references": [
                            {"title": "System Design Primer by Donne Martin", "url": "https://github.com/donnemartin/system-design-primer", "type": "guide"}
                        ]
                    },
                    {
                        "name": "Tailored Resume Highlighting Both Specializations",
                        "importance": "Must Know",
                        "completed": False,
                        "track": "Career",
                        "description": "Feature the bridge capstone prominently to showcase rare dual proficiency.",
                        "references": [
                            {"title": "Tech Interview Handbook Resume Guide", "url": "https://www.techinterviewhandbook.org/resume/", "type": "guide"}
                        ]
                    }
                ],
                "resources": []
            }
        ]

        steps = []
        for m in modules:
            step_id = str(uuid.uuid4())[:8]
            steps.append({
                "id": step_id,
                "title": m["title"],
                "description": m["description"],
                "is_multitrack": True,
                "tracks": m["tracks"],
                "topics": m["topics"],
                "resources": m.get("resources", []),
                "resource_ids": [r["resource_id"] for r in m.get("resources", []) if "resource_id" in r],
                "skill_ids": [],
                "order": m["order"],
                "completed": False
            })

        return {
            "goal_title": resolved_title,
            "target_role": resolved_role,
            "description": f"Balanced multi-track execution path designed to pursue {len(clean_track_names)} goals simultaneously ({track_str}). Modeled after roadmap.sh with daily time-splits, interleaved milestones, and a unified bridge capstone.",
            "youtube_playlists": youtube_playlists,
            "related_roadmaps": related_roadmaps,
            "steps": steps
        }

    # -------------------------------------------------------------
    # 1. AI ENGINEER ROADMAP (https://roadmap.sh/ai)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["ai", "artificial intelligence", "llm", "machine learning", "genai", "agent", "deep learning"]):
        resolved_title = "AI Engineer Roadmap"
        resolved_role = target_role or "AI Engineer / Generative AI Specialist"

        youtube_playlists = [
            {
                "title": "Neural Networks: Zero to Hero",
                "channel": "Andrej Karpathy",
                "url": "https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ",
                "badge": "Top Rated Series",
                "videos_count": "8 Deep Dives"
            },
            {
                "title": "Generative AI with Large Language Models",
                "channel": "DeepLearning.AI / Andrew Ng",
                "url": "https://www.youtube.com/@Deeplearningai",
                "badge": "Industry Standard",
                "videos_count": "Full Series"
            },
            {
                "title": "Machine Learning & Neural Networks Fundamentals",
                "channel": "StatQuest with Josh Starmer",
                "url": "https://www.youtube.com/playlist?list=PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF",
                "badge": "Intuitive Visuals",
                "videos_count": "45 Videos"
            },
            {
                "title": "Full AI Engineer Course: From Zero to Production",
                "channel": "freeCodeCamp.org",
                "url": "https://www.youtube.com/watch?v=5NgNicANyqM",
                "badge": "Free Course",
                "videos_count": "12 Hours"
            }
        ]

        related_roadmaps = [
            "Prompt Engineering",
            "MLOps",
            "Data Structures & Algorithms",
            "Python Developer",
            "Backend Developer"
        ]

        modules = [
            {
                "order": 1,
                "title": "1. AI Engineering Fundamentals & Pre-trained Models",
                "description": "Differentiate AI Engineering from ML Research. Master tokenization, context windows, parameters (temperature, top-p, top-k), and pricing models.",
                "topics": [
                    {
                        "name": "AI Engineer vs ML Researcher Roles",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Understand why AI engineering focuses on orchestrating and operationalizing pre-trained foundation models rather than training models from scratch.",
                        "references": [
                            {"title": "The Rise of the AI Engineer (Swyx)", "url": "https://www.latent.space/p/ai-engineer", "type": "article"},
                            {"title": "roadmap.sh AI Engineer Guide", "url": "https://roadmap.sh/ai", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Token Management & Context Windows",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "How BPE tokenizers work, calculating token-to-word ratios, context window limits, and cost management.",
                        "references": [
                            {"title": "OpenAI Interactive Tokenizer", "url": "https://platform.openai.com/tokenizer", "type": "tool"},
                            {"title": "Tiktoken Tokenizer GitHub", "url": "https://github.com/openai/tiktoken", "type": "github"}
                        ]
                    },
                    {
                        "name": "Model Parameters: Temperature, Top-P, Top-K",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Controlling randomness and probability distributions during model inference for deterministic vs creative outputs.",
                        "references": [
                            {"title": "Anthropic Model Parameters & Temperature Guide", "url": "https://docs.anthropic.com/en/docs/resources/prompt-engineering/prompt-parameters", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Closed vs Open Source Models (GPT-4o, Claude 3.5, Llama 3)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Evaluating proprietary API providers against open weights hosted locally or in private VPCs.",
                        "references": [
                            {"title": "LMSYS Chatbot Arena Leaderboard", "url": "https://chat.lmsys.org/", "type": "tool"},
                            {"title": "Hugging Face Open LLM Leaderboard", "url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard", "type": "tool"}
                        ]
                    },
                    {
                        "name": "Local Model Execution (Ollama, vLLM, LM Studio)",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Run quantized models locally with Ollama or host high-throughput inference endpoints with vLLM PagedAttention.",
                        "references": [
                            {"title": "Ollama Official Get Started", "url": "https://ollama.com/", "type": "doc"},
                            {"title": "vLLM High-Throughput Serving Engine", "url": "https://docs.vllm.ai/", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "roadmap.sh AI Engineer Guide", "url": "https://roadmap.sh/ai", "type": "guide"},
                    {"title": "Anthropic API Fundamentals", "url": "https://github.com/anthropics/courses/blob/master/anthropic_api_fundamentals/README.md", "type": "course"}
                ]
            },
            {
                "order": 2,
                "title": "2. Prompt Engineering & In-Context Learning",
                "description": "Move beyond casual chat to structured production prompts. Implement few-shot examples, reasoning chains, and schema-enforced structured outputs.",
                "topics": [
                    {
                        "name": "Zero-Shot & Few-Shot Prompting",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Formulating precise system instructions with exemplar pairs to dramatically reduce variance and edge case errors.",
                        "references": [
                            {"title": "Anthropic Interactive Prompt Tutorial", "url": "https://github.com/anthropics/courses/blob/master/prompt_engineering_interactive_tutorial/README.md", "type": "course"},
                            {"title": "Prompt Engineering Guide by DAIR.AI", "url": "https://www.promptingguide.ai/", "type": "guide"}
                        ]
                    },
                    {
                        "name": "Chain-of-Thought (CoT) & Reasoning Chains",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Triggering step-by-step thinking scratchpads to boost accuracy on multi-step logic and mathematical reasoning.",
                        "references": [
                            {"title": "Chain-of-Thought Prompting Paper (Wei et al.)", "url": "https://arxiv.org/abs/2201.11903", "type": "article"}
                        ]
                    },
                    {
                        "name": "Strict JSON Output & Schema Enforcement",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Extracting guaranteed type-safe JSON objects via instructor or structured output schemas.",
                        "references": [
                            {"title": "OpenAI Structured Outputs Guide", "url": "https://platform.openai.com/docs/guides/structured-outputs", "type": "doc"},
                            {"title": "Instructor Python Library (Pydantic for LLMs)", "url": "https://python.useinstructor.com/", "type": "github"}
                        ]
                    },
                    {
                        "name": "System Prompts & Formatting Delimiters",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Using XML tags like <context>, <rules>, <output_format> to cleanly delineate prompt components.",
                        "references": [
                            {"title": "Anthropic Guide on Using XML Tags", "url": "https://docs.anthropic.com/en/docs/resources/prompt-engineering/use-xml-tags", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Prompt Injection Defenses & Delimiter Escaping",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Preventing user input from overriding system instructions through robust escaping and input sanitization.",
                        "references": [
                            {"title": "OWASP Top 10 for LLMs: Prompt Injection", "url": "https://genai.owasp.org/llm-top-10/", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Anthropic Prompt Engineering Tutorial", "url": "https://github.com/anthropics/courses/blob/master/prompt_engineering_interactive_tutorial/README.md", "type": "course"}
                ]
            },
            {
                "order": 3,
                "title": "3. Embeddings & Vector Databases",
                "description": "Understand dense vector representations for semantic search. Select and benchmark vector databases, distance metrics, and indexing algorithms.",
                "topics": [
                    {
                        "name": "Dense Vector Representations & Cosine Similarity",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "How neural networks project semantic meaning into high-dimensional geometric spaces and calculate dot product / cosine similarity.",
                        "references": [
                            {"title": "Visual Introduction to Embeddings (Cohere)", "url": "https://cohere.com/blog/embeddings-visualized", "type": "article"},
                            {"title": "3Blue1Brown: What Are Embeddings?", "url": "https://www.youtube.com/watch?v=wjZofJX0v4U", "type": "video"}
                        ]
                    },
                    {
                        "name": "Embedding Models (text-embedding-3, Voyage, BGE)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Choosing between hosted embeddings and local open-source sentence-transformers.",
                        "references": [
                            {"title": "MTEB Massive Text Embedding Benchmark", "url": "https://huggingface.co/spaces/mteb/leaderboard", "type": "tool"}
                        ]
                    },
                    {
                        "name": "Vector DBs: ChromaDB, Pinecone, Qdrant, pgvector",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Evaluating managed cloud vector stores vs embedded databases vs PostgreSQL pgvector extension.",
                        "references": [
                            {"title": "ChromaDB Quickstart Guide", "url": "https://docs.trychroma.com/getting-started", "type": "doc"},
                            {"title": "Pinecone Vector Architecture Guide", "url": "https://docs.pinecone.io/guides/get-started/overview", "type": "doc"},
                            {"title": "pgvector GitHub Repository", "url": "https://github.com/pgvector/pgvector", "type": "github"}
                        ]
                    },
                    {
                        "name": "Vector Indexing Algorithms (HNSW, IVFFlat, PQ)",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Hierarchical Navigable Small World graphs for sub-millisecond approximate nearest neighbor retrieval.",
                        "references": [
                            {"title": "Pinecone HNSW Explained Visually", "url": "https://www.pinecone.io/learn/series/faiss/hnsw/", "type": "article"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "ChromaDB Official Documentation", "url": "https://docs.trychroma.com/", "type": "docs"},
                    {"title": "Pinecone Vector Search Architecture", "url": "https://docs.pinecone.io/", "type": "docs"}
                ]
            },
            {
                "order": 4,
                "title": "4. Retrieval-Augmented Generation (RAG)",
                "description": "Build end-to-end RAG pipelines connecting proprietary knowledge to LLMs with minimal hallucination and maximum provenance.",
                "topics": [
                    {
                        "name": "Document Chunking Strategies (Recursive, Semantic, Window)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Splitting documents into optimal context chunks balancing semantic continuity with context window economics.",
                        "references": [
                            {"title": "Pinecone Chunking Strategies Guide", "url": "https://www.pinecone.io/learn/chunking-strategies/", "type": "article"},
                            {"title": "LlamaIndex Advanced Chunking", "url": "https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Semantic Retrieval & Top-K Sampling",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Querying vector indices to fetch top-k relevant fragments and interpolating them into prompt templates.",
                        "references": [
                            {"title": "LangChain Retrieval Documentation", "url": "https://python.langchain.com/docs/modules/data_connection/retrievers/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Hybrid Search (Dense Semantic + Sparse BM25 Keyword)",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Combining keyword frequency (BM25) with vector embeddings via Reciprocal Rank Fusion (RRF) for precise acronym matching.",
                        "references": [
                            {"title": "Qdrant Hybrid Search Tutorial", "url": "https://qdrant.tech/articles/hybrid-search/", "type": "article"}
                        ]
                    },
                    {
                        "name": "Reranking Pipelines (Cohere Rerank, BGE Reranker)",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Passing retrieved candidates through a cross-encoder to produce calibrated relevance scores.",
                        "references": [
                            {"title": "Cohere Rerank API Documentation", "url": "https://docs.cohere.com/docs/rerank-overview", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Source Attribution & Citation Provenance",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Returning verifiable document metadata, page numbers, and quote spans to users for auditability.",
                        "references": [
                            {"title": "RAG Provenance & Hallucination Mitigation (LlamaIndex)", "url": "https://docs.llamaindex.ai/", "type": "guide"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "LangChain / LlamaIndex RAG Playbook", "url": "https://docs.llamaindex.ai/", "type": "guide"}
                ]
            },
            {
                "order": 5,
                "title": "5. Autonomous AI Agents & Tool Calling",
                "description": "Construct reasoning engines that can dynamically select tools, invoke external APIs, execute multi-step workflows, and persist state.",
                "topics": [
                    {
                        "name": "Function Calling & Tool Definition Schemas",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Declaring JSON schemas for external functions and parsing model tool call arguments with type validation.",
                        "references": [
                            {"title": "Anthropic Tool Use Curriculum", "url": "https://github.com/anthropics/courses/blob/master/tool_use/README.md", "type": "course"},
                            {"title": "OpenAI Function Calling Guide", "url": "https://platform.openai.com/docs/guides/function-calling", "type": "doc"}
                        ]
                    },
                    {
                        "name": "ReAct (Reasoning + Acting) Decision Loops",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Implementing iterative Think -> Act -> Observe loops allowing agents to reflect on previous tool results.",
                        "references": [
                            {"title": "ReAct: Synergizing Reasoning and Acting in Language Models", "url": "https://arxiv.org/abs/2210.03629", "type": "article"}
                        ]
                    },
                    {
                        "name": "Short-Term Buffer vs Long-Term Vector Memory",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Managing conversation buffers, session summaries, and persistent associative memory stores across sessions.",
                        "references": [
                            {"title": "MemGPT / Letta Agent Memory Architecture", "url": "https://docs.letta.com/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Multi-Agent Orchestration (LangGraph, CrewAI)",
                        "importance": "Advanced",
                        "completed": False,
                        "description": "Modeling complex team workflows as cyclic graphs with specialized routing agents.",
                        "references": [
                            {"title": "LangGraph Interactive Tutorials", "url": "https://langchain-ai.github.io/langgraph/", "type": "doc"},
                            {"title": "CrewAI Multi-Agent Framework", "url": "https://docs.crewai.com/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Error Recovery & Self-Correction Loops",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Catching API exceptions and formatting errors, sending feedback to LLM to self-heal and retry.",
                        "references": [
                            {"title": "Reflexion: Language Agents with Verbal Reinforcement Learning", "url": "https://arxiv.org/abs/2303.11366", "type": "article"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Anthropic Tool Use Curriculum", "url": "https://github.com/anthropics/courses/blob/master/tool_use/README.md", "type": "course"}
                ]
            },
            {
                "order": 6,
                "title": "6. Evaluation, Security & Production Serving",
                "description": "Prevent regressions, defend against adversarial jailbreaks, evaluate accuracy, and trace production LLM calls.",
                "topics": [
                    {
                        "name": "Automated LLM-as-a-Judge Evaluation Suites",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Benchmarking pipeline revisions with automated judge models evaluating factual consistency and answer relevance.",
                        "references": [
                            {"title": "Ragas: Evaluation Framework for RAG", "url": "https://docs.ragas.io/", "type": "doc"},
                            {"title": "Anthropic Prompt Evaluations Guide", "url": "https://github.com/anthropics/courses/blob/master/prompt_evaluations/README.md", "type": "course"}
                        ]
                    },
                    {
                        "name": "Prompt Injection Defenses & Input Sanitization",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Detecting indirect prompt injections from web pages or untrusted user files using safety classifiers.",
                        "references": [
                            {"title": "Llama Guard Safety Classifier (Meta)", "url": "https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/", "type": "article"}
                        ]
                    },
                    {
                        "name": "Output Guardrails & PII Redaction",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Enforcing schema boundaries and masking sensitive API tokens, SSNs, and personal data before responding.",
                        "references": [
                            {"title": "NeMo Guardrails (NVIDIA)", "url": "https://docs.nvidia.com/nemo/guardrails/", "type": "doc"},
                            {"title": "Guardrails AI Hub", "url": "https://hub.guardrailsai.com/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "LLM Observability & Tracing (LangSmith, Langfuse)",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Tracing execution trees, recording token expenditures, latency distributions, and capturing user feedback.",
                        "references": [
                            {"title": "Langfuse Open Source LLM Engineering Platform", "url": "https://langfuse.com/docs", "type": "doc"},
                            {"title": "LangSmith Observability Documentation", "url": "https://docs.smith.langchain.com/", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Anthropic Prompt Evaluations Guide", "url": "https://github.com/anthropics/courses/blob/master/prompt_evaluations/README.md", "type": "course"}
                ]
            }
        ]

        steps = []
        for m in modules:
            step_id = str(uuid.uuid4())[:8]
            res_ids = [r["resource_id"] for r in m.get("resources", []) if "resource_id" in r]
            steps.append({
                "id": step_id,
                "title": m["title"],
                "description": m["description"],
                "topics": m["topics"],
                "resources": m.get("resources", []),
                "resource_ids": res_ids,
                "skill_ids": [],
                "order": m["order"],
                "completed": False
            })

        return {
            "goal_title": resolved_title,
            "target_role": resolved_role,
            "description": "Comprehensive roadmap modeled after roadmap.sh/ai covering pre-trained models, prompt engineering, vector databases, RAG architecture, agentic tool workflows, and safety guardrails.",
            "youtube_playlists": youtube_playlists,
            "related_roadmaps": related_roadmaps,
            "steps": steps
        }

    # -------------------------------------------------------------
    # 2. DATA STRUCTURES & ALGORITHMS (roadmap.sh/datastructures-and-algorithms)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["algo", "dsa", "data structure", "leetcode", "problem solving", "competitive programming"]):
        resolved_title = "Data Structures & Algorithms (roadmap.sh/dsa)"
        resolved_role = target_role or "Software Engineer (Algorithms & Problem Solving)"

        youtube_playlists = [
            {
                "title": "A2Z DSA Course & Sheet (Complete Roadmap)",
                "channel": "Striver / take U forward",
                "url": "https://www.youtube.com/playlist?list=PLgUwDviBIf0oF6QL8m22w1hIDC1vJ_st8",
                "badge": "Complete Roadmap",
                "videos_count": "180 Videos"
            },
            {
                "title": "Algorithms & Data Structures for Beginners",
                "channel": "NeetCode",
                "url": "https://www.youtube.com/playlist?list=PLot-Xpze53lf5C3HSjCnyFghlW0G1QKXo",
                "badge": "Top Rated",
                "videos_count": "150 Videos"
            },
            {
                "title": "Algorithms Mastery Series",
                "channel": "Abdul Bari",
                "url": "https://www.youtube.com/playlist?list=PLDN4rrl48XKpZkf03iYFl-O29szjTrs_O",
                "badge": "Foundational Masterclass",
                "videos_count": "84 Videos"
            }
        ]

        related_roadmaps = [
            "Competitive Programming",
            "Backend Developer",
            "AI Engineer (roadmap.sh/ai)",
            "System Design"
        ]

        modules = [
            {
                "order": 1,
                "title": "1. Algorithmic Complexity & Foundations",
                "description": "Master asymptotic notation, recursive recurrence relations, space/time complexity tradeoffs, and bit manipulation primitives.",
                "topics": [
                    {
                        "name": "Big-O, Big-Omega, Big-Theta Analysis",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Formal definitions of asymptotic upper, lower, and tight bounds for algorithmic growth.",
                        "references": [
                            {"title": "MIT 6.006 Big-O Lecture Notes", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "type": "course"},
                            {"title": "Big-O Cheat Sheet", "url": "https://www.bigocheatsheet.com/", "type": "tool"}
                        ]
                    },
                    {
                        "name": "Recursion Trees & Master Theorem",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Solving divide-and-conquer recurrence relations like T(n) = 2T(n/2) + O(n).",
                        "references": [
                            {"title": "Master Theorem Formula & Proofs", "url": "https://en.wikipedia.org/wiki/Master_theorem_(analysis_of_algorithms)", "type": "article"}
                        ]
                    },
                    {
                        "name": "Space & Time Tradeoffs & In-Place Algorithms",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Auxiliary space complexity, stack frames, and mutating input arrays in O(1) space.",
                        "references": [
                            {"title": "In-Place Algorithms Explained", "url": "https://neetcode.io/roadmap", "type": "practice"}
                        ]
                    },
                    {
                        "name": "Bitwise Operations & Masks",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "XOR tricks, checking powers of two, bit shifts, and representing subsets as integers.",
                        "references": [
                            {"title": "Bit Manipulation Hacks (Stanford)", "url": "https://graphics.stanford.edu/~seander/bithacks.html", "type": "guide"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "MIT 6.006 Introduction to Algorithms", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "type": "course"}
                ]
            },
            {
                "order": 2,
                "title": "2. Linear Data Structures & Two Pointers",
                "description": "Implement arrays, linked lists, stacks, and queues from scratch. Master two-pointer navigation patterns.",
                "topics": [
                    {
                        "name": "Dynamic Arrays & Amortized Insertion",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "How contiguous memory geometric doubling provides O(1) amortized append time.",
                        "references": [
                            {"title": "NeetCode Dynamic Array Walkthrough", "url": "https://neetcode.io/roadmap", "type": "practice"}
                        ]
                    },
                    {
                        "name": "Singly & Doubly Linked Lists",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Pointer reversal, sentinel dummy heads, and fast/slow cycle detection (Floyd's algorithm).",
                        "references": [
                            {"title": "LeetCode Linked List Study Guide", "url": "https://leetcode.com/explore/learn/card/linked-list/", "type": "practice"}
                        ]
                    },
                    {
                        "name": "Stacks & Monotonic Stack Pattern",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Next greater element and histogram area optimization using monotonic stacks.",
                        "references": [
                            {"title": "Monotonic Stack Pattern Guide", "url": "https://leetcode.com/discuss/general-discussion/1154563/monotonic-stack-summary-list-of-problems", "type": "article"}
                        ]
                    },
                    {
                        "name": "Two-Pointer (Opposite Ends & Fast/Slow)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Sorted pair sum finding, palindrome verification, and partition schemes.",
                        "references": [
                            {"title": "LeetCode Two Pointer Explorations", "url": "https://leetcode.com/explore/featured/card/array-and-string/", "type": "practice"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "NeetCode Linear Data Structures", "url": "https://neetcode.io/roadmap", "type": "practice"}
                ]
            },
            {
                "order": 3,
                "title": "3. Binary Search & Sliding Window",
                "description": "Execute binary search on sorted sequences and abstract answer spaces. Solve contiguous subarray optimization problems.",
                "topics": [
                    {
                        "name": "Binary Search on Arrays & Boundary Finding",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Lower bound, upper bound, and rotated sorted array searches with zero index overflow.",
                        "references": [
                            {"title": "LeetCode Binary Search Study Plan", "url": "https://leetcode.com/studyplan/binary-search/", "type": "practice"}
                        ]
                    },
                    {
                        "name": "Binary Search on Answer Space",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Searching monotonic predicate functions for minimum capacity or maximum time.",
                        "references": [
                            {"title": "Binary Search on Answer Pattern", "url": "https://leetcode.com/discuss/general-discussion/786126/python-powerful-ultimate-binary-search-template", "type": "article"}
                        ]
                    },
                    {
                        "name": "Fixed & Variable Size Sliding Window",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Contiguous subarray tracking with frequency hash maps in O(N) runtime.",
                        "references": [
                            {"title": "Sliding Window Algorithm Cheat Sheet", "url": "https://leetcode.com/discuss/general-discussion/657507/sliding-window-for-beginners-problems-template-sample-solutions", "type": "guide"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "LeetCode Binary Search Study Plan", "url": "https://leetcode.com/studyplan/binary-search/", "type": "practice"}
                ]
            },
            {
                "order": 4,
                "title": "4. Trees, Heaps & Prefix Structures",
                "description": "Navigate hierarchical data structures. Implement tree traversals, priority queues, and character prefix trees.",
                "topics": [
                    {
                        "name": "Binary Trees & BST Search/Insert/Delete",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Recursive tree traversal, lowest common ancestor, and balanced AVL properties.",
                        "references": [
                            {"title": "VisuAlgo BST Visualizer", "url": "https://visualgo.net/en/bst", "type": "visualization"}
                        ]
                    },
                    {
                        "name": "Min/Max Binary Heaps & Top-K Problems",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Priority queues, heapify in O(n), and maintaining rolling top-K elements.",
                        "references": [
                            {"title": "Heap Data Structure Lecture", "url": "https://en.wikipedia.org/wiki/Binary_heap", "type": "article"}
                        ]
                    },
                    {
                        "name": "Tries (Prefix Trees) for Autocomplete",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Character node graphs for sub-millisecond string dictionary lookups.",
                        "references": [
                            {"title": "Trie Prefix Tree Implementation", "url": "https://leetcode.com/explore/learn/card/trie/", "type": "practice"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "VisuAlgo Binary Search Tree & Heap Visualizer", "url": "https://visualgo.net/en/bst", "type": "visualization"}
                ]
            },
            {
                "order": 5,
                "title": "5. Graph Theory & Connectivity",
                "description": "Represent networks with adjacency lists/matrices. Solve pathfinding, cycle detection, and dependency ordering.",
                "topics": [
                    {
                        "name": "Breadth-First Search (BFS) for Shortest Path",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Level-order queue traversal guaranteeing minimal step path on unweighted graphs.",
                        "references": [
                            {"title": "VisuAlgo Graph Traversals (BFS/DFS)", "url": "https://visualgo.net/en/dfsbfs", "type": "visualization"}
                        ]
                    },
                    {
                        "name": "Depth-First Search (DFS) & Connected Components",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Recursive visitation, backtracking, and island flood fill.",
                        "references": [
                            {"title": "Algorithms, Part II (Princeton)", "url": "https://www.coursera.org/learn/algorithms-part2", "type": "course"}
                        ]
                    },
                    {
                        "name": "Topological Sort & Kahn's Algorithm",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "In-degree tracking for linear ordering of directed acyclic dependencies.",
                        "references": [
                            {"title": "Topological Sort Explained", "url": "https://en.wikipedia.org/wiki/Topological_sorting", "type": "article"}
                        ]
                    },
                    {
                        "name": "Dijkstra's Shortest Path Algorithm",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Priority queue greedy relaxation for non-negative weighted graphs.",
                        "references": [
                            {"title": "VisuAlgo Single-Source Shortest Paths", "url": "https://visualgo.net/en/sssp", "type": "visualization"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Algorithms, Part II (Princeton / Coursera)", "url": "https://www.coursera.org/learn/algorithms-part2", "type": "course"}
                ]
            },
            {
                "order": 6,
                "title": "6. Dynamic Programming & Backtracking",
                "description": "Deconstruct overlapping subproblems and optimal substructure. Transition from top-down memoization to bottom-up tabulation.",
                "topics": [
                    {
                        "name": "Memoization (Top-Down) vs Tabulation (Bottom-Up)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "State transition recurrence formulation, cache keys, and space optimization.",
                        "references": [
                            {"title": "Dynamic Programming Patterns Guide", "url": "https://leetcode.com/discuss/general-discussion/458695/Dynamic-Programming-Patterns", "type": "guide"}
                        ]
                    },
                    {
                        "name": "1D & 2D Grid DP Patterns (Knapsack, LCS)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "0/1 Knapsack, longest common subsequence, and edit distance.",
                        "references": [
                            {"title": "Knapsack Problem Patterns", "url": "https://leetcode.com/discuss/general-discussion/458695/Dynamic-Programming-Patterns", "type": "guide"}
                        ]
                    },
                    {
                        "name": "Backtracking (Subsets, Permutations, N-Queens)",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Systematic state tree exploration with branch pruning.",
                        "references": [
                            {"title": "LeetCode Backtracking Study Guide", "url": "https://leetcode.com/explore/learn/card/recursion-ii/", "type": "practice"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Dynamic Programming Patterns Guide", "url": "https://leetcode.com/discuss/general-discussion/458695/Dynamic-Programming-Patterns", "type": "guide"}
                ]
            },
            {
                "order": 7,
                "title": "7. High-Frequency Patterns & Mock Rounds",
                "description": "Synthesize patterns under timed interview conditions. Practice clean code communication and edge case handling.",
                "topics": [
                    {
                        "name": "Blind 75 & NeetCode 150 High-Yield Problems",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Comprehensive core problem set covering 95% of interview patterns.",
                        "references": [
                            {"title": "Blind 75 LeetCode Questions List", "url": "https://leetcode.com/discuss/general-discussion/460599/blind-75-leetcode-questions", "type": "practice"},
                            {"title": "NeetCode 150 Interactive Sheet", "url": "https://neetcode.io/practice", "type": "practice"}
                        ]
                    },
                    {
                        "name": "Timed 45-Minute Mock Technical Screenings",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Practice coding without IDE autocomplete while explaining your thought process out loud.",
                        "references": [
                            {"title": "Pramp Free Peer Mock Interviews", "url": "https://www.pramp.com/", "type": "tool"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Blind 75 LeetCode Questions", "url": "https://leetcode.com/discuss/general-discussion/460599/blind-75-leetcode-questions", "type": "practice"}
                ]
            }
        ]

        steps = []
        for m in modules:
            step_id = str(uuid.uuid4())[:8]
            steps.append({
                "id": step_id,
                "title": m["title"],
                "description": m["description"],
                "topics": m["topics"],
                "resources": m.get("resources", []),
                "resource_ids": [],
                "skill_ids": [],
                "order": m["order"],
                "completed": False
            })

        return {
            "goal_title": resolved_title,
            "target_role": resolved_role,
            "description": "Comprehensive Algorithms & Data Structures roadmap modeled after roadmap.sh covering complexity analysis, linear structures, trees, graphs, dynamic programming, and interview patterns.",
            "youtube_playlists": youtube_playlists,
            "related_roadmaps": related_roadmaps,
            "steps": steps
        }

    # -------------------------------------------------------------
    # 3. CORE BACKEND SDE (roadmap.sh/backend)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["backend", "server", "api engineer", "distributed system"]):
        resolved_title = "Backend Developer (roadmap.sh/backend)"
        resolved_role = target_role or "Core Backend Software Engineer"

        youtube_playlists = [
            {
                "title": "Backend Engineering & Architecture",
                "channel": "Hussein Nasser",
                "url": "https://www.youtube.com/@hnasr",
                "badge": "Industry Standard",
                "videos_count": "300+ Deep Dives"
            },
            {
                "title": "System Design & Distributed Scalability",
                "channel": "ByteByteGo / Alex Xu",
                "url": "https://www.youtube.com/@ByteByteGo",
                "badge": "Top Rated",
                "videos_count": "50+ Videos"
            },
            {
                "title": "Python Backend & Frameworks",
                "channel": "Corey Schafer",
                "url": "https://www.youtube.com/@coreyms",
                "badge": "Complete Series",
                "videos_count": "80+ Videos"
            }
        ]

        related_roadmaps = [
            "DevOps & Cloud",
            "Data Structures & Algorithms",
            "System Design",
            "PostgreSQL",
            "AI Engineer"
        ]

        modules = [
            {
                "order": 1,
                "title": "1. Language Mastery, Concurrency & Memory",
                "description": "Deep-dive into a primary backend language. Master thread models, async event loops, memory layout, and garbage collection.",
                "topics": [
                    {
                        "name": "Async I/O, Event Loops & Concurrency",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Non-blocking cooperative multitasking, event loops, and thread pool worker dispatching.",
                        "references": [
                            {"title": "roadmap.sh Backend Guide", "url": "https://roadmap.sh/backend", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Standard Library Networking & HTTP Client/Server",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Raw TCP socket handling, TLS handshake negotiation, and HTTP/1.1 vs HTTP/2 protocol frames.",
                        "references": [
                            {"title": "MDN HTTP Overview", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "roadmap.sh Backend Guide", "url": "https://roadmap.sh/backend", "type": "guide"}
                ]
            },
            {
                "order": 2,
                "title": "2. Relational & Distributed Databases",
                "description": "Design relational schemas with ACID guarantees, write optimized SQL, and tune indexes (B-Tree, Hash, GIN).",
                "topics": [
                    {
                        "name": "PostgreSQL Schema Design & Normalization",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Entity relationship design, foreign keys, constraints, and 3NF normalization.",
                        "references": [
                            {"title": "PostgreSQL Official Documentation", "url": "https://www.postgresql.org/docs/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "B-Tree Indexing, EXPLAIN ANALYZE & Query Plans",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Reading query execution plans, preventing sequential table scans, and composite index ordering.",
                        "references": [
                            {"title": "Use The Index, Luke (SQL Indexing Guide)", "url": "https://use-the-index-luke.com/", "type": "guide"}
                        ]
                    },
                    {
                        "name": "ACID Properties & Transaction Isolation Levels",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Read Committed, Repeatable Read, and Serializable levels preventing dirty/phantom reads.",
                        "references": [
                            {"title": "Transaction Isolation Levels in Databases", "url": "https://en.wikipedia.org/wiki/Isolation_(database_systems)", "type": "article"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Use The Index, Luke", "url": "https://use-the-index-luke.com/", "type": "guide"}
                ]
            },
            {
                "order": 3,
                "title": "3. API Architecture & Communication Protocols",
                "description": "Engineer resilient APIs across REST, gRPC/Protobuf, and real-time WebSockets with strict input validation.",
                "topics": [
                    {
                        "name": "RESTful API Standards & Idempotency",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Idempotent HTTP verbs, status codes, pagination, and error payload structures.",
                        "references": [
                            {"title": "REST API Tutorial", "url": "https://restfulapi.net/", "type": "guide"}
                        ]
                    },
                    {
                        "name": "gRPC & Protocol Buffers for Low-Latency RPCs",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Binary serialization, HTTP/2 multiplexing, and bi-directional streaming.",
                        "references": [
                            {"title": "gRPC Official Documentation", "url": "https://grpc.io/docs/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Authentication & Authorization (OAuth2, JWT, RBAC)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Token verification, refresh rotations, and granular role permissions.",
                        "references": [
                            {"title": "Auth0 JWT Handbook", "url": "https://auth0.com/resources/ebooks/jwt-handbook", "type": "guide"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "gRPC Official Documentation", "url": "https://grpc.io/docs/", "type": "docs"}
                ]
            },
            {
                "order": 4,
                "title": "4. Caching & Asynchronous Message Queues",
                "description": "Alleviate database hotspots with distributed caching tiers and decouple background workloads using event brokers.",
                "topics": [
                    {
                        "name": "Redis Caching Strategies (Cache-Aside, Write-Through)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Sub-millisecond data retrieval and cache stampede protection.",
                        "references": [
                            {"title": "Redis Official University", "url": "https://university.redis.io/", "type": "course"}
                        ]
                    },
                    {
                        "name": "Message Queues & Event Streaming (RabbitMQ, Kafka)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Publish-subscribe fanout, partition consumer groups, and message persistence.",
                        "references": [
                            {"title": "Apache Kafka Quickstart", "url": "https://kafka.apache.org/quickstart", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Redis Official University", "url": "https://university.redis.io/", "type": "course"}
                ]
            },
            {
                "order": 5,
                "title": "5. System Design & Distributed Scalability",
                "description": "Architect high-availability systems with horizontal scaling, load balancing, circuit breakers, and database sharding.",
                "topics": [
                    {
                        "name": "Horizontal Scaling & Layer 4/Layer 7 Load Balancing",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Round-robin, least connections, sticky sessions, and TLS termination.",
                        "references": [
                            {"title": "System Design Primer by Donne Martin", "url": "https://github.com/donnemartin/system-design-primer", "type": "guide"}
                        ]
                    },
                    {
                        "name": "CAP Theorem & PACELC Tradeoffs",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Consistency vs Availability during network partitions and latency tradeoffs.",
                        "references": [
                            {"title": "CAP Theorem Overview", "url": "https://en.wikipedia.org/wiki/CAP_theorem", "type": "article"}
                        ]
                    },
                    {
                        "name": "Rate Limiting Algorithms (Token Bucket, Leaky Bucket)",
                        "importance": "Recommended",
                        "completed": False,
                        "description": "Protecting public endpoints against denial of service and traffic spikes.",
                        "references": [
                            {"title": "Rate Limiting Architecture", "url": "https://cloud.google.com/architecture/rate-limiting-strategies-techniques", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "guide"}
                ]
            }
        ]

        steps = []
        for m in modules:
            step_id = str(uuid.uuid4())[:8]
            steps.append({
                "id": step_id,
                "title": m["title"],
                "description": m["description"],
                "topics": m["topics"],
                "resources": m.get("resources", []),
                "resource_ids": [c.id for c in saved_courses[:2]],
                "skill_ids": [],
                "order": m["order"],
                "completed": False
            })

        return {
            "goal_title": resolved_title,
            "target_role": resolved_role,
            "description": "Comprehensive Backend Engineering roadmap modeled after roadmap.sh/backend covering language internals, databases, API protocols, caching, message queues, and system design.",
            "youtube_playlists": youtube_playlists,
            "related_roadmaps": related_roadmaps,
            "steps": steps
        }

    # -------------------------------------------------------------
    # 4. FRONTEND DEVELOPER (roadmap.sh/frontend)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["frontend", "front-end", "react", "vue", "javascript", "ui"]):
        resolved_title = "Frontend Developer (roadmap.sh/frontend)"
        resolved_role = target_role or "Modern Frontend Software Engineer"

        youtube_playlists = [
            {
                "title": "Modern Frontend & Full Stack Masterclass",
                "channel": "Traversy Media",
                "url": "https://www.youtube.com/@TraversyMedia",
                "badge": "Comprehensive",
                "videos_count": "50+ Playlists"
            },
            {
                "title": "React & JavaScript Simplified",
                "channel": "Web Dev Simplified",
                "url": "https://www.youtube.com/@WebDevSimplified",
                "badge": "Top Rated",
                "videos_count": "120+ Videos"
            }
        ]

        related_roadmaps = [
            "Backend Developer",
            "Full Stack Developer",
            "TypeScript",
            "React",
            "DevOps & Cloud"
        ]

        modules = [
            {
                "order": 1,
                "title": "1. Internet, Modern HTML & Semantic Architecture",
                "description": "Understand how the browser works, DNS resolution, DOM rendering tree, and semantic accessible HTML5 elements.",
                "topics": [
                    {
                        "name": "How Browsers Work (DOM, CSSOM, Render Tree)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Browser parsing, paint cycles, reflow, and critical rendering path.",
                        "references": [
                            {"title": "MDN How Browsers Work", "url": "https://developer.mozilla.org/en-US/docs/Web/Performance/How_browsers_work", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Semantic HTML5 & WCAG Web Accessibility (a11y)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "ARIA roles, keyboard focus management, and screen reader compatibility.",
                        "references": [
                            {"title": "W3C Web Accessibility Initiative", "url": "https://www.w3.org/WAI/fundamentals/accessibility-intro/", "type": "guide"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "roadmap.sh Frontend Guide", "url": "https://roadmap.sh/frontend", "type": "guide"}
                ]
            },
            {
                "order": 2,
                "title": "2. Modern CSS, Tailwind & Responsive Layouts",
                "description": "Master Flexbox, CSS Grid, custom properties, and utility-first Tailwind CSS.",
                "topics": [
                    {
                        "name": "CSS Flexbox & CSS Grid Mastery",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Two-dimensional layout composition, responsive fluid grids, and alignment.",
                        "references": [
                            {"title": "CSS-Tricks Complete Guide to Flexbox", "url": "https://css-tricks.com/snippets/css/a-guide-to-flexbox/", "type": "guide"}
                        ]
                    },
                    {
                        "name": "Tailwind CSS & Responsive Breakpoints",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "JIT compilation, utility classes, and dark mode theming.",
                        "references": [
                            {"title": "Tailwind CSS Official Documentation", "url": "https://tailwindcss.com/docs", "type": "doc"}
                        ]
                    }
                ],
                "resources": []
            },
            {
                "order": 3,
                "title": "3. JavaScript & TypeScript Deep Dive",
                "description": "Closures, prototypes, async event loops, promises, and strict type safety.",
                "topics": [
                    {
                        "name": "Event Loop, Promises & Async/Await",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Microtasks, macrotasks, and unhandled rejection handling.",
                        "references": [
                            {"title": "javascript.info Event Loop", "url": "https://javascript.info/event-loop", "type": "guide"}
                        ]
                    },
                    {
                        "name": "TypeScript Generics, Utility Types & Type Guards",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Strict type safety across frontend and API boundary schemas.",
                        "references": [
                            {"title": "TypeScript Handbook", "url": "https://www.typescriptlang.org/docs/handbook/intro.html", "type": "doc"}
                        ]
                    }
                ],
                "resources": []
            },
            {
                "order": 4,
                "title": "4. Modern React Ecosystem & State Architecture",
                "description": "Hooks (useState, useEffect, useMemo), React Query server cache, and component architecture.",
                "topics": [
                    {
                        "name": "React 19 Hooks & Server Components (RSC)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Component life cycles, memoization, and server-side rendering streaming.",
                        "references": [
                            {"title": "React Official Documentation", "url": "https://react.dev/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "TanStack React Query & Client Caching",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Stale-while-revalidate data fetching, optimistic UI updates, and cache invalidation.",
                        "references": [
                            {"title": "TanStack Query Docs", "url": "https://tanstack.com/query/latest", "type": "doc"}
                        ]
                    }
                ],
                "resources": []
            },
            {
                "order": 5,
                "title": "5. Performance, Web Vitals & Production Deployment",
                "description": "Optimize Core Web Vitals (LCP, INP, CLS), bundle splitting, and deployment to edge CDN platforms.",
                "topics": [
                    {
                        "name": "Core Web Vitals Optimization (LCP, INP, CLS)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Image lazy loading, font optimization, and reducing main thread blocking time.",
                        "references": [
                            {"title": "web.dev Core Web Vitals", "url": "https://web.dev/explore/learn-core-web-vitals", "type": "guide"}
                        ]
                    },
                    {
                        "name": "Vite Bundler & Production CI/CD Deployment",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Tree-shaking, code-splitting chunks, and deploying to Vercel/Cloudflare Pages.",
                        "references": [
                            {"title": "Vite Official Guide", "url": "https://vitejs.dev/guide/", "type": "doc"}
                        ]
                    }
                ],
                "resources": []
            }
        ]

        steps = []
        for m in modules:
            step_id = str(uuid.uuid4())[:8]
            steps.append({
                "id": step_id,
                "title": m["title"],
                "description": m["description"],
                "topics": m["topics"],
                "resources": m.get("resources", []),
                "resource_ids": [],
                "skill_ids": [],
                "order": m["order"],
                "completed": False
            })

        return {
            "goal_title": resolved_title,
            "target_role": resolved_role,
            "description": "Comprehensive Frontend Development roadmap modeled after roadmap.sh/frontend covering web architecture, HTML/CSS, TypeScript, React, state caching, and Web Vitals.",
            "youtube_playlists": youtube_playlists,
            "related_roadmaps": related_roadmaps,
            "steps": steps
        }

    # -------------------------------------------------------------
    # 5. CLOUD & DEVOPS (roadmap.sh/devops)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["devops", "cloud", "kubernetes", "docker", "infrastructure", "sre"]):
        resolved_title = "Cloud & DevOps (roadmap.sh/devops)"
        resolved_role = target_role or "DevOps / Site Reliability Engineer (SRE)"

        youtube_playlists = [
            {
                "title": "DevOps Bootcamp & Kubernetes Complete",
                "channel": "TechWorld with Nana",
                "url": "https://www.youtube.com/@TechWorldwithNana",
                "badge": "Top Rated",
                "videos_count": "100+ Videos"
            },
            {
                "title": "Docker & Kubernetes Full Course",
                "channel": "freeCodeCamp.org",
                "url": "https://www.youtube.com/watch?v=fqMOX6JJhGo",
                "badge": "Free Course",
                "videos_count": "6 Hours"
            }
        ]

        related_roadmaps = [
            "Backend Developer",
            "Linux",
            "Kubernetes",
            "Cyber Security",
            "AI Engineer"
        ]

        modules = [
            {
                "order": 1,
                "title": "1. Linux Internals, Networking & Scripting",
                "description": "Master Linux system administration, process isolation, bash scripting, and core networking fundamentals.",
                "topics": [
                    {
                        "name": "Linux Shell Scripting & CLI Automation",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Writing robust bash scripts, pipes, redirection, and cron automation.",
                        "references": [
                            {"title": "roadmap.sh DevOps Guide", "url": "https://roadmap.sh/devops", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Networking: DNS, TCP/IP, OSI Layers, TLS Certificates",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Routing, ports, iptables, and Let's Encrypt automated TLS renewal.",
                        "references": [
                            {"title": "Cloudflare Learning: How DNS Works", "url": "https://www.cloudflare.com/learning/dns/what-is-dns/", "type": "article"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "roadmap.sh DevOps Guide", "url": "https://roadmap.sh/devops", "type": "guide"}
                ]
            },
            {
                "order": 2,
                "title": "2. Containerization with Docker",
                "description": "Package applications with lightweight containers, multi-stage builds, and secure non-root users.",
                "topics": [
                    {
                        "name": "Optimized Multi-Stage Dockerfiles",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Minimizing image size using scratch/alpine base and caching build layers.",
                        "references": [
                            {"title": "Docker Multi-stage Builds Guide", "url": "https://docs.docker.com/build/building/multi-stage/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Docker Compose for Multi-Container Services",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Network bridge isolation, volume persistence, and environment secrets.",
                        "references": [
                            {"title": "Docker Compose Specification", "url": "https://docs.docker.com/compose/", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Docker Official Documentation", "url": "https://docs.docker.com/", "type": "docs"}
                ]
            },
            {
                "order": 3,
                "title": "3. Container Orchestration with Kubernetes (K8s)",
                "description": "Deploy, scale, and manage containerized applications with declarative Kubernetes manifests.",
                "topics": [
                    {
                        "name": "Kubernetes Architecture (Control Plane vs Worker Nodes)",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "API server, etcd, scheduler, kubelet, and kube-proxy coordination.",
                        "references": [
                            {"title": "Kubernetes Architecture Concepts", "url": "https://kubernetes.io/docs/concepts/architecture/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Pods, Deployments, Services & Ingress Controllers",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Declarative rollouts, ClusterIP, NodePort, and NGINX Ingress routing.",
                        "references": [
                            {"title": "Kubernetes Official Tutorials", "url": "https://kubernetes.io/docs/tutorials/", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Kubernetes Official Tutorials", "url": "https://kubernetes.io/docs/tutorials/", "type": "docs"}
                ]
            },
            {
                "order": 4,
                "title": "4. CI/CD Automation & Infrastructure as Code (IaC)",
                "description": "Automate build, test, and deployment workflows with GitHub Actions and provision reproducible cloud infrastructure via Terraform.",
                "topics": [
                    {
                        "name": "GitHub Actions CI/CD Pipeline Workflows",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Automated linting, test suites, matrix builds, and CD triggers on merge.",
                        "references": [
                            {"title": "GitHub Actions Documentation", "url": "https://docs.github.com/en/actions", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Terraform HCL Syntax, Providers & State Management",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Declarative cloud provisioning, remote S3 state locks, and modules.",
                        "references": [
                            {"title": "HashiCorp Terraform Tutorials", "url": "https://developer.hashicorp.com/terraform/tutorials", "type": "guide"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "HashiCorp Terraform Tutorials", "url": "https://developer.hashicorp.com/terraform/tutorials", "type": "guide"}
                ]
            },
            {
                "order": 5,
                "title": "5. Observability, Monitoring & Reliability",
                "description": "Collect the 3 pillars of observability (Metrics, Logs, Traces) to monitor uptime and troubleshoot incidents.",
                "topics": [
                    {
                        "name": "Prometheus Metrics Scraping & Alertmanager",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Time-series database querying with PromQL and configuring PagerDuty alerts.",
                        "references": [
                            {"title": "Prometheus Official Guide", "url": "https://prometheus.io/docs/introduction/overview/", "type": "doc"}
                        ]
                    },
                    {
                        "name": "Grafana Dashboard Creation & Visualization",
                        "importance": "Must Know",
                        "completed": False,
                        "description": "Real-time KPI graphs, SLO tracking, and alerting panels.",
                        "references": [
                            {"title": "Grafana Getting Started", "url": "https://grafana.com/docs/grafana/latest/getting-started/", "type": "doc"}
                        ]
                    }
                ],
                "resources": [
                    {"title": "Prometheus Official Guide", "url": "https://prometheus.io/docs/introduction/overview/", "type": "docs"}
                ]
            }
        ]

        steps = []
        for m in modules:
            step_id = str(uuid.uuid4())[:8]
            steps.append({
                "id": step_id,
                "title": m["title"],
                "description": m["description"],
                "topics": m["topics"],
                "resources": m.get("resources", []),
                "resource_ids": [c.id for c in saved_courses[:2]],
                "skill_ids": [],
                "order": m["order"],
                "completed": False
            })

        return {
            "goal_title": resolved_title,
            "target_role": resolved_role,
            "description": "Comprehensive Cloud & DevOps roadmap modeled after roadmap.sh/devops covering Linux, Docker, Kubernetes, CI/CD, Terraform, and observability.",
            "youtube_playlists": youtube_playlists,
            "related_roadmaps": related_roadmaps,
            "steps": steps
        }

    # -------------------------------------------------------------
    # 6. DYNAMIC AI LLM GENERATOR (For custom user queries)
    # -------------------------------------------------------------
    system_prompt = (
        "You are an expert curriculum developer and technical architect creating structured roadmaps modeled after roadmap.sh.\n"
        "Generate a sequential, milestone-based learning roadmap strictly adhering to the following JSON schema:\n"
        "{\n"
        "  \"roadmap_title\": \"string\",\n"
        "  \"target_role\": \"string\",\n"
        "  \"description\": \"string\",\n"
        "  \"related_roadmaps\": [\"string\"],\n"
        "  \"youtube_playlists\": [\n"
        "    {\"title\": \"string\", \"channel\": \"string\", \"url\": \"string\", \"badge\": \"string\"}\n"
        "  ],\n"
        "  \"modules\": [\n"
        "    {\n"
        "      \"title\": \"string (e.g. 1. Foundations)\",\n"
        "      \"description\": \"string\",\n"
        "      \"topics\": [\n"
        "        {\n"
        "          \"name\": \"string\",\n"
        "          \"importance\": \"Must Know | Recommended | Advanced\",\n"
        "          \"description\": \"string\",\n"
        "          \"references\": [\n"
        "            {\"title\": \"string\", \"url\": \"string\", \"type\": \"doc | guide | video\"}\n"
        "          ]\n"
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "1. Create between 5 and 7 progressive sequential modules.\n"
        "2. Provide 3-5 specific, practical subtopics per module.\n"
        "3. Include curated learning references for each subtopic.\n"
        "4. Output ONLY valid JSON matching this schema."
    )
    user_prompt = f"Goal / Topic: {goal_title}\nTarget Role: {target_role or goal_title}"

    try:
        llm_data = await call_llm_json(user_prompt, system_prompt)
        if llm_data and isinstance(llm_data, dict) and "modules" in llm_data and isinstance(llm_data["modules"], list):
            steps = []
            for idx, mod in enumerate(llm_data["modules"]):
                t_list = []
                for top in mod.get("topics", []):
                    if isinstance(top, dict):
                        t_list.append({
                            "name": top.get("name", "Core Topic"),
                            "importance": top.get("importance", "Must Know"),
                            "completed": False,
                            "description": top.get("description", "Core domain competency."),
                            "references": top.get("references", [
                                {"title": f"{top.get('name', 'Topic')} Reference", "url": "https://roadmap.sh", "type": "doc"}
                            ])
                        })
                    elif isinstance(top, str):
                        t_list.append({
                            "name": top,
                            "importance": "Must Know",
                            "completed": False,
                            "description": "Core domain competency.",
                            "references": [
                                {"title": f"{top} Reference", "url": "https://roadmap.sh", "type": "doc"}
                            ]
                        })

            return {
                "goal_title": llm_data.get("roadmap_title", goal_title),
                "target_role": llm_data.get("target_role", target_role or goal_title),
                "description": llm_data.get("description", f"AI-synthesized roadmap.sh learning path for {goal_title}."),
                "youtube_playlists": llm_data.get("youtube_playlists", [
                    {
                        "title": f"Mastering {goal_title}",
                        "channel": "freeCodeCamp.org",
                        "url": "https://www.youtube.com/@freecodecamp",
                        "badge": "Free Course",
                        "videos_count": "Complete Series"
                    }
                ]),
                "related_roadmaps": llm_data.get("related_roadmaps", ["Software Engineer", "Backend Developer", "System Design"]),
                "steps": steps
            }
    except Exception:
        pass

    # -------------------------------------------------------------
    # 7. GENERAL FALLBACK ROADMAP.SH TEMPLATE
    # -------------------------------------------------------------
    default_modules = [
        {
            "order": 1,
            "title": f"1. Core Competency & Foundational Architecture",
            "description": f"Master fundamental principles, syntax, toolchain setup, and core design paradigms for {goal_title}.",
            "topics": [
                {
                    "name": f"Foundations & Principles of {goal_title}",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Core concepts and architectural standards.",
                    "references": [{"title": "roadmap.sh Documentation", "url": "https://roadmap.sh", "type": "guide"}]
                },
                {
                    "name": "Development Environment & Tooling Setup",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Setting up CLI, package managers, and editors.",
                    "references": [{"title": "VS Code Setup Guide", "url": "https://code.visualstudio.com/", "type": "doc"}]
                },
                {
                    "name": "Standard Libraries & Core APIs",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Working with base libraries and built-in functions.",
                    "references": [{"title": "Official Language Docs", "url": "https://roadmap.sh", "type": "doc"}]
                }
            ]
        },
        {
            "order": 2,
            "title": "2. Intermediate Frameworks & Data Pipelines",
            "description": "Build end-to-end features integrating databases, external APIs, and asynchronous processing.",
            "topics": [
                {
                    "name": "Data Modeling, Storage & ORMs",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Database schemas, query builders, and object relational mappings.",
                    "references": [{"title": "SQL & Data Modeling Basics", "url": "https://roadmap.sh", "type": "doc"}]
                },
                {
                    "name": "RESTful & Real-Time API Architecture",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Handling requests, validation, and serialization.",
                    "references": [{"title": "RESTful Standards", "url": "https://restfulapi.net/", "type": "guide"}]
                }
            ]
        },
        {
            "order": 3,
            "title": "3. Production Testing, CI/CD & Deployment",
            "description": "Automate test coverage, containerize workloads, and configure continuous integration pipelines.",
            "topics": [
                {
                    "name": "Unit Testing & Automated Integration Suites",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Writing test assertions, fixtures, and coverage metrics.",
                    "references": [{"title": "Automated Testing Handbook", "url": "https://roadmap.sh", "type": "guide"}]
                },
                {
                    "name": "Docker Containerization & CI/CD Pipelines",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Multi-stage Docker builds and automated GitHub Actions workflows.",
                    "references": [{"title": "Docker Documentation", "url": "https://docs.docker.com/", "type": "doc"}]
                }
            ]
        },
        {
            "order": 4,
            "title": "4. System Performance, Scalability & Monitoring",
            "description": "Optimize latency, implement caching tiers, configure structured logging, and ensure resilient error handling.",
            "topics": [
                {
                    "name": "Performance Profiling & Bottleneck Mitigation",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Profiling memory allocations and execution latency.",
                    "references": [{"title": "Performance Optimization Guide", "url": "https://roadmap.sh", "type": "guide"}]
                },
                {
                    "name": "Structured Logging & Centralized Observability",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Metrics aggregation and distributed tracing.",
                    "references": [{"title": "OpenTelemetry Documentation", "url": "https://opentelemetry.io/", "type": "doc"}]
                }
            ]
        },
        {
            "order": 5,
            "title": "5. Portfolio Capstone & Technical Interview Readiness",
            "description": "Synthesize acquired skills into a production-grade portfolio project with live URL, tests, and documentation.",
            "topics": [
                {
                    "name": "Production Capstone Project with Live Demo",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Publicly hosted application solving real-world domain requirements.",
                    "references": [{"title": "Portfolio Project Architecture", "url": "https://roadmap.sh", "type": "guide"}]
                },
                {
                    "name": "System Design & Technical Deep-Dive Interview Prep",
                    "importance": "Must Know",
                    "completed": False,
                    "description": "Mock interview screening and architectural defense.",
                    "references": [{"title": "Tech Interview Handbook", "url": "https://www.techinterviewhandbook.org/", "type": "guide"}]
                }
            ]
        }
    ]

    steps = []
    for m in default_modules:
        step_id = str(uuid.uuid4())[:8]
        steps.append({
            "id": step_id,
            "title": m["title"],
            "description": m["description"],
            "topics": m["topics"],
            "resources": [],
            "resource_ids": [c.id for c in saved_courses[:2]],
            "skill_ids": [],
            "order": m["order"],
            "completed": False
        })

    return {
        "goal_title": goal_title,
        "target_role": target_role or goal_title,
        "description": f"Custom opportunity execution plan generated for {goal_title} modeled after roadmap.sh modules and competencies.",
        "youtube_playlists": [
            {
                "title": f"Complete {goal_title} Masterclass",
                "channel": "freeCodeCamp.org",
                "url": "https://www.youtube.com/@freecodecamp",
                "badge": "Free Course",
                "videos_count": "Full Series"
            }
        ],
        "related_roadmaps": ["Software Engineer", "Backend Developer", "System Design"],
        "steps": steps
    }
