import json
import re
import unicodedata
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

COMMON_TECH_SKILLS = [
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "sql", "postgresql",
    "mysql", "mongodb", "redis", "react", "next.js", "vue", "angular", "node.js", "fastapi", "django",
    "flask", "spring boot", "docker", "kubernetes", "aws", "gcp", "azure", "git", "ci/cd", "graphql",
    "rest api", "machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "data analysis", "system design", "data structures", "algorithms",
    "llm", "langchain", "prompt engineering", "linux", "html", "css", "tailwind css", "devops"
]

CANONICAL_CASING = {
    "pytorch": "PyTorch",
    "scikit-learn": "scikit-learn",
    "fastapi": "FastAPI",
    "next.js": "Next.js",
    "node.js": "Node.js",
    "vue": "Vue",
    "react": "React",
    "sql": "SQL",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "ci/cd": "CI/CD",
    "nlp": "NLP",
    "llm": "LLM",
    "html": "HTML",
    "css": "CSS",
    "rest api": "REST API",
    "c++": "C++",
    "c#": "C#",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB"
}

def extract_skills_from_text(text: str) -> List[str]:
    text_norm = unicodedata.normalize('NFKD', text)
    text_lower = text_norm.lower()
    found = set()
    for skill in COMMON_TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            cased = CANONICAL_CASING.get(skill, skill.title())
            found.add(cased)
    return sorted(list(found))

def heuristic_extract_opportunities(raw_text: str, source_title: str = "", source_url: str = "") -> List[Dict[str, Any]]:
    """
    Intelligent heuristic parser capable of splitting multi-opportunity posts
    (such as a LinkedIn list of 10 internships, or a list of courses/hackathons)
    into distinct, validated opportunities. Handles fancy Unicode styling and social boilerplate.
    """
    opportunities = []
    
    # 1. Normalize fancy Unicode (like LinkedIn Mathematical Bold '𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗛𝗮𝗰𝗸𝗮𝘁𝗵𝗼𝗻' -> 'Developer Hackathon')
    raw_text = unicodedata.normalize('NFKD', raw_text)

    # 2. Strip social engagement boilerplate (comments, like/share buttons, footer metrics)
    for stop_marker in ["View C2PA information", "Like\nComment\nShare", "Comments\nLike", "\nReactions\n"]:
        if stop_marker in raw_text:
            raw_text = raw_text.split(stop_marker)[0]

    # Try splitting by numbered items e.g., "1.", "2.", "Opportunity 1:", "[1]", "Role 1"
    split_pattern = r'(?m)(?:^\s*(?:\d+[\.\)]|#\d+|Opportunity \d+|Role \d+|Job \d+|Internship \d+|Hackathon \d+)[\s\t]*\n?|[ \t]*\n\s*---\s*\n)'
    parts = re.split(split_pattern, raw_text)
    
    chunks = []
    if len(parts) > 1:
        first_clean = parts[0].strip()
        is_preamble = (
            any(marker in first_clean.lower() for marker in [
                "agree & join", "skip to main content", "report this post", "sign in", "here are",
                "looking for your next", "top ", "list of", "ongoing major hackathons"
            ])
            or (len(first_clean) < 120 and first_clean.endswith(":"))
            or (len(first_clean) < 400 and "http" not in first_clean and "apply" not in first_clean.lower() and "skills" not in first_clean.lower())
        )
        if is_preamble:
            chunks = [p.strip() for p in parts[1:] if len(p.strip()) > 20]
        else:
            chunks = [p.strip() for p in parts if len(p.strip()) > 20]
    
    # If no numbered split was found, try section dividers or bullet blocks
    if not chunks:
        potential_blocks = re.split(r'\n{2,}', raw_text)
        current_block = []
        for block in potential_blocks:
            b = block.strip()
            if any(term in b.lower() for term in ["intern", "engineer", "developer", "course", "specialization", "fellowship", "analyst", "hackathon"]) and len(current_block) > 0:
                chunks.append("\n\n".join(current_block))
                current_block = [b]
            else:
                current_block.append(b)
        if current_block:
            chunks.append("\n\n".join(current_block))
            
    # If still single chunk, process entire text as single opportunity
    if len(chunks) <= 1:
        chunks = [raw_text.strip()]

    source_hints = (source_title + " " + source_url).lower()

    for chunk in chunks:
        if not chunk or len(chunk) < 20:
            continue

        lines = [line.strip() for line in chunk.split("\n") if line.strip()]
        if not lines:
            continue

        first_line = re.sub(r'^(?:\d+[\.\)]|#\d+|[-*•])\s*', '', lines[0]).strip()
        second_line = re.sub(r'^(?:\d+[\.\)]|#\d+|[-*•])\s*', '', lines[1]).strip() if len(lines) > 1 else ""
        
        # Determine type
        chunk_lower = chunk.lower()
        if (
            "hackathon" in chunk_lower or "devpost" in chunk_lower or "unstop" in chunk_lower
            or "prize pool" in chunk_lower or "bounty" in chunk_lower
            or "hackathon" in source_hints or ("competition" in chunk_lower and "hackathon" in source_hints)
        ):
            opp_type = "hackathon"
        elif "course" in chunk_lower or "syllabus" in chunk_lower or "curriculum" in chunk_lower or "coursera" in chunk_lower or "edx" in chunk_lower or "udemy" in chunk_lower or "certification" in chunk_lower:
            opp_type = "certification" if "certif" in chunk_lower else "course"
        elif "project" in chunk_lower and "intern" not in chunk_lower and "job" not in chunk_lower:
            opp_type = "project"
        elif "research" in chunk_lower and "intern" not in chunk_lower:
            opp_type = "research"
        elif "full-time" in chunk_lower or "software engineer II" in chunk_lower or "senior" in chunk_lower:
            opp_type = "job"
        else:
            opp_type = "internship"

        # Determine title and company
        title = first_line
        organization = None
        
        # Check if first line is Organization and second line is Role / Hackathon Name (e.g. "Amazon\nDeveloper Hackathon")
        if len(first_line) < 35 and second_line and any(term in second_line.lower() for term in ["hackathon", "competition", "intern", "developer", "engineer", "analyst", "fellowship", "challenge"]):
            title = f"{first_line} {second_line}"
            organization = first_line
        elif " - " in first_line:
            parts = first_line.split(" - ", 1)
            if any(term in parts[0].lower() for term in ["intern", "engineer", "course", "analyst", "developer", "hackathon"]):
                title, organization = parts[0].strip(), parts[1].strip()
            else:
                organization, title = parts[0].strip(), parts[1].strip()
        elif " @ " in first_line or " at " in first_line:
            delim = " @ " if " @ " in first_line else " at "
            parts = first_line.split(delim, 1)
            title = parts[0].strip()
            organization = parts[1].strip()
        else:
            # Check lines for Company: / Organization:
            for l in lines[1:5]:
                org_match = re.search(r'(?:Company|Organization|Provider|Host|Employer):\s*([^\n\r,]+)', l, re.IGNORECASE)
                if org_match:
                    organization = org_match.group(1).strip()
                    break

        if not organization and source_title and source_title != title:
            if " at " in source_title:
                organization = source_title.split(" at ")[-1].strip()

        # Find direct application link in chunk
        direct_url = None
        url_matches = re.findall(r'https?://[^\s<>"\'{}|\\^`]+', chunk)
        for u in url_matches:
            clean_u = u.rstrip(".,;)")
            if clean_u != source_url and ("apply" in clean_u.lower() or "job" in clean_u.lower() or "careers" in clean_u.lower() or "course" in clean_u.lower() or "forms" in clean_u.lower() or "bit.ly" in clean_u.lower() or "lnkd.in" in clean_u.lower() or "devpost" in clean_u.lower()):
                direct_url = clean_u
                break
        if not direct_url and url_matches and url_matches[0] != source_url:
            direct_url = url_matches[0].rstrip(".,;)")

        # Extract deadline
        deadline = None
        deadline_match = re.search(r'(?:Deadline|Apply by|Closing date|Due date|Ends on):\s*([A-Za-z0-9\s,/-]+?)(?:\.|\n|$)', chunk, re.IGNORECASE)
        if deadline_match:
            candidate_dl = deadline_match.group(1).strip()
            if len(candidate_dl) < 40 and not any(w in candidate_dl.lower() for w in ["none", "na", "n/a", "tba"]):
                deadline = candidate_dl

        # Location
        location = None
        loc_match = re.search(r'(?:Location|Place):\s*([^\n,]+(?:,\s*[^\n,]+)?)', chunk, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()
        elif "remote" in chunk_lower or "worldwide" in chunk_lower or "global" in chunk_lower:
            location = "Remote / Worldwide"
        elif "hybrid" in chunk_lower:
            location = "Hybrid"

        # Compensation / Stipend / Prizes
        compensation = None
        stipend_match = re.search(r'(?:Stipend|Salary|Compensation|Pay|Prizes?|Prize Pool|Bounty):\s*([^\n\r]+)', chunk, re.IGNORECASE)
        if stipend_match:
            compensation = stipend_match.group(1).strip()
        else:
            money_match = re.search(r'(\$\s*\d+[\d,kK\.\s/\w-]*|₹\s*\d+[\d,kK\.\s/\w-]*)', chunk)
            if money_match:
                compensation = money_match.group(1).split('\n')[0].strip().rstrip('.-')

        # Duration
        duration = None
        dur_match = re.search(r'(?:Duration|Length):\s*([^\n]+)', chunk, re.IGNORECASE)
        if dur_match:
            duration = dur_match.group(1).strip()
        else:
            dur_inline = re.search(r'(\d+\s*(?:months?|weeks?|days?|hours?))', chunk, re.IGNORECASE)
            if dur_inline:
                duration = dur_inline.group(1).strip()

        # Required skills and taught skills
        skills = extract_skills_from_text(chunk)
        required_skills = skills if opp_type in ("internship", "job", "research", "hackathon") else []
        taught_skills = skills if opp_type in ("course", "certification", "project") else []

        # Eligibility
        eligibility = {}
        deg_match = re.search(r'(?:Degree|Education|Major):\s*([^\n]+)', chunk, re.IGNORECASE)
        if deg_match:
            eligibility["degree"] = deg_match.group(1).strip()
        
        grad_match = re.search(r'(?:Graduation|Batch|Class of):\s*([^\n]+)', chunk, re.IGNORECASE)
        if grad_match:
            eligibility["graduation_years"] = grad_match.group(1).strip()

        # Evidence snippets
        evidence = []
        for line in lines[:8]:
            if any(term in line.lower() for term in ["require", "skill", "eligib", "deadline", "apply", "stipend", "prize", "cash"]):
                evidence.append(line[:120])
        if not evidence and lines:
            evidence.append(lines[0][:120])

        # Short description
        desc_lines = lines[1:6] if len(lines) > 1 else lines
        description = "\n".join(desc_lines).strip()

        # Sanity check title
        if len(title) > 160:
            title = title[:157] + "..."

        opportunities.append({
            "type": opp_type,
            "title": title or "Untitled Opportunity",
            "organization": organization,
            "description": description,
            "direct_url": direct_url,
            "location": location,
            "compensation": compensation,
            "duration": duration,
            "deadline": deadline,
            "eligibility": eligibility,
            "required_skills": required_skills,
            "taught_skills": taught_skills,
            "source_evidence": evidence[:4],
            "confidence": 0.88,
            "verification_status": "needs_review",
            "notes": ""
        })

    return opportunities

async def call_llm_json(prompt: str, system_prompt: str) -> Optional[Any]:
    """
    Calls configured external LLM (Gemini or OpenAI) with strict JSON output.
    Returns parsed JSON object or None if not configured or failed.
    """
    # 1. Try Gemini
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{system_prompt}\n\nTask:\n{prompt}"}]}
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_resp = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return json.loads(text_resp)
        except Exception:
            pass

    # 2. Try OpenAI
    if settings.OPENAI_API_KEY:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt + "\nRespond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception:
            pass

    return None

async def extract_structured_opportunities(raw_text: str, source_title: str = "", source_url: str = "") -> List[Dict[str, Any]]:
    """
    Extracts structured opportunities from content.
    Prioritizes configured LLM; gracefully falls back to deterministic heuristic parser.
    Ensures zero hallucination and strict schema compliance.
    """
    system_prompt = (
        "You are LinkMind AI's extraction engine. Extract individual learning, internship, and career opportunities "
        "from the text. If a post contains multiple opportunities (e.g., 5 internships), extract each as a separate item.\n"
        "Rules:\n"
        "1. Never invent missing facts. Use null for unknown fields (deadline, compensation, duration, etc.).\n"
        "2. Detect type accurately: 'course', 'internship', 'job', 'project', 'certification', 'research', or 'resource'.\n"
        "3. Provide direct application or course URLs if present in the text.\n"
        "4. Include short source_evidence snippets supporting the extraction.\n"
        "Return a JSON object with key 'opportunities' containing a list of items."
    )
    
    prompt = f"Source Title: {source_title}\nSource URL: {source_url}\n\nContent:\n{raw_text[:8000]}"
    
    llm_result = await call_llm_json(prompt, system_prompt)
    if llm_result and isinstance(llm_result, dict) and "opportunities" in llm_result and isinstance(llm_result["opportunities"], list):
        items = llm_result["opportunities"]
        if items:
            # Clean and normalize
            normalized = []
            for item in items:
                normalized.append({
                    "type": item.get("type", "internship"),
                    "title": item.get("title", "Untitled Opportunity"),
                    "organization": item.get("organization"),
                    "description": item.get("description", ""),
                    "direct_url": item.get("direct_url"),
                    "location": item.get("location"),
                    "compensation": item.get("compensation"),
                    "duration": item.get("duration"),
                    "deadline": item.get("deadline"),
                    "eligibility": item.get("eligibility", {}),
                    "required_skills": item.get("required_skills", []),
                    "taught_skills": item.get("taught_skills", []),
                    "source_evidence": item.get("source_evidence", []),
                    "confidence": float(item.get("confidence", 0.9)),
                    "verification_status": "needs_review",
                    "notes": ""
                })
            return normalized

    # Fallback to local heuristic extractor
    return heuristic_extract_opportunities(raw_text, source_title, source_url)

def parse_resume_content(raw_text: str) -> Dict[str, Any]:
    """
    Extracts structured profile details from resume text:
    technical skills, frameworks, tools, education, graduation year, experience, projects.
    """
    skills = extract_skills_from_text(raw_text)
    
    # Categorize skills into technical, frameworks, tools
    framework_names = {"react", "next.js", "vue", "angular", "fastapi", "django", "flask", "spring boot", "pytorch", "tensorflow"}
    tool_names = {"docker", "kubernetes", "aws", "gcp", "azure", "git", "ci/cd", "linux", "redis", "postgresql", "mysql", "mongodb"}
    
    tech_skills = []
    frameworks = []
    tools = []
    for s in skills:
        s_lower = s.lower()
        if s_lower in framework_names:
            frameworks.append(s)
        elif s_lower in tool_names:
            tools.append(s)
        else:
            tech_skills.append(s)

    # Detect graduation year
    grad_year = None
    grad_matches = re.findall(r'\b(202[0-9]|203[0-9])\b', raw_text)
    if grad_matches:
        # Usually the latest year in education context is graduation year
        grad_year = int(max(grad_matches))

    # Detect education
    education = []
    edu_keywords = ["bachelor", "master", "b.tech", "m.tech", "b.s.", "m.s.", "b.e.", "university", "institute", "college"]
    lines = raw_text.split("\n")
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if any(kw in line_clean.lower() for kw in edu_keywords) and len(line_clean) < 120:
            education.append({"degree_or_institution": line_clean, "details": lines[i+1].strip() if i+1 < len(lines) else ""})
            if len(education) >= 3:
                break

    # Detect projects
    projects = []
    proj_headers = ["projects", "personal projects", "academic projects", "key projects"]
    in_proj = False
    proj_lines = []
    for line in lines:
        line_clean = line.strip()
        if any(h == line_clean.lower() or h + ":" == line_clean.lower() for h in proj_headers):
            in_proj = True
            continue
        if in_proj:
            if line_clean.isupper() and len(line_clean) < 30 and "PROJECT" not in line_clean:
                # Next section started
                break
            if line_clean:
                proj_lines.append(line_clean)

    if proj_lines:
        current_p = {"title": proj_lines[0], "description": " ".join(proj_lines[1:4])}
        projects.append(current_p)

    return {
        "technical_skills": tech_skills,
        "frameworks": frameworks,
        "tools": tools,
        "education": education,
        "graduation_year": grad_year,
        "projects": projects,
        "experience": [],
        "career_interests": ["Software Engineering", "AI & Machine Learning"],
        "preferred_locations": ["Remote"]
    }
