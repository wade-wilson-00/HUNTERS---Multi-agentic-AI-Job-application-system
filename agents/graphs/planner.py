import sys
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.graphs.hunter_state import HunterState
from agents.graphs.groq_llm import chat_llm

async def planner_node(state: HunterState):

    client = MultiServerMCPClient({
        "hunters_tools": {
        "command": sys.executable,
        "args": ["-m", "mcp_server.central_server"],
        "transport": "stdio",
    }
    })
    tools = await client.get_tools()

    llm_with_tools = chat_llm.bind_tools(tools)
    response = await llm_with_tools.ainvoke(state["messages"])

    return {"messages": [response]}

