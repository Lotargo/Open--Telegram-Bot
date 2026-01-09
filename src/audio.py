import os
from openai import AsyncOpenAI
from src.config import LLM_CONFIG

class AudioClient:
    def __init__(self):
        provider_config = LLM_CONFIG.get("provider", {})
        # Re-use the same client setup as LLM, or create a new one if needed.
        # Groq's STT endpoint is compatible with OpenAI's interface.
        self.client = AsyncOpenAI(
            base_url=provider_config.get("base_url", "https://api.groq.com/openai/v1"),
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = LLM_CONFIG.get("stt", {}).get("model", "whisper-large-v3-turbo")

    async def transcribe(self, file_path):
        """
        Transcribes audio file at file_path using Groq's Whisper API.
        """
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.model,
                    response_format="json"  # or verbose_json, text
                )
            return transcription.text
        except Exception as e:
            print(f"STT Error: {e}")
            return None
