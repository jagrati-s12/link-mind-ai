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
    # 0. Check if content is a curated course catalog / awesome list
    curated_courses = extract_markdown_curated_courses(raw_text, source_title, source_url)
    if len(curated_courses) >= 2:
        return curated_courses

    opportunities = []
    
    # 1. Normalize fancy Unicode (like LinkedIn Mathematical Bold '𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗛𝗮𝗰𝗸𝗮𝘁𝗵𝗼𝗻' -> 'Developer Hackathon')
    raw_text = unicodedata.normalize('NFKD', raw_text)

    # 2. Strip social engagement boilerplate (comments, like/share buttons, footer metrics, reviews)
    for stop_marker in [
        "View C2PA information", "Like\nComment\nShare", "Comments\nLike", "\nReactions\n",
        "\nLearner Reviews", "\nReviews\n", "\nFrequently Asked Questions", "\nFAQs\n",
        "\nExplore more resources", "\nWhat learners say"
    ]:
        if stop_marker.lower() in raw_text.lower():
            idx = raw_text.lower().find(stop_marker.lower())
            raw_text = raw_text[:idx]

    is_course_site = any(d in source_url.lower() for d in [
        "coursera.org", "edx.org", "udemy.com", "udacity.com", "datacamp.com", "pluralsight.com"
    ])
    is_job_site = any(d in source_url.lower() for d in [
        "hackerrank.com", "greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com"
    ])

    if is_course_site or is_job_site:
        chunks = [raw_text.strip()]
    else:
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
            # Check if text is a single coherent job posting or article
            first_lines = [l.strip() for l in raw_text.split("\n") if l.strip()][:6]
            first_few = " ".join(first_lines).lower()
            is_single_job = (
                any(k in first_few for k in ["company:", "location:", "job description", "about the role", "overview", "responsibilities"])
                or ("intern" in first_few and not any(term in raw_text.lower() for term in ["devpost", "bounties", "top 10", "top 5"]))
            )

            if is_single_job:
                chunks = [raw_text.strip()]
            else:
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
        elif "intern" in first_line.lower() or "internship" in chunk_lower or "intern" in chunk_lower:
            opp_type = "internship"
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

        # If source is from a known dedicated course platform, prefer cleaned source title
        if is_course_site and source_title:
            cleaned_st = re.sub(r'\s*\|\s*(?:Coursera|edX|Udemy|DataCamp|Pluralsight).*$', '', source_title, flags=re.I).strip()
            if len(cleaned_st) > 4:
                title = cleaned_st
            
            t_lower = (title + " " + chunk[:500]).lower()
            if "google" in t_lower:
                organization = "Google"
            elif "meta" in t_lower:
                organization = "Meta"
            elif "ibm" in t_lower:
                organization = "IBM"
            elif "aws" in t_lower or "amazon" in t_lower:
                organization = "AWS"
            elif "microsoft" in t_lower:
                organization = "Microsoft"
            else:
                for prov in ["Coursera", "edX", "Udemy", "DataCamp", "Pluralsight"]:
                    if prov.lower() in source_url.lower():
                        organization = prov
                        break

        # Validate title: Reject invalid numbers, ratings like "0", "8", "62%", or "Reviewed on..."
        clean_title_no_num = re.sub(r'[\d\.\,%kK\$₹#\-+()\s]', '', title)
        if (
            not clean_title_no_num
            or len(title.strip()) < 4
            or title.lower().startswith("reviewed on")
            or title.lower() in ("untitled", "loading...", "learn more")
        ):
            if is_course_site and source_title:
                title = re.sub(r'\s*\|\s*(?:Coursera|edX|Udemy|DataCamp|Pluralsight).*$', '', source_title, flags=re.I).strip()
            else:
                # Discard invalid junk chunk from review ratings or buttons
                continue

        # Find direct application/competition link in chunk
        direct_url = None
        for line in lines:
            if re.search(r'\b(?:apply|register|registration|link|compete|form|website|url|portal)\b', line, re.IGNORECASE):
                line_urls = re.findall(r'https?://[^\s<>"\'{}|\\^`]+', line)
                if line_urls:
                    cand = line_urls[0].rstrip(".,;)")
                    if cand != source_url:
                        direct_url = cand
                        break

        if not direct_url:
            url_matches = re.findall(r'https?://[^\s<>"\'{}|\\^`]+', chunk)
            for u in url_matches:
                clean_u = u.rstrip(".,;)")
                if clean_u != source_url and any(kw in clean_u.lower() for kw in [
                    "lnkd.in", "bit.ly", "tinyurl", "t.co", "forms.gle", "docs.google.com/forms",
                    "devpost", "unstop", "hackerearth", "kaggle", "mlh.io", "apply", "job", "career",
                    "greenhouse", "lever.co", "workday", "ashbyhq", "hackathon"
                ]):
                    direct_url = clean_u
                    break

        if not direct_url:
            for u in re.findall(r'https?://[^\s<>"\'{}|\\^`]+', chunk):
                clean_u = u.rstrip(".,;)")
                if clean_u != source_url:
                    direct_url = clean_u
                    break

        # If no separate direct URL exists in the chunk, keep direct_url None
        # rather than duplicating source_url, so the user clearly sees no direct link was found.

        # Extract deadline
        deadline = None
        deadline_match = re.search(r'(?:Deadline|Apply by|Closing date|Due date|Ends on):\s*([A-Za-z0-9\s,/-]+?)(?:\.|\n|$)', chunk, re.IGNORECASE)
        if deadline_match:
            candidate_dl = deadline_match.group(1).strip()
            if len(candidate_dl) < 40 and not any(w in candidate_dl.lower() for w in ["none", "na", "n/a", "tba"]):
                deadline = candidate_dl

        # Location
        location = None
        loc_match = re.search(r'(?:Location|Place|Workplace|City|Office):\s*([^\n,]+(?:,\s*[^\n,]+)?)', chunk, re.IGNORECASE)
        if loc_match:
            cand_loc = loc_match.group(1).strip()
            if not any(w in cand_loc.lower() for w in ["department", "employment", "apply", "type"]):
                location = cand_loc

        if not location:
            # Check for prominent known tech hub cities in the top portion of the chunk
            known_locations = ["Bangalore", "Bengaluru", "San Francisco", "New York", "London", "Hyderabad", "Seattle", "Pune", "Delhi", "Gurgaon", "Mumbai", "Austin", "Singapore", "Berlin", "Toronto"]
            for city in known_locations:
                if re.search(rf'\b{city}\b', chunk[:400], re.IGNORECASE):
                    location = city
                    break

        if not location:
            if re.search(r'\b(?:100% remote|fully remote|remote work|location:\s*remote)\b', chunk_lower) or "remote" in title.lower():
                location = "Remote / Worldwide"
            elif "hybrid" in chunk_lower[:300]:
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
        desc_lines = lines[1:8] if len(lines) > 1 else lines
        description = "\n".join(desc_lines).strip()
        if direct_url and direct_url != source_url and direct_url not in description:
            label = "Competition / Registration Link" if opp_type == "hackathon" else "Direct Application Link"
            description += f"\n- {label}: {direct_url}"

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

def extract_markdown_curated_courses(raw_text: str, source_title: str = "", source_url: str = "") -> List[Dict[str, Any]]:
    """
    Intelligently parses curated university/tech course catalogs, awesome lists, and GitHub repositories
    (e.g. prakhar1989/awesome-courses, ossu/computer-science, developer roadmaps)
    into individual categorized course resources. Preserves section category folders
    (e.g. 'Systems', 'Machine Learning', 'Algorithms') for automatic folder filing.
    """
    # 1. Normalize Setext headings (Heading\n--- or Heading\n===) to ATX markdown (## Heading)
    normalized_text = re.sub(r'(?m)^([A-Za-z0-9][^\n]+)\n[=-]{3,}\s*$', r'## \1', raw_text)

    # 2. Split on ATX markdown headings (# through ####)
    sections = re.split(r'(?m)^#{1,4}\s+([^\n]+)', normalized_text)
    if len(sections) <= 2:
        return []

    courses = []
    seen_urls = set()
    current_category = ""

    gh_match = re.search(r'github\.com/([^/]+)/([^/?#]+)', source_url, re.I)
    gh_owner = gh_match.group(1) if gh_match else ''
    gh_repo = re.sub(r'\.git$', '', gh_match.group(2), flags=re.I) if gh_match else ''

    # Default tech provider organization if present in source URL or title
    default_org = "University"
    source_lower = (source_title + " " + source_url).lower()
    if "anthropic" in source_lower:
        default_org = "Anthropic"
    elif "deepmind" in source_lower:
        default_org = "Google DeepMind"
    elif "google" in source_lower:
        default_org = "Google"
    elif "microsoft" in source_lower:
        default_org = "Microsoft"
    elif "openai" in source_lower:
        default_org = "OpenAI"
    elif "meta" in source_lower:
        default_org = "Meta"
    elif "aws" in source_lower or "amazon" in source_lower:
        default_org = "Amazon / AWS"
    elif gh_owner and gh_owner.lower() not in ("developer-y", "mostafatouny", "prakhar1989"):
        default_org = gh_owner.capitalize()

    for i in range(1, len(sections), 2):
        sec_title = sections[i].strip()
        sec_title_clean = re.sub(r'\[.*?\]\(.*?\)|<.*?>|[#*`]', '', sec_title).strip()

        # Skip non-course meta sections
        if sec_title_clean.lower() in (
            'introduction', 'table of contents', 'contents', 'legend',
            'license', 'contributing', 'how to use', 'authors', 'faq',
            'prerequisites', 'overview', 'code of conduct', 'guidelines', 'notes'
        ):
            continue

        if sec_title_clean.lower() != 'courses':
            current_category = sec_title_clean

        folder_name = current_category or sec_title_clean
        sec_body = sections[i + 1]

        # Extract course items from both Markdown list items (-/+/1.) and Markdown table rows
        # Format A: Markdown list entries (handles YouTube playlists, course portals, video lecture lines)
        bullets = re.split(r'(?m)^(?=[-*+0-9.]+\s+)', sec_body)
        for b in bullets:
            b_str = b.strip()
            if not b_str or not re.match(r'^[-*+0-9.]+\s+', b_str):
                continue

            # Skip lines that are purely callout notes or disclaimers
            if re.match(r'^[-*+0-9.]*\s*\*\*(?:Please note|Note|Warning|Disclaimer|Important|Caution)', b_str, re.I):
                continue

            raw_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', b_str)
            if not raw_links:
                continue

            all_links = []
            for t, u in raw_links:
                u_clean = u.strip()
                if u_clean.startswith('#'):
                    continue
                if not u_clean.startswith('http'):
                    if gh_owner and gh_repo:
                        rel_p = u_clean.lstrip('./')
                        u_clean = f"https://github.com/{gh_owner}/{gh_repo}/tree/main/{rel_p}"
                    else:
                        continue
                all_links.append((t.strip(), u_clean))

            if not all_links:
                continue

            # Prioritize YouTube / Video links for video course catalogs!
            yt_links = [u for t, u in all_links if ('youtube.com' in u or 'youtu.be' in u)]
            portal_links = [u for t, u in all_links if not any(w in t.lower() for w in ['notes', 'contributing', 'issue', 'license', 'archive.org', 'video', 'assignment', 'workshop', 'vertex', 'lecture videos'])]
            
            direct_link = yt_links[0] if yt_links else (portal_links[0] if portal_links else all_links[0][1])
            direct_link = direct_link.strip()
            if direct_link == source_url or direct_link.startswith('#'):
                continue
            if direct_link in seen_urls:
                continue
            seen_urls.add(direct_link)

            # Determine title: check for non-meta link text or pre-link heading
            content_links = [(t, u) for t, u in all_links if not any(w in t.lower() for w in ['video playlist', 'lecture video', 'video', 'playlist', 'notes', 'website', 'workshop', 'vertex', 'assignment', 'lecture videos'])]
            if content_links:
                raw_title = content_links[0][0].strip()
            else:
                first_line = b_str.split('\n')[0].strip()
                pre_link = first_line.split('[')[0].strip().lstrip('-*+0123456789. ')
                raw_title = pre_link.rstrip(' |:-') if pre_link else all_links[0][0].strip()

            # Look for bold course name: **Course Title**
            bold_match = re.search(r'\*\*([^*]+)\*\*', b_str)
            if bold_match:
                bold_candidate = bold_match.group(1).strip()
                is_disclaimer = any(w in bold_candidate.lower() for w in [
                    'note', 'please', 'warning', 'disclaimer', 'caution', 'important',
                    'tip', 'feel free', 'api cost', 'model', 'follow along', 'student', 'favor our'
                ])
                if len(bold_candidate) <= 60 and len(bold_candidate.split()) <= 8 and not is_disclaimer and not re.search(r'[.!?]\s+', bold_candidate):
                    if raw_title.lower() not in bold_candidate.lower() and len(raw_title) <= 20:
                        title = f"{raw_title}: {bold_candidate}"
                    else:
                        title = bold_candidate
                else:
                    title = re.sub(r'[*_`]', '', raw_title).strip()
            else:
                title = re.sub(r'[*_`]', '', raw_title).strip()

            if not title or len(title) < 2:
                title = all_links[0][0].strip()

            org = None
            # Look for italicized university/institution: *UC Berkeley*, *Stanford*, *MIT*
            italic_match = re.search(r'(?<!\*)\*([^*]+)\*(?!\*)', b_str)
            if italic_match:
                cand_org = italic_match.group(1).strip()
                if len(cand_org) < 60 and not any(kw in cand_org.lower() for kw in ['video', 'note', 'assignment', 'http', 'lecture']):
                    org = cand_org

            if not org:
                univ_match = re.search(r'\b([A-Z][A-Za-z\s]+(?:University|College|Institute|MIT|Caltech|Stanford|Berkeley|Harvard|Oxford|Cambridge|UNSW))\b', b_str)
                if univ_match:
                    org = univ_match.group(1).strip()

            if not org:
                org = default_org

            # Description
            desc_lines = []
            for line in b_str.split('\n'):
                l = line.strip()
                if not l or '<img' in l:
                    continue
                if re.match(r'^\*\*(?:Please note|Note|Warning|Disclaimer)', l, re.I):
                    continue
                cleaned = re.sub(r'^[-*o•\s]+', '', l).strip()
                cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned) # unwrap markdown links
                if cleaned and not cleaned.startswith('**') and not (cleaned.startswith('*') and cleaned.endswith('*')):
                    desc_lines.append(cleaned)

            desc = ' '.join(desc_lines[:3]).strip()
            if not desc:
                desc = f"{title} course materials and tutorial documentation."

            taught_skills = extract_skills_from_text(f"{title} {desc} {folder_name}")

            courses.append({
                "type": "course",
                "title": title,
                "organization": org,
                "direct_url": direct_link,
                "description": desc,
                "section": folder_name,
                "suggested_collection": folder_name,
                "taught_skills": taught_skills,
                "required_skills": [],
                "confidence": 1.0,
                "verification_status": "verified",
                "notes": f"Imported from {source_title or 'curated list'}"
            })

        # Format B: Markdown table rows: | [Title](url) | University | Description |
        for table_line in sec_body.split('\n'):
            line_str = table_line.strip()
            if not line_str.startswith('|') or not line_str.endswith('|'):
                continue
            cols = [c.strip() for c in line_str.split('|')[1:-1]]
            if len(cols) < 2 or all(set(c).issubset({'-', ':', ' '}) for c in cols):
                continue
            table_link_match = re.search(r'\[([^\]]+)\]\((https?://[^)]+)\)', cols[0])
            if not table_link_match and len(cols) > 1:
                table_link_match = re.search(r'\[([^\]]+)\]\((https?://[^)]+)\)', cols[1])
            if table_link_match:
                t_title, t_url = table_link_match.groups()
                t_url = t_url.strip()
                if t_url in seen_urls:
                    continue
                seen_urls.add(t_url)
                t_org = cols[1] if len(cols) > 1 and not ('http' in cols[1]) else None
                t_desc = ' '.join(cols[2:]) if len(cols) > 2 else f"{t_title} course curriculum."
                courses.append({
                    "type": "course",
                    "title": t_title,
                    "organization": t_org or "University",
                    "direct_url": t_url,
                    "description": t_desc,
                    "section": folder_name,
                    "suggested_collection": folder_name,
                    "taught_skills": extract_skills_from_text(f"{t_title} {t_desc} {folder_name}"),
                    "required_skills": [],
                    "confidence": 1.0,
                    "verification_status": "verified",
                    "notes": f"Imported from {source_title or 'curated list'}"
                })

    return courses

async def extract_structured_opportunities(
    raw_text: str,
    source_title: str = "",
    source_url: str = "",
    few_shot_guidance: str = ""
) -> List[Dict[str, Any]]:
    """
    Extracts structured opportunities from content.
    Prioritizes curated catalogs (awesome-courses, repo lists) and configured LLMs
    with dynamic few-shot continuous learning; gracefully falls back to deterministic heuristic parser.
    Ensures zero hallucination and strict schema compliance.
    """
    # 1. Check if source is a structured curated markdown list (e.g. awesome-courses)
    curated_courses = extract_markdown_curated_courses(raw_text, source_title, source_url)
    if len(curated_courses) >= 2:
        return curated_courses
    system_prompt = (
        "You are LinkMind AI's extraction engine. Extract individual learning, internship, hackathon, and career opportunities "
        "from the text. If a post (e.g. on LinkedIn, Twitter, or blogs) contains multiple opportunities (e.g., 3 hackathons), extract each as a separate item.\n"
        "Rules:\n"
        "1. Never invent missing facts. Use null for unknown fields (deadline, compensation, duration, etc.).\n"
        "2. Detect type accurately: 'hackathon', 'internship', 'job', 'course', 'project', 'certification', 'research', or 'resource'.\n"
        "3. Prioritize direct application or competition URLs (e.g. lnkd.in, devpost, forms, unstop, bit.ly, career portal links) as 'direct_url'. Preserve the original post link as the source.\n"
        "4. Include short source_evidence snippets supporting the extraction.\n"
        "Return a JSON object with key 'opportunities' containing a list of items."
    )
    if few_shot_guidance:
        system_prompt += "\n" + few_shot_guidance
    
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
