import os
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from playwright.async_api import async_playwright

from agents.graphs.hunter_state import HunterState
from sub_agents.schemas import ApplicationResult, ApplicationBatchResult
from sub_agents.gemini_client import gemini_llm
from mcp_server.tools import resume_read

# ── Profile & ATS Helpers ───────────────────────────────────────────────────

def get_resume_file_path() -> str:
    """Helper to locate the candidate's resume file path for Playwright upload."""
    workspace_profile = Path(__file__).parent.parent / "workspace_profile"
    if not workspace_profile.exists():
        return ""
    for fmt in [".pdf", ".docx", ".txt", ".md"]:
        matches = list(workspace_profile.glob(f"*{fmt}"))
        if matches:
            return str(matches[0].resolve())
    return ""


def detect_ats_platform(url: str) -> str:
    """Identifies the ATS platform from the job URL if recognizable."""
    url_lower = url.lower()
    if "greenhouse.io" in url_lower:
        return "Greenhouse"
    elif "lever.co" in url_lower:
        return "Lever"
    elif "workday" in url_lower or "myworkdayjobs" in url_lower:
        return "Workday"
    elif "ashbyhq.com" in url_lower:
        return "Ashby"
    elif "smartrecruiters.com" in url_lower:
        return "SmartRecruiters"
    elif "linkedin.com" in url_lower:
        return "LinkedIn"
    elif "indeed.com" in url_lower:
        return "Indeed"
    return "Custom/Direct"


async def extract_user_profile(resume_text: str) -> dict:
    """
    Extracts a structured candidate profile dictionary from resume text using Gemini.
    Returns clean key-value pairs needed by plan_form_fill.
    """
    prompt = f"""You are Hunter's Profile Extractor. Extract structured candidate information from the following resume text.
Extract full name, first name, last name, email address, phone number, LinkedIn URL, GitHub URL, portfolio/website URL, location/city/country, current title, years of experience, highest degree, university, major, and key skills.

CANDIDATE RESUME:
{resume_text}

Return ONLY a valid JSON object matching this exact structure:
{{
  "first_name": "...",
  "last_name": "...",
  "full_name": "...",
  "email": "...",
  "phone": "...",
  "linkedin_url": "...",
  "github_url": "...",
  "portfolio_url": "...",
  "location": "...",
  "city": "...",
  "country": "...",
  "current_title": "...",
  "years_of_experience": "...",
  "education": {{
    "degree": "...",
    "university": "...",
    "major": "..."
  }},
  "skills": ["..."]
}}
If any field is not found in the resume, set its value to an empty string "".
"""
    try:
        llm = gemini_llm(json_mode=True, temperature=0.1)
        res = llm.generate_content(prompt)
        return json.loads(res.text)
    except Exception as e:
        print(f"[ApplyAgent] Warning: Failed to extract structured user profile: {e}")
        return {"raw_resume": resume_text[:1000]}


# ── Step 3: DOM Extractor ────────────────────────────────────────────────────

async def extract_form_fields(page) -> list[dict]:
    """
    DOM Extractor — runs a JS script inside the live browser page to extract
    only meaningful, interactive form fields. Returns a clean list of dicts
    ready to be passed to the LLM form-fill planner.
    """

    js_script = """
    () => {
        const elements = document.querySelectorAll('input, textarea, select');
        const fields = [];
        const seenSelectors = new Set();

        elements.forEach(el => {
            // Filter out non-fillable or invisible field types
            const skipTypes = ['hidden', 'submit', 'button', 'reset', 'image', 'checkbox', 'radio'];
            if (skipTypes.includes(el.type)) return;
            if (el.offsetParent === null) return;  // Skip hidden/invisible elements

            // Build the best unique CSS selector for this element
            let selector = null;
            if (el.id) {
                selector = '#' + el.id;
            } else if (el.name) {
                selector = '[name="' + el.name + '"]';
            } else if (el.getAttribute('data-testid')) {
                selector = '[data-testid="' + el.getAttribute('data-testid') + '"]';
            }

            // Skip if we can't reliably target this element
            if (!selector) return;

            // Skip duplicates (e.g. mobile/desktop duplicate fields)
            if (seenSelectors.has(selector)) return;
            seenSelectors.add(selector);

            // Find the best human-readable label for this field
            let label = '';
            if (el.id) {
                const labelEl = document.querySelector('label[for="' + el.id + '"]');
                if (labelEl) label = labelEl.innerText.trim();
            }
            // Fallbacks if no <label for="..."> was found
            if (!label) label = el.getAttribute('aria-label') || '';
            if (!label) label = el.placeholder || '';
            if (!label) label = el.name || '';

            // Determine element type
            const tagName = el.tagName.toLowerCase();
            let type = tagName === 'input' ? (el.type || 'text') : tagName;

            fields.push({
                label:       label,
                selector:    selector,
                type:        type,
                required:    el.required || false,
                placeholder: el.placeholder || ''
            });
        });

        return fields;
    }
    """

    # Run the JS inside the live browser, returns a Python list of dicts
    raw_fields = await page.evaluate(js_script)

    # Post-processing in Python: cap at 20 fields to keep LLM prompt lean
    fields = raw_fields[:20]

    print(f"[ApplyAgent] DOM Extractor: found {len(raw_fields)} fields, using top {len(fields)}.")
    return fields


def is_valid_application_form(fields: list[dict]) -> tuple[bool, str]:
    """
    Validates whether the extracted fields represent a genuine job application form
    rather than a search engine bar, filter panel, or category index.
    """
    if not fields:
        return False, "No interactive form fields detected on page."

    app_keywords = [
        "name", "first", "last", "email", "phone", "resume", "cv", "attach",
        "portfolio", "linkedin", "github", "address", "city", "country", "education"
    ]
    search_keywords = ["search", "what", "where", "q", "query", "filter", "keywords"]

    field_strings = [
        f"{f.get('label', '')} {f.get('selector', '')} {f.get('placeholder', '')}".lower()
        for f in fields
    ]
    all_text = " ".join(field_strings)

    has_app_keyword = any(kw in all_text for kw in app_keywords)
    has_only_search = all(any(sk in s for sk in search_keywords) for s in field_strings)

    if has_only_search and not has_app_keyword:
        return False, "Page appears to be a search or filter portal rather than a candidate application form."

    if not has_app_keyword:
        return False, "Fields do not contain standard candidate application inputs (e.g. name, email, resume)."

    return True, "Valid application form detected."


# ── Step 4: LLM Form-Fill Planner ───────────────────────────────────────────

async def plan_form_fill(fields: list[dict], user_profile: dict) -> list[dict]:
    """
    Step 4: LLM Form-Fill Planner.
    Sends extracted DOM fields + user profile to Gemini.
    Returns a fill plan: [{selector, value}] with null entries excluded.
    """

    prompt = f"""You are Hunter's Apply Agent assistant. Your job is to map a candidate's profile data
to a job application form's fields accurately and completely.

CANDIDATE PROFILE:
{json.dumps(user_profile, indent=2)}

FORM FIELDS EXTRACTED FROM THE JOB APPLICATION PAGE:
{json.dumps(fields, indent=2)}

INSTRUCTIONS:
1. For each field in the FORM FIELDS list, determine the most accurate value from the CANDIDATE PROFILE.
2. Use the field's 'label', 'type', and 'placeholder' to understand what it's asking for.
3. For 'file' type fields (resume upload), return the exact value: "__RESUME_UPLOAD__" as a signal.
4. If no relevant data exists in the profile for a field, return null for that field's value.
5. Do NOT invent or fabricate data. Only use what is present in the profile.
6. For 'select' type fields, return the option text (not a numeric index).

Return ONLY a valid JSON array with this exact structure, no explanation:
[
  {{"selector": "<css selector>", "value": "<value or null>"}},
  ...
]"""

    planner_llm = gemini_llm(json_mode=True, temperature=0.1)

    try:
        response = planner_llm.generate_content(prompt)
        raw = json.loads(response.text)

        # Filter out null-value entries — don't attempt to fill fields with no data
        fill_plan = [
            entry for entry in raw
            if entry.get("value") is not None
        ]

        print(f"[ApplyAgent] LLM Planner: {len(fill_plan)} fields mapped from {len(fields)} extracted.")
        return fill_plan

    except Exception as e:
        print(f"[ApplyAgent] Warning: LLM form planner failed: {e}")
        return []


# ── Step 5: Playwright Form Filler ───────────────────────────────────────────

async def fill_form(page, fill_plan: list[dict], resume_pdf_path: str) -> int:
    """
    Step 5: Playwright Form Filler.
    Iterates the fill plan from Step 4 and fills each field using Playwright.
    Handles text inputs, textareas, selects, and file uploads.
    Returns the count of successfully filled fields.
    """

    filled_count = 0

    for entry in fill_plan:
        selector = entry.get("selector")
        value    = entry.get("value")

        if not selector or not value:
            continue

        try:
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=2500)

            # Determine field type by checking the element's tag/type attribute
            tag  = await element.evaluate("el => el.tagName.toLowerCase()")
            kind = await element.evaluate("el => el.type || el.tagName.toLowerCase()")

            # Handle resume file upload — special sentinel value
            if kind == "file" or value == "__RESUME_UPLOAD__":
                if resume_pdf_path and os.path.exists(resume_pdf_path):
                    await element.set_input_files(resume_pdf_path)
                    print(f"[ApplyAgent] Uploaded resume to: {selector}")
                else:
                    print(f"[ApplyAgent] Warning: Resume path not found, skipping file upload.")
                    continue

            # Handle <select> dropdowns
            elif tag == "select":
                await element.select_option(label=str(value))

            # Handle all text-like inputs and textareas
            else:
                await element.fill(str(value))

            filled_count += 1

        except Exception as e:
            print(f"[ApplyAgent] Warning: Could not fill field '{selector}': {e}")
            continue

    print(f"[ApplyAgent] Form Filler: successfully filled {filled_count}/{len(fill_plan)} fields.")
    return filled_count


# ── Step 6: HITL Checkpoint ──────────────────────────────────────────────────

async def hitl_checkpoint(job: dict, fill_plan: list[dict], filled_count: int, auto_decision: Optional[str] = None) -> str:
    """
    Step 6: Human-In-The-Loop (HITL) Checkpoint Logic.
    Presents the filled form details to the user and awaits confirmation.
    Returns: 'SUBMIT' | 'SKIP' | 'QUIT'
    """
    company = job.get("company", "Unknown Company")
    role = job.get("role", "Unknown Role")
    url = job.get("url", "")
    total_planned = len(fill_plan)

    print("\n" + "═" * 70)
    print(" 🛑 HUMAN-IN-THE-LOOP (HITL) CHECKPOINT — REVIEW BEFORE SUBMISSION")
    print("═" * 70)
    print(f" 🏢 Company : {company}")
    print(f" 💼 Role    : {role}")
    print(f" 🔗 URL     : {url}")
    print(f" 📝 Fields  : {filled_count}/{total_planned} fields successfully filled")
    print("─" * 70)
    print(" 📋 Form Fill Summary:")
    for entry in fill_plan[:10]:
        selector = entry.get("selector", "")
        val = str(entry.get("value", ""))
        val_display = val if len(val) <= 40 else val[:37] + "..."
        print(f"   • {selector:<25} -> {val_display}")
    if len(fill_plan) > 10:
        print(f"   ... and {len(fill_plan) - 10} more fields.")
    print("═" * 70)

    if auto_decision:
        dec = auto_decision.strip().upper()
        if dec in ("S", "SUBMIT"):
            print(f"[ApplyAgent] Auto-Decision: SUBMIT")
            return "SUBMIT"
        elif dec in ("Q", "QUIT"):
            print(f"[ApplyAgent] Auto-Decision: QUIT")
            return "QUIT"
        else:
            print(f"[ApplyAgent] Auto-Decision: SKIP")
            return "SKIP"

    print(" [S] Submit Application  |  [K] Skip This Job  |  [Q] Quit Apply Session")
    print("═" * 70)

    while True:
        try:
            choice = input("Enter decision [S/K/Q]: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\n[ApplyAgent] HITL input aborted. Defaulting to SKIP.")
            return "SKIP"

        if choice in ("S", "SUBMIT"):
            print("[ApplyAgent] Decision: Approved for submission.")
            return "SUBMIT"
        elif choice in ("K", "SKIP"):
            print("[ApplyAgent] Decision: Skipped application.")
            return "SKIP"
        elif choice in ("Q", "QUIT"):
            print("[ApplyAgent] Decision: Quitting apply session.")
            return "QUIT"
        else:
            print("Invalid input. Please enter 'S' to submit, 'K' to skip, or 'Q' to quit.")


# ── Step 7: Form Submission & Evidence Capture ───────────────────────────────

async def submit_application(page, job_id: str) -> tuple[bool, Optional[str], str]:
    """
    Step 7: Form Submission and Confirmation Handling.
    Locates and clicks the primary submit button, waits for response,
    and captures a confirmation screenshot.
    """
    screenshot_dir = Path(__file__).parent.parent / "workspace" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = str((screenshot_dir / f"apply_{job_id}_{timestamp}.png").resolve())

    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit Application")',
        'button:has-text("Submit application")',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        '[data-testid="submit-button"]'
    ]

    clicked = False
    for selector in submit_selectors:
        btn = page.locator(selector).first
        try:
            if await btn.is_visible(timeout=1000):
                print(f"[ApplyAgent] Clicking submit button: {selector}")
                await btn.click()
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        return False, None, "Could not find an interactive submit button on the page."

    # Wait for post-submission transition / confirmation
    try:
        await page.wait_for_load_state("networkidle", timeout=7000)
    except Exception:
        pass

    # Capture verification screenshot
    try:
        await page.screenshot(path=screenshot_path, full_page=False)
        print(f"[ApplyAgent] Saved confirmation screenshot to {screenshot_path}")
    except Exception as e:
        print(f"[ApplyAgent] Warning: Could not take screenshot: {e}")
        screenshot_path = None

    return True, screenshot_path, "Application submitted successfully."


# ── Report Generation ────────────────────────────────────────────────────────

def generate_application_report(batch: ApplicationBatchResult) -> str:
    """Generates an evidence report in workspace/reports/application_report.md."""
    report_dir = Path(__file__).parent.parent / "workspace" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "application_report.md"

    lines = [
        "# 📝 Apply Agent — Application Submission Report\n",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Total Applications Attempted:** {batch.total_attempted}\n",
        f"**Total Successfully Submitted:** {batch.total_submitted}\n\n",
        "---\n",
        "## Application Details\n"
    ]

    if batch.applications:
        for idx, app in enumerate(batch.applications, 1):
            status_icon = "✅" if app.status == "SUBMITTED" else ("⏸️" if app.status == "AWAITING_APPROVAL" else "❌")
            lines.append(f"### {idx}. {app.role} — {app.company}")
            lines.append(f"- **Job ID:** `{app.job_id}`")
            lines.append(f"- **URL:** [{app.url}]({app.url})")
            lines.append(f"- **ATS Platform:** `{app.ats_platform or 'Unknown'}`")
            lines.append(f"- **Status:** {status_icon} `{app.status}`")
            lines.append(f"- **Fields Filled:** `{app.form_fields_filled}`")
            if app.confirmation_screenshot:
                lines.append(f"- **Screenshot:** `{app.confirmation_screenshot}`")
            if app.notes:
                lines.append(f"- **Notes:** {app.notes}")
            lines.append("")
    else:
        lines.append("_No applications attempted._\n")

    try:
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return str(report_path.resolve())
    except Exception as e:
        print(f"[ApplyAgent] Warning: Could not write application report: {e}")
        return ""


# ── Step 8: Main Apply Node ──────────────────────────────────────────────────

async def apply_node(state: HunterState) -> dict:
    """
    Main orchestrator node for the Application Agent.
    Filters HIGHLY_RECOMMENDED and GOOD_FIT jobs, launches browser,
    extracts fields, maps profile values with LLM, executes Playwright filling,
    invokes HITL review gate, submits upon approval, and writes results to state.
    """
    # 1. Extract and unpack state with filtered ranked_jobs
    match_data = state.get("match_data", {})
    ranked_jobs = match_data.get("ranked_jobs", [])

    target_verdicts = tuple(state.get("apply_verdicts", ("HIGHLY_RECOMMENDED", "GOOD_FIT")))
    filtered_jobs = [
        job for job in ranked_jobs
        if job.get("verdict") in target_verdicts
    ]

    if not filtered_jobs:
        print(f"[ApplyAgent] No jobs matching verdicts {target_verdicts} to apply for.")
        empty_batch = ApplicationBatchResult(
            total_attempted=0,
            total_submitted=0,
            applications=[],
            report_path=None
        )
        return {"application_data": empty_batch.model_dump()}

    # 2. Check for candidate resume
    cached_resume = state.get("cached_resume", "")
    if not cached_resume:
        cached_resume = resume_read.read_resume()

    resume_text = cached_resume or ""
    resume_file_path = get_resume_file_path()

    # 3. Extract structured candidate profile dict for form mapping
    print("[ApplyAgent] Parsing candidate resume into structured profile for form mapping...")
    user_profile = await extract_user_profile(resume_text)

    results: List[ApplicationResult] = []

    # 4. Launch Playwright browser session
    headless_mode = os.environ.get("HUNTER_HEADLESS", "false").lower() in ("true", "1", "yes")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=headless_mode)
        except Exception:
            # Fallback to headless if display server is unavailable
            browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        # 5. Iterate through filtered jobs
        for job in filtered_jobs:
            job_id = str(job.get("job_id", "job_unknown"))
            company = job.get("company", "Unknown Company")
            role = job.get("role", "Unknown Role")
            url = job.get("url", "")
            if not url:
                scout_jobs = state.get("scout_data", {}).get("jobs", [])
                for sj in scout_jobs:
                    if sj.get("job_id") == job_id:
                        url = sj.get("url", "")
                        break

            ats_platform = detect_ats_platform(url)

            if not url:
                print(f"[ApplyAgent] Job {job_id} has no valid URL. Skipping.")
                results.append(
                    ApplicationResult(
                        job_id=job_id,
                        company=company,
                        role=role,
                        url=url,
                        ats_platform=ats_platform,
                        form_fields_filled=0,
                        status="FAILED",
                        notes="Missing application URL."
                    )
                )
                continue

            try:
                # Normalize Lever URLs: if on a lever.co job page without /apply, target /apply
                if "jobs.lever.co" in url.lower() and not url.lower().endswith("/apply"):
                    url = url.rstrip("/") + "/apply"

                print(f"\n[ApplyAgent] Navigating to {company} — {role} ({url})...")
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)

                # Step 3: DOM extraction
                fields = await extract_form_fields(page)
                is_valid, validation_msg = is_valid_application_form(fields)

                # If no direct form on landing page, look for an 'Apply' button/link to click or follow
                if not is_valid:
                    apply_locators = [
                        'a:has-text("Apply for this job")',
                        'a:has-text("Apply Now")',
                        'a:has-text("Apply for this position")',
                        'a:has-text("Apply")',
                        'button:has-text("Apply for this job")',
                        'button:has-text("Apply Now")',
                        'button:has-text("Apply")'
                    ]
                    found_apply_trigger = False
                    for locator_str in apply_locators:
                        btn = page.locator(locator_str).first
                        try:
                            if await btn.is_visible(timeout=1000):
                                href = await btn.get_attribute("href")
                                if href and (href.startswith("http") or href.startswith("/")):
                                    target_url = href if href.startswith("http") else url.rstrip("/") + href
                                    print(f"[ApplyAgent] Following Apply link: {target_url}")
                                    await page.goto(target_url, timeout=25000, wait_until="domcontentloaded")
                                else:
                                    print(f"[ApplyAgent] Clicking Apply button: {locator_str}")
                                    await btn.click()
                                await page.wait_for_timeout(2000)
                                found_apply_trigger = True
                                break
                        except Exception:
                            continue

                    if found_apply_trigger:
                        fields = await extract_form_fields(page)
                        is_valid, validation_msg = is_valid_application_form(fields)

                if not is_valid:
                    print(f"[ApplyAgent] Form validation: {validation_msg} ({url})")
                    results.append(
                        ApplicationResult(
                            job_id=job_id,
                            company=company,
                            role=role,
                            url=url,
                            ats_platform=ats_platform,
                            form_fields_filled=0,
                            status="FAILED",
                            notes=validation_msg
                        )
                    )
                    continue

                # Step 4: Plan form fill
                fill_plan = await plan_form_fill(fields, user_profile)
                if not fill_plan:
                    print(f"[ApplyAgent] LLM planner found no mappable fields for candidate profile.")
                    results.append(
                        ApplicationResult(
                            job_id=job_id,
                            company=company,
                            role=role,
                            url=url,
                            ats_platform=ats_platform,
                            form_fields_filled=0,
                            status="FAILED",
                            notes="LLM form planner could not map any fields to candidate profile."
                        )
                    )
                    continue

                # Step 5: Execute Playwright form filling
                filled_count = await fill_form(page, fill_plan, resume_file_path)

                # Step 6: Human-In-The-Loop Checkpoint
                auto_decision = state.get("auto_hitl_decision")
                decision = await hitl_checkpoint(job, fill_plan, filled_count, auto_decision=auto_decision)

                # Step 7: Handle decision
                if decision == "SUBMIT":
                    success, screenshot_path, notes = await submit_application(page, job_id)
                    status = "SUBMITTED" if success else "FAILED"
                    results.append(
                        ApplicationResult(
                            job_id=job_id,
                            company=company,
                            role=role,
                            url=url,
                            ats_platform=ats_platform,
                            form_fields_filled=filled_count,
                            status=status,
                            confirmation_screenshot=screenshot_path,
                            notes=notes
                        )
                    )
                elif decision == "SKIP":
                    results.append(
                        ApplicationResult(
                            job_id=job_id,
                            company=company,
                            role=role,
                            url=url,
                            ats_platform=ats_platform,
                            form_fields_filled=filled_count,
                            status="AWAITING_APPROVAL",
                            notes="Application filled but skipped by candidate at HITL checkpoint."
                        )
                    )
                elif decision == "QUIT":
                    results.append(
                        ApplicationResult(
                            job_id=job_id,
                            company=company,
                            role=role,
                            url=url,
                            ats_platform=ats_platform,
                            form_fields_filled=filled_count,
                            status="AWAITING_APPROVAL",
                            notes="Candidate aborted apply session at HITL checkpoint."
                        )
                    )
                    print("[ApplyAgent] Apply session aborted by candidate.")
                    break

            except Exception as e:
                print(f"[ApplyAgent] Error processing {company} — {role}: {e}")
                results.append(
                    ApplicationResult(
                        job_id=job_id,
                        company=company,
                        role=role,
                        url=url,
                        ats_platform=ats_platform,
                        form_fields_filled=0,
                        status="FAILED",
                        notes=f"Error encountered during application: {e}"
                    )
                )

        await browser.close()

    # Step 8: Generate Report & Finalize State
    batch_result = ApplicationBatchResult(
        total_attempted=len(results),
        total_submitted=sum(1 for r in results if r.status == "SUBMITTED"),
        applications=results,
        report_path=None
    )
    report_path = generate_application_report(batch_result)
    batch_result.report_path = report_path

    return {
        "application_data": batch_result.model_dump()
    }
