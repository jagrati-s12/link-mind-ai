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

async def generate_personalized_roadmap(db: Session, user_id: int, goal_title: str, target_role: str = "") -> Dict[str, Any]:
    """
    Builds a grounded, high-value career or technical roadmap using the structured logic
    of roadmap.sh (sequential modules, granular subtopics, importance levels, and connected resources).
    Tailored to user's saved courses, missing skills, and active resume.
    """
    user_skill_names = _extract_user_skills(db, user_id)

    # Get user's saved courses and opportunities
    saved_courses = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.type.in_(["course", "certification"]),
        Resource.is_archived == False
    ).all()

    saved_internships = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.type.in_(["internship", "job", "hackathon"]),
        Resource.is_archived == False
    ).all()

    goal_lower = goal_title.lower().strip()

    # -------------------------------------------------------------
    # 1. AI ENGINEER ROADMAP (https://roadmap.sh/ai)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["ai", "artificial intelligence", "llm", "machine learning", "genai", "agent", "deep learning"]):
        resolved_title = "AI Engineer Roadmap (roadmap.sh/ai)" if goal_lower in ("ai", "ai engineer", "artificial intelligence") else goal_title
        resolved_role = target_role or "AI Engineer / Generative AI Specialist"

        modules = [
            {
                "order": 1,
                "title": "1. AI Engineering Fundamentals & Pre-trained Models",
                "description": "Differentiate AI Engineering from ML Research. Master tokenization, context windows, parameters (temperature, top-p, top-k), and pricing models.",
                "topics": [
                    {"name": "AI Engineer vs ML Researcher Roles", "importance": "Must Know", "completed": False},
                    {"name": "Token Management & Context Windows", "importance": "Must Know", "completed": False},
                    {"name": "Model Parameters: Temperature, Top-P, Top-K", "importance": "Must Know", "completed": False},
                    {"name": "Closed vs Open Source Models (GPT-4o, Claude 3.5, Llama 3)", "importance": "Must Know", "completed": False},
                    {"name": "Local Model Execution (Ollama, vLLM, LM Studio)", "importance": "Recommended", "completed": False}
                ],
                "resources": _map_saved_courses(saved_courses, ["anthropic", "google", "cloud", "model", "foundation"]) or [
                    {"title": "roadmap.sh AI Engineer Guide", "url": "https://roadmap.sh/ai", "type": "guide"},
                    {"title": "Anthropic API Fundamentals", "url": "https://github.com/anthropics/courses/blob/master/anthropic_api_fundamentals/README.md", "type": "course"}
                ]
            },
            {
                "order": 2,
                "title": "2. Prompt Engineering & In-Context Learning",
                "description": "Move beyond casual chat to structured production prompts. Implement few-shot examples, reasoning chains, and schema-enforced structured outputs.",
                "topics": [
                    {"name": "Zero-Shot & Few-Shot Prompting", "importance": "Must Know", "completed": False},
                    {"name": "Chain-of-Thought (CoT) & Step-by-Step Reasoning", "importance": "Must Know", "completed": False},
                    {"name": "Strict JSON Output & Schema Enforcement", "importance": "Must Know", "completed": False},
                    {"name": "System Prompts & Formatting Delimiters", "importance": "Must Know", "completed": False},
                    {"name": "Directional Stimulus & Meta-Prompting", "importance": "Recommended", "completed": False}
                ],
                "resources": _map_saved_courses(saved_courses, ["prompt", "anthropic"]) or [
                    {"title": "Anthropic Prompt Engineering Tutorial", "url": "https://github.com/anthropics/courses/blob/master/prompt_engineering_interactive_tutorial/README.md", "type": "course"},
                    {"title": "Real World Prompting Techniques", "url": "https://github.com/anthropics/courses/blob/master/real_world_prompting/README.md", "type": "course"}
                ]
            },
            {
                "order": 3,
                "title": "3. Embeddings & Vector Databases",
                "description": "Understand dense vector representations for semantic search. Select and benchmark vector databases, distance metrics, and indexing algorithms.",
                "topics": [
                    {"name": "Dense Vector Representations & Cosine Similarity", "importance": "Must Know", "completed": False},
                    {"name": "Embedding Models (text-embedding-3, Voyage AI, BGE)", "importance": "Must Know", "completed": False},
                    {"name": "Vector DBs: ChromaDB, Pinecone, Qdrant, pgvector", "importance": "Must Know", "completed": False},
                    {"name": "Vector Indexing (HNSW, IVFFlat, Quantization)", "importance": "Recommended", "completed": False}
                ],
                "resources": _map_saved_courses(saved_courses, ["data", "analytics", "vector"]) or [
                    {"title": "ChromaDB Official Documentation", "url": "https://docs.trychroma.com/", "type": "docs"},
                    {"title": "Pinecone Vector Search Architecture", "url": "https://docs.pinecone.io/", "type": "docs"}
                ]
            },
            {
                "order": 4,
                "title": "4. Retrieval-Augmented Generation (RAG)",
                "description": "Build end-to-end RAG pipelines connecting proprietary knowledge to LLMs with minimal hallucination.",
                "topics": [
                    {"name": "Document Chunking Strategies (Recursive, Semantic, Window)", "importance": "Must Know", "completed": False},
                    {"name": "Semantic Retrieval & Top-K Sampling", "importance": "Must Know", "completed": False},
                    {"name": "Hybrid Search (Dense Semantic + Sparse BM25 Keyword)", "importance": "Recommended", "completed": False},
                    {"name": "Reranking Pipelines (Cohere Rerank, BGE Reranker)", "importance": "Recommended", "completed": False},
                    {"name": "Source Attribution & Citation Provenance", "importance": "Must Know", "completed": False}
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
                    {"name": "Function Calling & Tool Definition Schemas", "importance": "Must Know", "completed": False},
                    {"name": "ReAct (Reasoning + Acting) Decision Loops", "importance": "Must Know", "completed": False},
                    {"name": "Short-Term Buffer vs Long-Term Vector Memory", "importance": "Must Know", "completed": False},
                    {"name": "Multi-Agent Orchestration (LangGraph, CrewAI, AutoGen)", "importance": "Advanced", "completed": False},
                    {"name": "Error Recovery & Self-Correction Loops", "importance": "Recommended", "completed": False}
                ],
                "resources": _map_saved_courses(saved_courses, ["tool", "anthropic"]) or [
                    {"title": "Anthropic Tool Use Curriculum", "url": "https://github.com/anthropics/courses/blob/master/tool_use/README.md", "type": "course"}
                ]
            },
            {
                "order": 6,
                "title": "6. Evaluation, Security & Production Guardrails",
                "description": "Prevent regressions, defend against adversarial jailbreaks, evaluate accuracy, and trace production LLM calls.",
                "topics": [
                    {"name": "Automated LLM-as-a-Judge Evaluation Suites", "importance": "Must Know", "completed": False},
                    {"name": "Prompt Injection Defenses & Input Sanitization", "importance": "Must Know", "completed": False},
                    {"name": "Output Guardrails & PII Redaction", "importance": "Must Know", "completed": False},
                    {"name": "LLM Observability & Tracing (LangSmith, Phoenix)", "importance": "Recommended", "completed": False}
                ],
                "resources": _map_saved_courses(saved_courses, ["eval", "anthropic"]) or [
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
            "steps": steps
        }

    # -------------------------------------------------------------
    # 2. DATA STRUCTURES & ALGORITHMS (roadmap.sh/datastructures-and-algorithms)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["algo", "dsa", "data structure", "leetcode", "problem solving", "competitive programming"]):
        resolved_title = "Data Structures & Algorithms (DSA) Roadmap" if goal_lower in ("algo", "dsa", "algorithm", "algorithms") else goal_title
        resolved_role = target_role or "Software Engineer (Algorithms & Problem Solving)"

        modules = [
            {
                "order": 1,
                "title": "1. Algorithmic Complexity & Foundations",
                "description": "Master asymptotic notation, recursive recurrence relations, space/time complexity tradeoffs, and bit manipulation primitives.",
                "topics": [
                    {"name": "Big-O, Big-Omega, Big-Theta Analysis", "importance": "Must Know", "completed": False},
                    {"name": "Recursion Trees & Master Theorem", "importance": "Must Know", "completed": False},
                    {"name": "Space & Time Tradeoffs & In-Place Algorithms", "importance": "Must Know", "completed": False},
                    {"name": "Bitwise Operations & Masks", "importance": "Recommended", "completed": False}
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
                    {"name": "Dynamic Arrays & Amortized Insertion", "importance": "Must Know", "completed": False},
                    {"name": "Singly & Doubly Linked Lists", "importance": "Must Know", "completed": False},
                    {"name": "Stacks & Monotonic Stack Pattern", "importance": "Must Know", "completed": False},
                    {"name": "Queues, Circular Buffers & Deques", "importance": "Must Know", "completed": False},
                    {"name": "Two-Pointer (Opposite Ends & Fast/Slow)", "importance": "Must Know", "completed": False}
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
                    {"name": "Binary Search on Arrays & Boundary Finding", "importance": "Must Know", "completed": False},
                    {"name": "Binary Search on Answer / Predicate Functions", "importance": "Must Know", "completed": False},
                    {"name": "Fixed-Size Sliding Window", "importance": "Must Know", "completed": False},
                    {"name": "Variable-Size Sliding Window with Hash Maps", "importance": "Must Know", "completed": False}
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
                    {"name": "Binary Trees & BST Search/Insert/Delete", "importance": "Must Know", "completed": False},
                    {"name": "Tree Traversals (DFS In/Pre/Post, BFS Level-Order)", "importance": "Must Know", "completed": False},
                    {"name": "Min/Max Binary Heaps & Top-K Problems", "importance": "Must Know", "completed": False},
                    {"name": "Tries (Prefix Trees) for Autocomplete & Search", "importance": "Recommended", "completed": False}
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
                    {"name": "Breadth-First Search (BFS) for Shortest Path", "importance": "Must Know", "completed": False},
                    {"name": "Depth-First Search (DFS) & Connected Components", "importance": "Must Know", "completed": False},
                    {"name": "Topological Sort & Kahn's Algorithm", "importance": "Must Know", "completed": False},
                    {"name": "Dijkstra's Shortest Path Algorithm", "importance": "Must Know", "completed": False},
                    {"name": "Disjoint Set Union (DSU / Union-Find)", "importance": "Recommended", "completed": False}
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
                    {"name": "Memoization (Top-Down) vs Tabulation (Bottom-Up)", "importance": "Must Know", "completed": False},
                    {"name": "1D DP Patterns (Climbing Stairs, House Robber)", "importance": "Must Know", "completed": False},
                    {"name": "2D Grid DP & Subsequences (LCS, Edit Distance)", "importance": "Must Know", "completed": False},
                    {"name": "0/1 Knapsack & Unbounded Knapsack", "importance": "Must Know", "completed": False},
                    {"name": "Backtracking (Subsets, Permutations, Combinations)", "importance": "Recommended", "completed": False}
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
                    {"name": "Blind 75 & NeetCode 150 High-Yield Problems", "importance": "Must Know", "completed": False},
                    {"name": "Monotonic Queue & Interval Merging", "importance": "Must Know", "completed": False},
                    {"name": "Timed 45-Minute Mock Technical Screenings", "importance": "Must Know", "completed": False},
                    {"name": "Explaining Thought Process & Tradeoffs Aloud", "importance": "Must Know", "completed": False}
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
            "description": "Comprehensive Algorithms & Data Structures roadmap modeled after roadmap.sh covering algorithmic complexity, linear structures, trees, graphs, dynamic programming, and interview patterns.",
            "steps": steps
        }

    # -------------------------------------------------------------
    # 3. CORE BACKEND SDE (roadmap.sh/backend)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["backend", "server", "api engineer", "distributed system"]):
        resolved_title = "Core Backend SDE Roadmap (roadmap.sh/backend)" if goal_lower in ("backend", "core backend sde", "backend engineer") else goal_title
        resolved_role = target_role or "Core Backend Software Engineer"

        modules = [
            {
                "order": 1,
                "title": "1. Language Mastery, Concurrency & Memory",
                "description": "Deep-dive into a primary backend language (Python/Go/Java/C++). Master thread models, async event loops, memory layout, and garbage collection.",
                "topics": [
                    {"name": "Async I/O, Event Loops & Goroutines / Threads", "importance": "Must Know", "completed": False},
                    {"name": "Memory Management & Pointer / Value Semantics", "importance": "Must Know", "completed": False},
                    {"name": "Standard Library Networking & HTTP Client/Server", "importance": "Must Know", "completed": False},
                    {"name": "Error Handling Patterns & Context Deadlines", "importance": "Must Know", "completed": False}
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
                    {"name": "PostgreSQL Schema Design & Normalization", "importance": "Must Know", "completed": False},
                    {"name": "B-Tree Indexing, EXPLAIN ANALYZE & Query Plans", "importance": "Must Know", "completed": False},
                    {"name": "ACID Properties & Transaction Isolation Levels", "importance": "Must Know", "completed": False},
                    {"name": "Connection Pooling & Database Migrations (Alembic)", "importance": "Must Know", "completed": False},
                    {"name": "NoSQL Tradeoffs: Document, Key-Value, Columnar", "importance": "Recommended", "completed": False}
                ],
                "resources": [
                    {"title": "Use The Index, Luke (SQL Indexing Guide)", "url": "https://use-the-index-luke.com/", "type": "guide"}
                ]
            },
            {
                "order": 3,
                "title": "3. API Architecture & Communication Protocols",
                "description": "Engineer resilient APIs across REST, gRPC/Protobuf, and real-time WebSockets with strict input validation.",
                "topics": [
                    {"name": "RESTful API Standards & Idempotency", "importance": "Must Know", "completed": False},
                    {"name": "gRPC & Protocol Buffers for Low-Latency RPCs", "importance": "Must Know", "completed": False},
                    {"name": "WebSockets & Server-Sent Events (SSE)", "importance": "Recommended", "completed": False},
                    {"name": "Authentication & Authorization (OAuth2, JWT, RBAC)", "importance": "Must Know", "completed": False}
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
                    {"name": "Redis In-Memory Caching Strategies (Cache-Aside, Write-Through)", "importance": "Must Know", "completed": False},
                    {"name": "Cache Invalidation, Cache Stampede & TTL Policies", "importance": "Must Know", "completed": False},
                    {"name": "Message Queues & Event Streaming (RabbitMQ, Kafka)", "importance": "Must Know", "completed": False},
                    {"name": "At-Least-Once Delivery & Idempotent Consumer Design", "importance": "Advanced", "completed": False}
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
                    {"name": "Horizontal Scaling & Layer 4/Layer 7 Load Balancing", "importance": "Must Know", "completed": False},
                    {"name": "CAP Theorem & PACELC Tradeoffs", "importance": "Must Know", "completed": False},
                    {"name": "Database Replication, Read Replicas & Sharding", "importance": "Must Know", "completed": False},
                    {"name": "Rate Limiting Algorithms (Token Bucket, Leaky Bucket)", "importance": "Recommended", "completed": False},
                    {"name": "Circuit Breakers, Retries & Exponential Backoff", "importance": "Recommended", "completed": False}
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
            "steps": steps
        }

    # -------------------------------------------------------------
    # 4. CLOUD & DEVOPS (roadmap.sh/devops)
    # -------------------------------------------------------------
    if any(term in goal_lower for term in ["devops", "cloud", "kubernetes", "docker", "infrastructure", "sre"]):
        resolved_title = "Cloud & DevOps Roadmap (roadmap.sh/devops)" if goal_lower in ("devops", "cloud", "cloud & devops") else goal_title
        resolved_role = target_role or "DevOps / Site Reliability Engineer (SRE)"

        modules = [
            {
                "order": 1,
                "title": "1. Linux Internals, Networking & Scripting",
                "description": "Master Linux system administration, process isolation, bash scripting, and core networking fundamentals.",
                "topics": [
                    {"name": "Linux Shell Scripting & CLI Automation", "importance": "Must Know", "completed": False},
                    {"name": "Process Management, File Descriptors & Signals", "importance": "Must Know", "completed": False},
                    {"name": "Networking: DNS, TCP/IP, OSI Layers, TLS Certificates", "importance": "Must Know", "completed": False},
                    {"name": "SSH Key Management & Security Best Practices", "importance": "Must Know", "completed": False}
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
                    {"name": "Container Runtimes, Namespaces & cgroups", "importance": "Must Know", "completed": False},
                    {"name": "Optimized Multi-Stage Dockerfiles", "importance": "Must Know", "completed": False},
                    {"name": "Docker Networking, Port Mapping & Volumes", "importance": "Must Know", "completed": False},
                    {"name": "Docker Compose for Multi-Container Local Dev", "importance": "Must Know", "completed": False}
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
                    {"name": "Kubernetes Architecture (Control Plane vs Worker Nodes)", "importance": "Must Know", "completed": False},
                    {"name": "Pods, Deployments, ReplicaSets & Rollouts", "importance": "Must Know", "completed": False},
                    {"name": "Services (ClusterIP, NodePort, LoadBalancer) & Ingress", "importance": "Must Know", "completed": False},
                    {"name": "ConfigMaps, Secrets & PersistentVolumeClaims", "importance": "Must Know", "completed": False},
                    {"name": "Helm Package Manager for Kubernetes Deployments", "importance": "Recommended", "completed": False}
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
                    {"name": "GitHub Actions CI/CD Pipeline Workflows", "importance": "Must Know", "completed": False},
                    {"name": "Automated Linting, Unit Testing & Security Scanning", "importance": "Must Know", "completed": False},
                    {"name": "Terraform HCL Syntax, Providers & State Management", "importance": "Must Know", "completed": False},
                    {"name": "Zero-Downtime Deployments (Blue-Green, Canary)", "importance": "Recommended", "completed": False}
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
                    {"name": "Prometheus Metrics Scraping & Alertmanager", "importance": "Must Know", "completed": False},
                    {"name": "Grafana Dashboard Creation & Visualization", "importance": "Must Know", "completed": False},
                    {"name": "Centralized Log Aggregation (ELK / Loki)", "importance": "Must Know", "completed": False},
                    {"name": "Distributed Tracing with OpenTelemetry", "importance": "Advanced", "completed": False}
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
            "steps": steps
        }

    # -------------------------------------------------------------
    # 5. DYNAMIC AI LLM GENERATOR (For custom user queries)
    # -------------------------------------------------------------
    system_prompt = (
        "You are an expert curriculum developer and technical architect creating structured roadmaps modeled after roadmap.sh.\n"
        "Generate a sequential, milestone-based learning roadmap strictly adhering to the following JSON schema:\n"
        "{\n"
        "  \"roadmap_title\": \"string\",\n"
        "  \"target_role\": \"string\",\n"
        "  \"description\": \"string\",\n"
        "  \"modules\": [\n"
        "    {\n"
        "      \"title\": \"string (e.g. 1. Foundations)\",\n"
        "      \"description\": \"string\",\n"
        "      \"topics\": [\n"
        "        {\n"
        "          \"name\": \"string\",\n"
        "          \"importance\": \"Must Know | Recommended | Advanced\"\n"
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "1. Create between 5 and 7 progressive sequential modules.\n"
        "2. Provide 3-5 specific, practical subtopics per module.\n"
        "3. Output ONLY valid JSON matching this schema."
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
                            "completed": False
                        })
                    elif isinstance(top, str):
                        t_list.append({
                            "name": top,
                            "importance": "Must Know",
                            "completed": False
                        })

                steps.append({
                    "id": str(uuid.uuid4())[:8],
                    "title": mod.get("title", f"Module {idx+1}"),
                    "description": mod.get("description", ""),
                    "topics": t_list,
                    "resources": [],
                    "resource_ids": [],
                    "skill_ids": [],
                    "order": idx + 1,
                    "completed": False
                })

            return {
                "goal_title": llm_data.get("roadmap_title", goal_title),
                "target_role": llm_data.get("target_role", target_role or goal_title),
                "description": llm_data.get("description", f"AI-synthesized roadmap.sh learning path for {goal_title}."),
                "steps": steps
            }
    except Exception:
        pass

    # -------------------------------------------------------------
    # 4. GENERAL FALLBACK ROADMAP.SH TEMPLATE
    # -------------------------------------------------------------
    default_modules = [
        {
            "order": 1,
            "title": f"1. Core Competency & Foundational Architecture",
            "description": f"Master fundamental principles, syntax, toolchain setup, and core design paradigms for {goal_title}.",
            "topics": [
                {"name": f"Foundations & Principles of {goal_title}", "importance": "Must Know", "completed": False},
                {"name": "Development Environment & Tooling Setup", "importance": "Must Know", "completed": False},
                {"name": "Standard Libraries & Core APIs", "importance": "Must Know", "completed": False},
                {"name": "Code Organization & Best Practices", "importance": "Recommended", "completed": False}
            ]
        },
        {
            "order": 2,
            "title": "2. Intermediate Frameworks & Data Pipelines",
            "description": "Build end-to-end features integrating databases, external APIs, and asynchronous processing.",
            "topics": [
                {"name": "Data Modeling, Storage & ORMs", "importance": "Must Know", "completed": False},
                {"name": "RESTful & Real-Time API Architecture", "importance": "Must Know", "completed": False},
                {"name": "Authentication, Authorization & Security", "importance": "Must Know", "completed": False},
                {"name": "State Management & Caching", "importance": "Recommended", "completed": False}
            ]
        },
        {
            "order": 3,
            "title": "3. Production Testing, CI/CD & Deployment",
            "description": "Automate test coverage, containerize workloads, and configure continuous integration and deployment pipelines.",
            "topics": [
                {"name": "Unit Testing & Automated Integration Suites", "importance": "Must Know", "completed": False},
                {"name": "Docker Containerization & Multi-Stage Builds", "importance": "Must Know", "completed": False},
                {"name": "CI/CD Pipeline Automation (GitHub Actions)", "importance": "Must Know", "completed": False},
                {"name": "Cloud Deployment & Environment Variables", "importance": "Recommended", "completed": False}
            ]
        },
        {
            "order": 4,
            "title": "4. System Performance, Scalability & Monitoring",
            "description": "Optimize latency, implement caching tiers, configure structured logging, and ensure resilient error handling.",
            "topics": [
                {"name": "Performance Profiling & Bottleneck Mitigation", "importance": "Must Know", "completed": False},
                {"name": "Structured Logging & Centralized Observability", "importance": "Must Know", "completed": False},
                {"name": "Distributed System Patterns & Message Queues", "importance": "Advanced", "completed": False},
                {"name": "Rate Limiting & Resilient Failure Handling", "importance": "Recommended", "completed": False}
            ]
        },
        {
            "order": 5,
            "title": "5. Portfolio Capstone & Technical Interview Readiness",
            "description": "Synthesize acquired skills into a production-grade portfolio project with live URL, tests, and documentation.",
            "topics": [
                {"name": "Production Capstone Project with Live Demo", "importance": "Must Know", "completed": False},
                {"name": "Comprehensive README & Architecture Diagrams", "importance": "Must Know", "completed": False},
                {"name": "System Design & Technical Deep-Dive Interview Prep", "importance": "Must Know", "completed": False},
                {"name": "Tailored Application Submissions & Portfolio Review", "importance": "Must Know", "completed": False}
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
        "steps": steps
    }
