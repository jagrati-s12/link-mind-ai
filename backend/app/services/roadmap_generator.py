import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Resource, UserProfile, Resume, UserSkill

def generate_personalized_roadmap(db: Session, user_id: int, goal_title: str, target_role: str = "") -> Dict[str, Any]:
    """
    Builds a grounded, high-value career or technical roadmap uniquely tailored
    to the user's goal, saved resources, missing skills, and active resume.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    active_resume = db.query(Resume).filter(Resume.user_id == user_id, Resume.is_active == True).first()
    user_skills_list = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    user_skill_names = set(us.skill.name.lower() for us in user_skills_list if us.skill)

    if active_resume and active_resume.parsed_data:
        parsed = active_resume.parsed_data
        for s in parsed.get("technical_skills", []) + parsed.get("frameworks", []) + parsed.get("tools", []):
            user_skill_names.add(s.lower())

    # Get user's saved courses and internships
    saved_courses = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.type.in_(["course", "certification"]),
        Resource.is_archived == False
    ).all()

    saved_internships = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.type.in_(["internship", "job"]),
        Resource.is_archived == False
    ).all()

    goal_lower = goal_title.lower().strip()

    # Specialized Roadmap 1: Data Structures & Algorithms (DSA / Algo)
    if any(term in goal_lower for term in ["algo", "dsa", "data structure", "leetcode", "problem solving", "competitive programming"]):
        resolved_title = "Data Structures & Algorithms (DSA) Roadmap" if goal_lower in ("algo", "dsa", "algorithm", "algorithms") else goal_title
        resolved_role = target_role or "Software Engineer (Algorithms & Problem Solving)"

        # Find any relevant courses in user's library
        relevant_course_ids = [
            c.id for c in saved_courses
            if any(term in (c.title + " " + (c.description or "")).lower() for term in ["algo", "data structure", "cs", "computer science", "python", "java", "c++"])
        ]
        if not relevant_course_ids and saved_courses:
            relevant_course_ids = [c.id for c in saved_courses[:2]]

        steps = [
            {
                "id": str(uuid.uuid4())[:8],
                "title": "Phase 1: Algorithmic Foundations & Complexity Analysis",
                "description": "Master asymptotic analysis (Big-O, Big-Omega, Big-Theta), recursion trees, space/time complexity trade-offs, and bitwise operations.",
                "resource_ids": relevant_course_ids[:1],
                "skill_ids": [],
                "order": 1,
                "completed": any(s in user_skill_names for s in ["algorithms", "data structures", "dsa"])
            },
            {
                "id": str(uuid.uuid4())[:8],
                "title": "Phase 2: Linear Data Structures & Binary Search",
                "description": "Implement and practice Arrays, Dynamic Arrays, Strings, Linked Lists, Stacks, Queues, and Binary Search (bounds and monotonic predicates).",
                "resource_ids": relevant_course_ids[1:2],
                "skill_ids": [],
                "order": 2,
                "completed": False
            },
            {
                "id": str(uuid.uuid4())[:8],
                "title": "Phase 3: Trees, Heaps & Prefix Structures",
                "description": "Master Binary Trees, BST operations, traversals (BFS/DFS), Min/Max Heaps, Priority Queues, and Trie structures for prefix matching.",
                "resource_ids": [],
                "skill_ids": [],
                "order": 3,
                "completed": False
            },
            {
                "id": str(uuid.uuid4())[:8],
                "title": "Phase 4: Graph Algorithms & Connectivity",
                "description": "Implement BFS, DFS, Cycle Detection, Topological Sort (Kahn's algorithm), Dijkstra's Shortest Path, and Disjoint Set Union (Union-Find).",
                "resource_ids": [],
                "skill_ids": [],
                "order": 4,
                "completed": False
            },
            {
                "id": str(uuid.uuid4())[:8],
                "title": "Phase 5: Dynamic Programming & Backtracking",
                "description": "Deconstruct optimal substructure with Memoization (top-down) and Tabulation (bottom-up): 1D DP, 2D Grid DP, 0/1 Knapsack, LCS, and Backtracking.",
                "resource_ids": [],
                "skill_ids": [],
                "order": 5,
                "completed": False
            },
            {
                "id": str(uuid.uuid4())[:8],
                "title": "Phase 6: High-Frequency Patterns & Mock Interview Rounds",
                "description": "Solve core patterns: Two Pointers, Sliding Window, Monotonic Stack, Interval Merging, and timed 45-minute coding rounds on Blind 75 / NeetCode 150.",
                "resource_ids": [i.id for i in saved_internships[:2]],
                "skill_ids": [],
                "order": 6,
                "completed": False
            }
        ]

        return {
            "goal_title": resolved_title,
            "target_role": resolved_role,
            "description": "Comprehensive step-by-step Algorithms & Data Structures mastery roadmap covering Big-O analysis, fundamental and non-linear data structures, graph theory, dynamic programming, and interview patterns.",
            "steps": steps
        }

    # Step 1: Skill Assessment
    known_skills_str = ", ".join([s.title() for s in list(user_skill_names)[:6]]) if user_skill_names else "Python, Git, Problem Solving"
    step1 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 1: Baseline Skill Assessment",
        "description": f"Verified current competencies: {known_skills_str}. Audit resume alignment against target '{goal_title}'.",
        "resource_ids": [],
        "skill_ids": [],
        "order": 1,
        "completed": True if len(user_skill_names) >= 3 else False
    }

    # Step 2: Targeted Learning
    course_ids = [c.id for c in saved_courses[:3]]
    courses_titles = ", ".join([c.title for c in saved_courses[:2]]) if saved_courses else "target technical specialization courses"
    step2 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 2: Complete Targeted Core Courses",
        "description": f"Close key skill gaps by working through saved resources: {courses_titles}.",
        "resource_ids": course_ids,
        "skill_ids": [],
        "order": 2,
        "completed": False
    }

    # Step 3: Practical Project
    step3 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 3: Build & Deploy Portfolio Project",
        "description": f"Synthesize core tools into a production-grade project with reproducible documentation, unit tests, and live deployment.",
        "resource_ids": [],
        "skill_ids": [],
        "order": 3,
        "completed": False
    }

    # Step 4: Shortlist & Refine Opportunities
    internship_ids = [i.id for i in saved_internships[:4]]
    internships_titles = ", ".join([i.title for i in saved_internships[:2]]) if saved_internships else "saved internship vacancies"
    step4 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 4: Target Application Shortlisting",
        "description": f"Review verified openings and align project bullet points with requirements: {internships_titles}.",
        "resource_ids": internship_ids,
        "skill_ids": [],
        "order": 4,
        "completed": False
    }

    # Step 5: Application Tracking & Interview Prep
    step5 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 5: Applications & Technical Rounds",
        "description": "Submit tailored applications ahead of deadlines, prepare technical DSA / system design topics, and log interview progress.",
        "resource_ids": [],
        "skill_ids": [],
        "order": 5,
        "completed": False
    }

    return {
        "goal_title": goal_title,
        "target_role": target_role or goal_title,
        "description": f"Custom opportunity execution plan generated for {goal_title} using {len(saved_courses)} saved courses and {len(saved_internships)} target opportunities.",
        "steps": [step1, step2, step3, step4, step5]
    }
