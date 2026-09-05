import os
import json
from sub_agents.schemas import MatchDetail, MatchResult
from sub_agents.gemini_client import gemini_llm
from mcp_server.tools import resume_read
from agents.graphs.hunter_state import HunterState

async def match_node(state: HunterState) -> dict:

    cached_resume = state.get("cached_resume","")
    if not cached_resume:
        user_resume = resume_read.read_resume()
    
    resume_text = cached_resume if cached_resume else user_resume

    jobs = state.get("scout_data",{}).get("jobs",[])
    jobs_list = json.dumps(jobs, indent=2)
    
    prompt = f"""You are Hunter's Match Agent, an expert AI career strategist and technical recruiter.
    Your objective is to evaluate each job listing from a candidate's job discovery search against their technical resume, calculate a granular compatibility fit score (0-100), identify matching and missing skills, and output a ranked JSON list.

    CANDIDATE RESUME:
    {resume_text}

    SCOUTED JOB LISTINGS TO EVALUATE:
    {jobs_list} 
    EVALUATION RULES & SCORING CRITERIA:
    1. Evaluate EVERY single job provided in the SCOUTED JOB LISTINGS array.
    2. For each job, calculate fit_score (0-100) using this hierarchy:
       - Experience & Seniority Fit (40% weight - HIGHEST PRIORITY): Check required years vs candidate background. 
         * HARD RULE: If a job requires Senior/Lead experience (5+ yrs) and candidate has entry/intern background, CAP fit_score at MAX 45.
       - Core Technical Stack (35% weight): Overlap between candidate projects/skills & mandatory technologies.
       - Domain & Role Alignment (25% weight): Relevance of past domain experience to role responsibilities.
    3. Assign a verdict according to strict thresholds:
       - 85–100: "HIGHLY_RECOMMENDED" (Strong experience fit, 80%+ tech stack match)
       - 70–84: "GOOD_FIT" (Good experience fit, solid skills with 1-2 minor gaps)
       - 50–69: "MODERATE" (Transferable skills, notable tech stack or slight experience gap)
       - 30–49: "WEAK_FIT" (Experience level mismatch or major tech gap)
       - 0–29: "SKIP" (Unrelated role or severe requirement deficit)
    4. List specific matching_skills present in BOTH candidate resume and job requirements.
    5. List specific missing_skills required by job but NOT found in candidate resume.
    6. Mention the notable experience requirement.

    REQUIRED JSON OUTPUT STRUCTURE:
    Return ONLY a valid JSON object matching this schema:
    {{ 
      "total_scored": <number of jobs evaluated>,
      "ranked_jobs": [
      {{
        "job_id": "<job_id from listing>",
        "company": "<company name>",
        "role": "<job title>",
        "fit_score": <integer 0-100>,
        "matching_skills": ["skill1", "skill2"],
        "missing_skills": ["skill3"],
        "verdict": "<HIGHLY_RECOMMENDED | GOOD_FIT | MODERATE | WEAK_FIT | SKIP>"
    }}]
    }} """

    match_llm = gemini_llm(json_mode=True, temperature=0.4)

    try:
        response = match_llm.generate_content(prompt=prompt)
        match_agent_response = json.loads(response.text)

        if "ranked_jobs" in match_agent_response:
            match_agent_response["ranked_jobs"].sort(
                key=lambda x: x.get("fit_score",0),
                reverse = True )
        match_result = MatchResult(**match_agent_response)

    except Exception as e:
        print(f"Match Agent LLM parsing error: {e}")
        match_result = MatchResult(
            total_scored=len(jobs),
            ranked_jobs=[],
            report_path=None
        )
    
# ──  Generate & Save Evidence Report ─────────────────────────────
    report_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.normpath(os.path.join(report_dir, "match_report.md"))

    report_lines = [
        "# 🎯 Match Agent — Job Compatibility & Ranking Report\n",
        f"**Total Opportunities Evaluated:** {match_result.total_scored}\n",
        f"**Top Ranked Opportunities:** {len(match_result.ranked_jobs)}\n\n",
        "---",
        "## Ranked Compatibility Breakdown\n"
    ]

    if match_result.ranked_jobs:
        for i, detail in enumerate(match_result.ranked_jobs, 1):
            matching_str = ", ".join(detail.matching_skills) if detail.matching_skills else "None identified"
            missing_str = ", ".join(detail.missing_skills) if detail.missing_skills else "None identified"
            
            report_lines.append(
                f"### {i}. {detail.role} — {detail.company}\n"
                f"- **Job ID:** `{detail.job_id}`\n"
                f"- **Fit Score:** `{detail.fit_score}/100` | **Verdict:** `{detail.verdict}`\n"
                f"- **Matching Skills:** {matching_str}\n"
                f"- **Missing Skills / Gaps:** {missing_str}\n"
            )
    else:
        report_lines.append("_No job matches were scored or available for ranking._\n")
    
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        match_result.report_path = report_path
    except Exception as e:
        print(f"[MatchAgent] Warning: Failed to write report file: {e}")
    
    return {
        "match_data": match_result.model_dump()
    }