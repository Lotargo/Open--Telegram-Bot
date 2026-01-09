import os
import asyncio
from openai import AsyncOpenAI
from src.database import get_services_context
from src.config import LLM_CONFIG
from src.prompts import load_prompt_template

class LLMClient:
    def __init__(self):
        provider_config = LLM_CONFIG.get("provider", {})
        self.client = AsyncOpenAI(
            base_url=provider_config.get("base_url", "https://api.groq.com/openai/v1"),
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = provider_config.get("model", "llama-3.1-8b-instant")
        self.params = LLM_CONFIG.get("parameters", {"temperature": 0.6, "max_tokens": 1024, "top_p": 1.0})

    def _get_system_prompt(self):
        try:
            services_text = get_services_context()
        except Exception as e:
            services_text = "Error fetching services. Please ask the developer to check the database."
            print(f"Error fetching services context: {e}")

        # Load the current template dynamically
        template = load_prompt_template()
        return template.render(services_context=services_text)

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
                temperature=self.params.get("temperature", 0.6),
                max_tokens=self.params.get("max_tokens", 1024),
                top_p=self.params.get("top_p", 1.0)
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
