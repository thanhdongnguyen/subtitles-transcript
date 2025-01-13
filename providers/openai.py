from openai import OpenAI
from os import environ

class OAI:
    def __init__(self):
        self.client = OpenAI()

    def transcription(self, audio_url: str) -> str:
        audio_file = open(audio_url, "rb")
        trans = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="srt",
            language="en"
        )

        return trans