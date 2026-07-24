import os
from dotenv import load_dotenv
from config.settings import LLM_MODEL
from agents.graphs.hunter_graph import build_hunter_graph
from langchain_core.messages import HumanMessage
from context.context_builder import HUNTER_FULL_CONTEXT

load_dotenv()

class HunterAgent:
    def __init__(self, model_id=None):
        self.model_id = model_id or LLM_MODEL
        print(f"Hunter is Getting Ready...")
        # chat_history is a lightweight conversation log (user/assistant turns only).
        # The full 5-layer context is injected by the Planner Node via HUNTER_FULL_CONTEXT.
        self.chat_history = []
        print(f"Hunter is ready.")
        print(f" Profile: {len(HUNTER_FULL_CONTEXT)} chars loaded into context.")

    def respond(self, text: str) -> str:
        """Generate a complete response (blocking). Used in legacy mode."""
        self.chat_history.append({"role": "user", "content": text})
        
        try:
            # Sync calls not supported on AsyncOpenAI, but we'll adapt since this is legacy mode
            raise NotImplementedError("Blocking respond() not supported with AsyncOpenAI client. Use respond_stream().")
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, sir. I encountered an error connecting to my server."

    async def respond_stream(self, text: str):
        """
        Asynchronous generator that yields tokens as they arrive from the LLM.
        Uses HuggingFace AsyncInferenceClient with stream=True (SSE streaming).
        
        Usage:
            async for token in hunter.respond_stream("Find AI internships"):
                print(token, end="", flush=True)
        """

        graph = await build_hunter_graph()

        # Convert chat history to LangChain messages for graph memory
        from langchain_core.messages import AIMessage
        history_messages = []
        for entry in self.chat_history:
            if entry["role"] == "user":
                history_messages.append(HumanMessage(content=entry["content"]))
            elif entry["role"] == "assistant":
                history_messages.append(AIMessage(content=entry["content"]))

        # Add the current user message to history BEFORE invoking
        self.chat_history.append({"role": "user", "content": text})
        history_messages.append(HumanMessage(content=text))

        try:
            print(f"Hunter is thinking....")
            final_state = await graph.ainvoke({
                "messages": history_messages  # Full conversation history
            })

            final_text = final_state["final_response"]

            self.chat_history.append({
                "role": "assistant",
                "content": final_text
            })

            # Yield the final text back to the voice server
            yield final_text

        except Exception as e:
            print(f"\nError in graph execution: {e}")
            yield "I'm sorry, sir. It seems I've hit a snag. Please try again."

    def clear_history(self):
        """Reset conversation history (user/assistant turns only)."""
        self.chat_history = []


if __name__ == "__main__":
    agent = HunterAgent()
    # Test streaming
    print("Testing streaming mode:")
    for token in agent.respond_stream("Hello, who are you?"):
        print(token, end="", flush=True)
    print()

