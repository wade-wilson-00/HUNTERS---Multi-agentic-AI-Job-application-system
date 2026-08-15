import os
from dotenv import load_dotenv
from config.settings import LLM_MODEL
from agents.graphs.hunter_graph import build_hunter_graph, DB_PATH
from langchain_core.messages import HumanMessage
from context.context_builder import HUNTER_FULL_CONTEXT
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

load_dotenv()

class HunterAgent:
    def __init__(self, model_id=None, session_id="default_session"):
        self.model_id = model_id or LLM_MODEL
        self.session_id = session_id
        self._graph = None
        self._checkpointer_cm = None
        print(f"Hunter is Getting Ready...")
        print(f"Hunter is ready.")
        print(f" Profile: {len(HUNTER_FULL_CONTEXT)} chars loaded into context.")

    async def _get_graph(self):
        if self._graph is None:
            self._checkpointer_cm = AsyncSqliteSaver.from_conn_string(DB_PATH)
            checkpointer = await self._checkpointer_cm.__aenter__()
            self._graph = await build_hunter_graph(checkpointer=checkpointer)
        return self._graph

    def respond(self, text: str) -> str:
        """Generate a complete response (blocking). Used in legacy mode."""
        try:
            raise NotImplementedError("Blocking respond() not supported with AsyncOpenAI client. Use respond_stream().")
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, sir. I encountered an error connecting to my server."

    async def respond_stream(self, text: str):
        """
        Asynchronous generator that yields tokens as they arrive from the LLM.
        Passes input to the LangGraph engine with persistent SQLite checkpointing.
        """
        graph = await self._get_graph()
        config = {
            "configurable": {"thread_id": self.session_id},
            "recursion_limit": 6
        }
        user_msg = HumanMessage(content=text)

        try:
            print(f"Hunter is thinking....")
            final_state = await graph.ainvoke(
                {"messages": [user_msg]},
                config=config
            )

            final_text = final_state.get("final_response", "")

            # Yield the final text back to the voice server / CLI
            yield final_text

        except Exception as e:
            print(f"\nError in graph execution: {e}")
            yield "I'm sorry, sir. It seems I've hit a snag. Please try again."

    def clear_history(self):
        """Reset session ID for clean history if needed."""
        import uuid
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"


if __name__ == "__main__":
    import asyncio
    async def main():
        agent = HunterAgent()
        print("Testing streaming mode:")
        async for token in agent.respond_stream("Hello, who are you?"):
            print(token, end="", flush=True)
        print()
    asyncio.run(main())
