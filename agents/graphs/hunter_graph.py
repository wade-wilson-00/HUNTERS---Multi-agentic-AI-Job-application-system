from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agents.graphs.hunter_state import HunterState
from agents.graphs.planner import make_planner_node
from agents.graphs.summary import summary_node
from langchain_mcp_adapters.client import MultiServerMCPClient
import sys
import os

DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".data", "hunter_state.db")
)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

async def build_hunter_graph(checkpointer=None):
    # Fetching Tools from MCP Server
    client = MultiServerMCPClient({
        "hunters_tools": {
            "command": sys.executable,
            "args": ["-m", "mcp_server.central_server"],
            "transport": "stdio",
        }
    })
    tools = await client.get_tools()

    # Initializing Graph with State
    workflow = StateGraph(HunterState)

    # Build planner node with the shared tool list — no second MCP subprocess
    planner_node = make_planner_node(tools)

    # Adding Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("summary", summary_node)

    # Defining the Execution flow using defined Nodes
    workflow.add_edge(START, "planner")

    # Defining Conditional Edging routes
    workflow.add_conditional_edges(
        "planner",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "summary"
        }
    )
    workflow.add_edge("tools", "planner")

    # After Summary Ends, the Graph flow is completed here
    workflow.add_edge("summary", END)
    
    return workflow.compile(checkpointer=checkpointer)



