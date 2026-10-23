from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Resource, Recommendation, Application, Resume, UserSkill
from app.services.ai_adapter import call_llm_json

async def answer_assistant_query(
    db: Session,
    user_id: int,
    user_query: str,
    chat_history: List[Dict[str, str]] | None = None
) -> Dict[str, Any]:
    """
    Retrieves relevant user resources, recommendations, applications, and skills
    to provide grounded answers with citations.
    """
    query_lower = user_query.lower()
    
    # 1. Fetch user's saved resources
    all_resources = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.is_archived == False
    ).all()

    # 2. Fetch recommendations
    all_recs = db.query(Recommendation).filter(Recommendation.user_id == user_id).all()
    rec_by_res_id = {r.resource_id: r for r in all_recs}

    # 3. Fetch applications
    all_apps = db.query(Application).filter(Application.user_id == user_id).all()

    # 4. Fetch resume & skills
    active_resume = db.query(Resume).filter(Resume.user_id == user_id, Resume.is_active == True).first()
    skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    user_skills_str = ", ".join([us.skill.name for us in skills if us.skill])

    # If library is completely empty
    if not all_resources:
        return {
            "response": "Your LinkMind library is currently empty. To get started, paste a URL or upload a PDF/document in the Inbox to extract courses and internships, and upload your resume in Profile to see personalized match scores!",
            "citations": [],
            "suggested_actions": ["Paste an opportunity link", "Upload resume"]
        }

    # Score resources for retrieval
    scored_resources = []
    for res in all_resources:
        score = 0
        text = f"{res.title} {res.organization or ''} {res.description or ''} {' '.join(res.required_skills or [])} {' '.join(res.taught_skills or [])}".lower()
        for word in query_lower.split():
            if len(word) > 2 and word in text:
                score += 1
        
        # Priority matches based on specific intents
        if "deadline" in query_lower and res.deadline:
            score += 3
        if "internship" in query_lower and res.type == "internship":
            score += 2
        if "course" in query_lower and res.type in ("course", "certification"):
            score += 2
        
        scored_resources.append((score, res))

    scored_resources.sort(key=lambda x: x[0], reverse=True)
    top_matches = [r for score, r in scored_resources if score > 0][:5]
    if not top_matches:
        top_matches = [r for _, r in scored_resources[:4]]

    citations = [
        {
            "resource_id": r.id,
            "title": r.title,
            "type": r.type,
            "direct_url": r.direct_url
        }
        for r in top_matches
    ]

    # Check if external LLM is available
    system_prompt = (
        "You are LinkMind AI's personal opportunity intelligence assistant. "
        "Answer the user's question grounded STRICTLY in their saved opportunities, courses, and profile data provided below.\n"
        "Rules:\n"
        "1. Mention specific courses and internships by name.\n"
        "2. Do not invent courses, internships, or deadlines not present in the data.\n"
        "3. If information is missing or not supported by saved items, say so clearly.\n"
        "4. Keep your answer concise, practical, and formatted in clean markdown."
    )

    data_context = []
    for r in top_matches:
        rec = rec_by_res_id.get(r.id)
        rec_info = f"Fit score: {rec.fit_score}/100, Match: {rec.matching_skills}, Missing: {rec.missing_skills}" if rec else "No rec"
        data_context.append(
            f"- [{r.type.upper()}] {r.title} (Provider: {r.organization or 'Unknown'}). "
            f"Deadline: {r.deadline or 'None stated'}. Req skills: {r.required_skills}. {rec_info}"
        )

    context_str = "\n".join(data_context)
    prompt = f"User Skills: {user_skills_str}\n\nSaved Resources:\n{context_str}\n\nUser Question:\n{user_query}"

    llm_resp = await call_llm_json(prompt, system_prompt)
    if llm_resp and isinstance(llm_resp, dict) and "response" in llm_resp:
        return {
            "response": llm_resp["response"],
            "citations": citations,
            "suggested_actions": ["View resource details", "Add to roadmap"]
        }

    # Deterministic fallback response grounded in the retrieved records
    if "deadline" in query_lower:
        upcoming = [r for r in all_resources if r.deadline]
        if upcoming:
            lines = [f"- **{r.title}** ({r.organization or 'Provider'}): Deadline is **{r.deadline}**" for r in upcoming[:5]]
            resp_text = "Here are the opportunities with deadlines on record:\n\n" + "\n".join(lines)
        else:
            resp_text = "None of your currently saved opportunities have explicit deadlines listed. You can verify and update deadlines on the opportunity detail page."
    elif "internship" in query_lower or "match" in query_lower:
        internships = [r for r in top_matches if r.type in ("internship", "job")]
        if internships:
            lines = []
            for item in internships:
                rec = rec_by_res_id.get(item.id)
                score_badge = f"(Match Score: **{rec.fit_score}/100**)" if rec else ""
                lines.append(f"- **{item.title}** at {item.organization or 'Company'} {score_badge}. Required skills: {', '.join(item.required_skills or ['General'])}.")
            resp_text = "Here are your top matching opportunities:\n\n" + "\n".join(lines)
        else:
            resp_text = "No saved internships found matching your query. Try saving new opportunities from the Inbox!"
    elif "course" in query_lower or "learn" in query_lower:
        courses = [r for r in top_matches if r.type in ("course", "certification")]
        if courses:
            lines = [f"- **{c.title}** (Teaches: {', '.join(c.taught_skills or ['Core topics'])})" for c in courses]
            resp_text = "Here are the most relevant courses in your library:\n\n" + "\n".join(lines)
        else:
            resp_text = "No specific courses in your library match that skill yet. Save relevant course URLs to discover how they connect to your internships."
    else:
        lines = [f"- **{r.title}** ({r.type.title()})" for r in top_matches]
        resp_text = f"Based on your saved library, here are the most relevant items:\n\n" + "\n".join(lines)

    return {
        "response": resp_text,
        "citations": citations,
        "suggested_actions": ["Review matches", "Open Roadmaps"]
    }
