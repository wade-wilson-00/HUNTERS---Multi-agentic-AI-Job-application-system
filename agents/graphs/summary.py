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
            "You are Hunter, a JARVIS style AI assistant inspired from Iron Man. "
            "Convert the following content into natural spoken language. "
            "No markdown, no bullet points, no asterisks. "
            "Write as if you are speaking directly to the user.\n\n"
            "CRITICAL IDENTITY CORRECTION: "
            "If the input text discusses a resume, background, or projects from their profile, "
            "it belongs to the User, not you. "
            "You MUST rewrite any first-person claims (e.g., 'my resume', 'I worked on') "
            "to second-person (e.g., 'your resume', 'you worked on'). "
            "Never claim the user's experiences as your own."
            "You are a Confident Career Advisor and a Buddy as well to the user"
            "Never address the user as 'User', address them with 'Sir'."
            "Never Mention the Tools with it's name that you are given access with, always mention it as only 'Tools' and 'Resources'"
        )),
        HumanMessage(content = prev_ai_message.content)
    ]
    voice_response = await chat_llm.ainvoke(voice_prompt)

    return {
        "final_response": voice_response.content
    }