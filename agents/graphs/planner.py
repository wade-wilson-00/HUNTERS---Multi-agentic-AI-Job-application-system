import sys
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.graphs.hunter_state import HunterState
from agents.graphs.groq_llm import chat_llm
from context.context_builder import HUNTER_FULL_CONTEXT

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

    # Prepend the full 5-layer context as the system message on every invocation.
    # This ensures Hunter always has the user profile, tool manifest, and operating
    # rules loaded, regardless of conversation history length.
    
    messages_with_context = [SystemMessage(content=HUNTER_FULL_CONTEXT)] + list(state["messages"])

    response = await llm_with_tools.ainvoke(messages_with_context)

    return {"messages": [response]}

