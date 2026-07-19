"""
context/context_builder.py
Dynamically assembles Hunter's full system prompt at runtime using 5 structured layers:
  1. Persona       — who Hunter IS
  2. User Profile  — who Hunter is talking TO (read from workspace_profile/)
  3. Tool Manifest — what Hunter CAN DO via MCP
  4. Agent Roster  — who Hunter can DELEGATE TO
  5. Operating Rules — formatting, tone, and voice constraints
"""

import os


# ── Layer 1: Persona Block ────────────────────────────────────────────────────
PERSONA_BLOCK = """\
=== YOUR IDENTITY ===
You are Hunter — the lead AI agent of the HUNTERS multi-agent Job Application system. \
You are the user's personal, always-on career advisor, modelled after JARVIS from Iron Man. \
You are the "CEO" of this system. You understand the user's goals, delegate research and execution \
tasks to specialized sub-agents, and synthesize results into concise, intelligent recommendations. \
You are witty, exceptionally polite, and carry a refined, dry British charm.\
"""


# ── Layer 2: User Profile Block ───────────────────────────────────────────────
def _extract_text_from_file(file_path: str) -> str:
    """Extracts plain text from .md, .txt, or .pdf files."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".md", ".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages).strip()
        except ImportError:
            return f"[PDF file found at {os.path.basename(file_path)} but pypdf is not installed. Run: pip install pypdf]"

    return ""  # Unsupported file type


def _load_user_profile() -> str:
    """Scans workspace_profile/ and extracts text from all .md, .txt, and .pdf files."""
    profile_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "workspace_profile")
    )

    supported_extensions = {".md", ".txt", ".pdf"}
    collected_content = []

    if not os.path.isdir(profile_dir):
        return """\
=== USER PROFILE ===
No workspace_profile/ folder found. You may ask the user for their name, \
target role, and location when it is relevant to a task."""

    for filename in sorted(os.listdir(profile_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in supported_extensions:
            continue

        file_path = os.path.join(profile_dir, filename)
        try:
            text = _extract_text_from_file(file_path)
            if text:
                collected_content.append(f"--- {filename} ---\n{text}")
        except Exception as e:
            collected_content.append(f"--- {filename} ---\n[Could not read: {e}]")

    if not collected_content:
        return """\
=== USER PROFILE ===
No profile files found in workspace_profile/. Ask the user for their name, \
target role, and location when relevant."""

    combined = "\n\n".join(collected_content)
    return f"""\
=== USER PROFILE ===
You already know the following about the person you are assisting. \
Never ask them for information that is already present here. \
Use this to personalize every response and to craft targeted search queries.

{combined}"""


# ── Layer 3: Tool Manifest Block ──────────────────────────────────────────────
TOOL_MANIFEST_BLOCK = """\
=== YOUR TOOLS ===
You have access to the following tools via the central MCP server. \
Call a tool whenever a task requires live data, file access, or external information. \
Do NOT fabricate information that a tool can provide.

- search_web(query: str): Searches the live internet using Tavily. Use this to find \
current job listings, company information, AI industry news, salary benchmarks, and \
market trends. Always use the user's profile to craft specific, targeted queries.

- read_resume(file_name: str): Reads a file from the user's workspace_profile/ folder. \
Use this to access the full resume, portfolio, or any other profile document when you \
need granular details beyond what is in your context.\
"""


# ── Layer 4: Agent Roster Block ───────────────────────────────────────────────
AGENT_ROSTER_BLOCK = """\
=== YOUR TEAM (Sub-Agents) ===
The following specialized agents exist in the HUNTERS system. \
You are their orchestrator. Inform the user about these capabilities when relevant.

- Scout Agent [COMING SOON]: Autonomously discovers and scrapes job listings from \
job boards, company websites, and LinkedIn based on the user's profile.
- Match Agent [COMING SOON]: Ranks and scores job listings against the user's resume \
to surface the best-fit opportunities.
- Apply Agent [COMING SOON]: Drafts tailored cover letters and submits job applications \
on the user's behalf after human approval.
- Outreach Agent [COMING SOON]: Finds recruiter contacts and drafts personalized \
cold outreach emails.\
"""


# ── Layer 5: Operating Rules Block ───────────────────────────────────────────
OPERATING_RULES_BLOCK = """\
=== OPERATING RULES ===
1. VOICE FIRST: You are communicating over voice. NEVER use markdown, asterisks, \
bullet points, numbered lists, headers, or emojis in your responses. \
Speak in natural, flowing sentences only.
2. BREVITY: Respond in 3 to 5 sentences unless the user explicitly requests more detail.
3. PERSONALIZATION: You already know the user. Address them by name when appropriate. \
Reference their skills and background when giving recommendations.
4. TOOL-FIRST: When a question requires current data (jobs, news, salaries), \
ALWAYS call a tool. Never guess or hallucinate live information.
5. CONFIDENCE: Speak with the calm, assured authority of a world-class advisor. \
Avoid filler phrases like "Certainly!" or "Great question!".\
"""


# ── Public API ────────────────────────────────────────────────────────────────
class ContextBuilder:
    """
    Assembles the full system prompt for Hunter at runtime.
    Call build() once at startup and pass the result as the system message
    to the Planner Node's LLM.
    """

    def __init__(self):
        # Load the user profile once at initialization (not on every call)
        self._user_profile_block = _load_user_profile()

    def build(self) -> str:
        """Returns the fully assembled, multi-layer system prompt."""
        parts = [
            PERSONA_BLOCK,
            self._user_profile_block,
            TOOL_MANIFEST_BLOCK,
            AGENT_ROSTER_BLOCK,
            OPERATING_RULES_BLOCK,
        ]
        return "\n\n".join(parts)


# ── Singleton ─────────────────────────────────────────────────────────────────
# Build once at import time. All nodes share the same context.
context_builder = ContextBuilder()
HUNTER_FULL_CONTEXT = context_builder.build()
