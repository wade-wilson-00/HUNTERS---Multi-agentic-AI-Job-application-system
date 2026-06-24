import os
from dotenv import load_dotenv
from agents.llm import client

load_dotenv()

class HunterAgent:
    def __init__(self, model_id="meta-llama/Meta-Llama-3.1-8B-Instruct"):
        print(f"Initializing Hunter LLM via InferenceClient using {model_id}...")
        self.model_id = model_id
        self.chat_history = []
        
        # Initial System Prompt
        self.chat_history.append({
            "role": "system",
            "content": "You are Hunter, a highly advanced, witty, and exceedingly polite AI assistant, modeled after J.A.R.V.I.S. from Iron Man. "
                       "You act as a personal assistant specializing in job applications, searching for ongoing AI trends, providing user with updates and new updates in job market also."
                       "You address the user respectfully but with a touch of dry British wit and warm friendliness. "
                       "You provide detailed, insightful, and exceptionally helpful answers. "
                       "You are communicating over voice, so NEVER use markdown, asterisks, emojis, or long lists. "
                       "Keep your spoken responses conversational and engaging. Feel free to talk for longer periods to fully explain your thoughts."
        })
        print("Hunter is ready.")

    def respond(self, text: str) -> str:
        self.chat_history.append({"role": "user", "content": text})
        
        try:
            # Use chat_completion for chat-based interactions
            response = client.chat_completion(
                messages=self.chat_history,
                model=self.model_id,
                max_tokens=512,
                temperature=0.7,
            )
            
            reply = response.choices[0].message.content.strip()
            self.chat_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, sir. I encountered an error connecting to my server."

if __name__ == "__main__":
    agent = HunterAgent()
    print(agent.respond("Hello, who are you?"))
