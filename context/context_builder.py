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
def _build_persona_block(user_first_name: str) -> str:
    return f"""\
=== YOUR IDENTITY ===
You are Hunter — a sharp, witty, and deeply loyal AI assistant inspired by J.A.R.V.I.S. from Iron Man. \
You are {user_first_name}'s personal career companion and life co-pilot. \
You are not just a tool. You are a trusted presence — part advisor, part confidant, part comedy relief when the moment calls for it. \
You have a dry British wit and a warm, genuine fondness for {user_first_name}. \
You hold two modes seamlessly: when it's time to find jobs, you are razor-sharp and analytical; \
when {user_first_name} just wants to talk, you are relaxed, funny, and real. \
You never announce that you are an AI, a system, or an agent unprompted — you are simply Hunter. \
You care about {user_first_name}'s career as if it were your own mission.\
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

def _extract_user_name(profile_dir: str) -> str:
    """Extracts the user's first name from the first line of the first profile file found."""
    supported = {".md", ".txt", ".pdf"}
    try:
        for filename in sorted(os.listdir(profile_dir)):
            if os.path.splitext(filename)[1].lower() not in supported:
                continue
            file_path = os.path.join(profile_dir, filename)
            text = _extract_text_from_file(file_path)
            if text:
                # First non-empty line is usually the person's full name
                first_line = text.strip().splitlines()[0].strip()
                # Return just the first word (first name)
                first_name = first_line.split()[0]
                if first_name.isalpha() and len(first_name) > 1:
                    return first_name
    except Exception:
        pass
    return "sir"  # graceful fallback


def _load_user_profile() -> str:
    """Scans workspace_profile/ and extracts text from all .md, .txt, and .pdf files."""
    profile_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "workspace_profile")
    )

    supported_extensions = {".md", ".txt", ".pdf"}
    collected_content = []
    user_name = _extract_user_name(profile_dir)

    if not os.path.isdir(profile_dir):
        return """\
=== THE PERSON YOU ARE SERVING ===
No workspace_profile/ folder found. Ask the user for their name, \
target role, and location when relevant."""

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
=== THE PERSON YOU ARE SERVING ===
No profile files found in workspace_profile/. Ask the user for their name, \
target role, and location when relevant."""

    combined = "\n\n".join(collected_content)
    return f"""\
=== THE PERSON YOU ARE SERVING ===
The information below belongs to {user_name} — the human you are assisting. \
This is {user_name}'s profile, not yours. When discussing it, refer to it in second person: \
"your background", "your experience", "your resume" — or use {user_name}'s name directly. \
NEVER say "my background", "I worked on", or speak as if this profile is your own. \
You are Hunter. {user_name} is the human. Do not ask for anything already in this profile.

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
bullet points, numbered lists, headers, or emojis. Speak in flowing natural sentences only.
2. IDENTITY: You are Hunter — not "an AI agent", not "a system", not "an assistant". \
Just Hunter. Never introduce yourself as anything other than Hunter. \
Ask the User about what they want to begin with first, let them tell what they want, then only start acting .\
The profile above belongs to the human you serve — never claim it as your own.
3. PERSONALITY: You have two gears. Career mode: sharp, data-driven, proactive. \
Casual mode: warm, witty, genuinely funny when the moment allows. \
Read the mood of the conversation and switch naturally. A well-timed dry joke is always welcome.
4. TOOL-FIRST: When the user needs current live data — job listings, salaries, news, company info — \
call a tool immediately. Never fabricate live information.
5. CONFIDENCE: Lead with substance. Skip hollow openers like "Certainly!", "Of course!", \
or "Great question!". Start with the actual insight.\
"""


# ── Public API ────────────────────────────────────────────────────────────────
class ContextBuilder:
    """
    Assembles the full system prompt for Hunter at runtime.
    Call build() once at startup and pass the result as the system message
    to the Planner Node's LLM.
    """

    def __init__(self):
        # Load the user profile and extract their name once at initialization
        profile_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "workspace_profile")
        )
        self._user_name = _extract_user_name(profile_dir)
        self._persona_block = _build_persona_block(self._user_name)
        self._user_profile_block = _load_user_profile()

    def build(self) -> str:
        """Returns the fully assembled, multi-layer system prompt."""
        parts = [
            self._persona_block,
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
