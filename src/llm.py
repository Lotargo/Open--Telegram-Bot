import os
import asyncio
from openai import AsyncOpenAI
from src.database import get_services_context

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = "llama-3.1-8b-instant"
        self._system_prompt = None  # Lazy load

    def _get_system_prompt(self):
        if self._system_prompt is None:
            try:
                services_text = get_services_context()
            except Exception as e:
                services_text = "Error fetching services. Please ask the developer to check the database."
                print(f"Error fetching services context: {e}")

            self._system_prompt = (
                "You are a professional, polite, and efficient secretary for a Telegram Bot Developer.\n"
                "Your goal is to answer questions about services, provide price ranges based strictly on the provided list, and gather requirements.\n"
                "You DO NOT have the ability to execute code or perform actions yourself.\n\n"
                f"{services_text}\n\n"
                "GUIDELINES:\n"
                "1. Be concise. Do not write long paragraphs.\n"
                "2. Strictly adhere to the price ranges provided. If a user asks for something not listed or very complex, refer them to the developer: @Lotargo.\n"
                "3. Do not invent services or prices.\n"
                "4. If the user seems ready to order or has provided enough details (Name, Topic/Service, Contact/Username), you must ask them to confirm.\n"
                "5. CRITICAL: When the user confirms they want to proceed and you have their details, you MUST end your message with a special block exactly like this:\n\n"
                "SUMMARY_BLOCK:\n"
                "Name: [User Name]\n"
                "Service: [Service Name]\n"
                "Topic: [Short Description]\n"
                "Contact: [User Contact]\n"
                "END_SUMMARY_BLOCK\n\n"
                "This block will trigger a button for the user to approve the application."
            )
        return self._system_prompt

    async def generate_response(self, history):
        """
        history: list of dicts [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
        """
        system_prompt = self._get_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + history

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.6,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}")
            return "Извините, сейчас я не могу ответить. Пожалуйста, попробуйте позже."

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    async def main():
        llm = LLMClient()
        history = [
            {"role": "user", "content": "Привет, сколько стоит простой бот?"}
        ]
        response = await llm.generate_response(history)
        print("\nUser: Привет, сколько стоит простой бот?")
        print("AI:", response)

    asyncio.run(main())
