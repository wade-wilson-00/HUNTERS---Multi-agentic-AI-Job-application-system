#Scout Agent for searching through web for available Jobs

import os
import json
from agents.graphs.hunter_state import HunterState
from sub_agents.schemas import JobListing, ScoutResult
from mcp_server.tools import resume_read, web_search
from sub_agents.gemini_client import gemini_llm

async def scout_node(state: HunterState) -> dict:

    """ Unpack the User's details, task instructions and
        user's targeted role"""

    cached_resume = state.get("cached_resume","")
    task_instructions = state.get("task_instructions","")
    target_role = state.get("target_role","")

    #Call the read_resume MCP tool if cached resume doesn't exist
    if not cached_resume:
        cached_resume = resume_read.read_resume()
    
    scout_llm = gemini_llm(json_mode=True, temperature=0.6)
   
    role_info = target_role if target_role else "Use the Targeted role from Candidate's Resume"
    base_query = task_instructions.strip() if task_instructions else target_role.strip()
    
    queries = [
        f"{base_query}",
        f"{base_query} Hiring",
        f"{base_query} site:linkedin.com/jobs".strip()
    ]

    search_snippets = []
    for q in queries:
        try:
            print(f"[Scout Agent] Running web search for query: '{q}'...", flush=True)
            results = web_search.search_web(query=q, max_results=6)
            search_snippets.append(results)
        except Exception as e:
            print(f"[Scout Agent] Warning: Search failed: {e} for '{q}'", flush=True)
    
    combined_results = "\n\n".join(search_snippets)

    #Detailed Context for LLM
    prompt = f"""
    You are Hunter's Scout Agent, you are an expert Job Search strategist and responsible for searching high relevant jobs based on User's profile.
    CANDIDATE RESUME SUMMARY:
    {cached_resume[:1200]}
    RAW SEARCH RESULTS:
    {combined_results[:12000]}
    TASK:
    Extract up to 15 of the top most relevant, active job/internship listings from the raw search results above.
    Set "total_found" to the number of job objects in the "jobs" array.
    Ensure all quotes inside strings are validly escaped so the JSON is strictly valid.
    Return ONLY a JSON object matching this exact schema:
    {{
      "query_used": "{queries[0]}",
      "total_found": 0,
      "jobs": [
        {{
          "job_id": "scout_001",
          "title": "Job Title",
          "company": "Company Name",
          "location": "Location / Remote",
          "url": "https://...",
          "description_summary": "Brief 2-sentence summary",
          "required_skills": ["Skill1", "Skill2"],
          "source": "web_search"
        }}
      ]
    }}
    """
    response = scout_llm.generate_content(prompt)

    # ── Part 1: Parse LLM Response into ScoutResult ─────────────────────────
    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        llm_response = json.loads(raw_text)
        # Ensure total_found reflects actual jobs count if not matched
        if isinstance(llm_response.get("jobs"), list):
            llm_response["total_found"] = len(llm_response["jobs"])
        scout_result = ScoutResult(**llm_response)
    except Exception as e:
        print(f"[ScoutAgent] Warning: Failed to parse LLM response into ScoutResult: {e}")
        scout_result = ScoutResult(
            query_used=queries[0] if queries else "",
            total_found=0,
            jobs=[]
        )

    # ── Part 2: Generate & Save Evidence Report ─────────────────────────────
    report_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.normpath(os.path.join(report_dir, "scout_report.md"))

    report_lines = [
        "# 🏹 Scout Agent — Job Search Report\n",
        f"**Search Query Used:** `{scout_result.query_used}`\n",
        f"**Total Opportunities Discovered:** {scout_result.total_found}\n\n",
        "---",
        "## Discovered Job Listings\n"
    ]

    if scout_result.jobs:
        for i, job in enumerate(scout_result.jobs, 1):
            skills_str = ", ".join(job.required_skills) if job.required_skills else "N/A"
            report_lines.append(
                f"### {i}. {job.title} — {job.company}\n"
                f"- **Location:** {job.location}\n"
                f"- **URL:** [{job.url}]({job.url})\n"
                f"- **Required Skills:** {skills_str}\n"
                f"- **Summary:** {job.description_summary}\n"
            )
    else:
        report_lines.append("_No matching job listings were found for this query._\n")

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        scout_result.report_path = report_path
    except Exception as e:
        print(f"[ScoutAgent] Warning: Failed to write report file: {e}")

    # ── Part 3: Return State Update ─────────────────────────────────────────
    return {
        "scout_data": scout_result.model_dump()
    }
