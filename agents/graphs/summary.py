from agents.graphs.hunter_state import HunterState
from agents.graphs.groq_llm import chat_llm
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

async def summary_node(state: HunterState) -> dict:

    prev_ai_message = None

    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            prev_ai_message = msg
            break

    if not prev_ai_message:
        return{
            "final_response": "I'm Sorry, I couldn't complete the task."
        }
    
    voice_prompt = [
        SystemMessage(content = (
            "You are Hunter, a J.A.R.V.I.S. style AI assistant. "
            "Convert the following content into natural spoken language. "
            "No markdown, no bullet points, no asterisks. "
            "Write as if you are speaking directly to the user."
        )),
        HumanMessage(content = prev_ai_message.content)
    ]
    voice_response = await chat_llm.ainvoke(voice_prompt)

    return {
        "final_response": voice_response.content
    }