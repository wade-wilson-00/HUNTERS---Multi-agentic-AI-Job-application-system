from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.graphs.hunter_state import HunterState
from hunter_state import HunterState
from groq_llm import chat_llm
import sys
 
async def planner_node(state: HunterState):

    client = MultiServerMCPClient({
        "hunter_tools": {
            "command": sys.executable,
            "args": ["-m","mcp_server.central_server"],
            "transport":"stdio",
        }
    })

    tools = await client.get_tools()

    llm_with_tools = chat_llm.bind_tools(tools)
    response = await llm_with_tools.ainvoke(state["messages"])

    return {"messages": [response]} 