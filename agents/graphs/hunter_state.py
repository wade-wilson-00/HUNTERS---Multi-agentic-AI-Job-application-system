from typing import TypedDict, Annotated,Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class HunterState(TypedDict):
    """The memory object passed from Node to Node in LangGraph."""

    messages:      Annotated[list[AnyMessage], add_messages]
    summary: str

    #Optional Fields for State variables
    target_role: Optional[str]
    preffered_role: Optional[str]
    active_company: Optional[str]

    intent:        str
    final_response: str
    cached_resume:  str   # Resume text — loaded once, injected into every planner call
