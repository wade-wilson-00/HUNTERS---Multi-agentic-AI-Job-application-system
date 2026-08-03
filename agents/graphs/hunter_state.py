from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class HunterState(TypedDict):
    """The memory object passed from Node to Node in LangGraph."""

    messages:      Annotated[list[BaseMessage], add_messages]
    intent:        str
    final_response: str
    cached_resume:  str   # Resume text — loaded once, injected into every planner call