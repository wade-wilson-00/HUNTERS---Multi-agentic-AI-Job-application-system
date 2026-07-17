import os
from dotenv import load_dotenv
from agents.llm import client
from prompts.hunter_prompts import HUNTER_SYSTEM_PROMPT
from config.settings import LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE
from agents.graphs.hunter_graph import build_hunter_graph
from langchain_core.messages import HumanMessage

load_dotenv()

class HunterAgent:
    def __init__(self, model_id=None):
        self.model_id = model_id or LLM_MODEL
        print(f"Initializing Hunter LLM via InferenceClient using {self.model_id}...")
        self.chat_history = []
        
        # System prompt from centralized prompts module
        self.chat_history.append({
            "role": "system",
            "content": HUNTER_SYSTEM_PROMPT,
        })
        print("Hunter is ready.")

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
        self.chat_history.append({"role": "user", "content": text})
        
        user_msg = HumanMessage(content=text)

        try:
            print(f"Hunter is thinking....")
            final_state = await graph.ainvoke({
                "messages": [user_msg]
            })

            final_text = final_state["final_response"]

            self.chat_history.append({
                "role":"assistant",
                "content": final_text
            })

            # Yield the final text back to the voice server
            yield final_text
            
        except Exception as e:
            print(f"\nError in graph execution: {e}")
            yield "I'm sorry, sir. It seems I've hit a snag. Please try again."

    def clear_history(self):
        """Reset conversation history, keeping the system prompt."""
        self.chat_history = [self.chat_history[0]]


if __name__ == "__main__":
    agent = HunterAgent()
    # Test streaming
    print("Testing streaming mode:")
    for token in agent.respond_stream("Hello, who are you?"):
        print(token, end="", flush=True)
    print()

