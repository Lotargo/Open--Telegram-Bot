import os
from openai import AsyncOpenAI
from src.config import LLM_CONFIG
from pydub import AudioSegment
import edge_tts
import re
import emoji

def clean_markdown_for_tts(text: str) -> str:
    """
    Removes Markdown formatting and Emojis from text for cleaner TTS output.
    Keeps only the human-readable content.
    """
    if not text:
        return ""

    # Remove Emojis
    text = emoji.replace_emoji(text, replace='')

    # Remove bold/italic (**text**, *text*, __text__, _text_)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove code blocks (```code```) and inline code (`code`)
    text = re.sub(r'```[\s\S]*?```', '', text) # Remove code blocks entirely or keep content? usually best to remove or simplify
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove headers (# Header)
    text = re.sub(r'#+\s?', '', text)

    # Remove lists markers (-, *, 1.)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    return text.strip()

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

    async def text_to_speech(self, text, output_filename, mood="professional"):
        """
        Converts text to speech using Edge-TTS and saves it to output_filename.
        Returns the path to the file to send (can be .ogg).

        mood: affects rate and pitch
          - enthusiastic: rate=+10%, pitch=+5Hz
          - cynical/professional: rate=-5%, pitch=-2Hz
          - default: no change
        """
        try:
            # Clean text before sending to TTS
            clean_text = clean_markdown_for_tts(text)
            if not clean_text:
                return None

            # Edge-TTS output is typically MP3
            temp_mp3 = output_filename + ".mp3"

            # Determine prosody options based on mood
            rate = "+0%"
            pitch = "+0Hz"

            if mood == "enthusiastic":
                rate = "+10%"
                pitch = "+5Hz"
            elif mood in ["cynical", "professional"]:
                rate = "-5%"
                pitch = "-2Hz"

            communicate = edge_tts.Communicate(clean_text, self.tts_voice, rate=rate, pitch=pitch)
            await communicate.save(temp_mp3)

            # Convert mp3 to ogg (opus) for Telegram voice message compatibility
            final_path = output_filename
            if not final_path.endswith(".ogg"):
                final_path += ".ogg"

            # Run blocking audio conversion in a separate thread
            import asyncio
            def _convert():
                audio = AudioSegment.from_mp3(temp_mp3)
                audio.export(final_path, format="ogg", codec="libopus")

            await asyncio.to_thread(_convert)

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
