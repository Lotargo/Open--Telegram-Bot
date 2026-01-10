import os
from openai import AsyncOpenAI
from src.config import LLM_CONFIG
from pydub import AudioSegment
import edge_tts

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
        self.tts_voice = "ru-RU-SvetlanaNeural"

    async def text_to_speech(self, text, output_filename):
        """
        Converts text to speech using Edge-TTS and saves it to output_filename.
        Returns the path to the file to send (can be .ogg).
        """
        try:
            # Edge-TTS output is typically MP3
            temp_mp3 = output_filename + ".mp3"

            communicate = edge_tts.Communicate(text, self.tts_voice)
            await communicate.save(temp_mp3)

            # Convert mp3 to ogg (opus) for Telegram voice message compatibility
            final_path = output_filename
            if not final_path.endswith(".ogg"):
                final_path += ".ogg"

            audio = AudioSegment.from_mp3(temp_mp3)
            audio.export(final_path, format="ogg", codec="libopus")

            # Clean up temp mp3
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)

            return final_path
        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    async def transcribe(self, file_path):
        """
        Transcribes audio file at file_path using Groq's Whisper API.
        Automatically converts .oga (Telegram voice) to .wav before sending.
        """
        if not os.path.exists(file_path):
            return None

        converted_path = None

        # Check if conversion is needed (Groq doesn't like .oga)
        if file_path.endswith('.oga') or file_path.endswith('.ogg'):
            try:
                converted_path = file_path.rsplit('.', 1)[0] + ".wav"
                # Load audio using pydub (requires ffmpeg installed in system)
                audio = AudioSegment.from_file(file_path)
                audio.export(converted_path, format="wav")
                file_to_send = converted_path
            except Exception as e:
                print(f"Audio Conversion Error: {e}")
                # Fallback to original file if conversion fails (might still fail at API)
                file_to_send = file_path
        else:
            file_to_send = file_path

        try:
            with open(file_to_send, "rb") as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.model,
                    response_format="json"
                )
            return transcription.text
        except Exception as e:
            print(f"STT Error: {e}")
            return None
        finally:
            # Cleanup converted file
            if converted_path and os.path.exists(converted_path):
                os.remove(converted_path)
