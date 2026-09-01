from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class HunterState(TypedDict):
    """
    The unified state object passed across all nodes in the Hunter LangGraph.

    Sections:
      - Core Chat:       Message history for planner reasoning.
      - Routing Control:  Supervisor decides which sub-agent runs next.
      - Inter-Agent Bus:  Typed dict slots where each sub-agent writes its output.
                          Downstream agents read upstream outputs from here.
      - Output & Caches: Final voice response and resume cache.
    """

    # ── Core Chat History (pruned dynamically) ────────────────────────────────
    messages: Annotated[list[AnyMessage], add_messages]
    summary: str

    # ── Routing Control (set by Planner, read by conditional edge) ────────────
    next_agent: Optional[str]           # "scout" | "match" | "apply" | "tracker" | "market" | "outreach" | "summary"
    task_instructions: Optional[str]    # Detailed goal the Planner passes to the next sub-agent

    # ── Inter-Agent Data Bus (sub-agents write here, others read) ─────────────
    scout_data: Optional[dict]          # ScoutResult.model_dump()
    match_data: Optional[dict]          # MatchResult.model_dump()
    application_data: Optional[dict]    # ApplicationResult.model_dump()
    tracker_data: Optional[dict]        # TrackerResult.model_dump()
    market_data: Optional[dict]         # MarketAnalysisResult.model_dump()
    outreach_data: Optional[dict]       # OutreachResult.model_dump()

    # ── Domain State (carried across turns) ───────────────────────────────────
    target_role: Optional[str]
    preffered_role: Optional[str]
    active_company: Optional[str]

    # ── Output & Persistence Caches ───────────────────────────────────────────
    intent: str
    final_response: str
    cached_resume: str                  # Resume text — loaded once, injected into every planner call

