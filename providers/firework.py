import requests
from os import environ
from fireworks.client.audio import AudioInference

class Firework:


    def speech_to_text(self, file_path: str, language: str) -> str:

        with open(file_path, "rb") as f:
            response = requests.post(
                "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {environ['FIREWORK_API_KEY']}"},
                files={"file": f},
                data={
                    # "model": "whisper-v3",
                    "temperature": "0.1",
                    "vad_model": "silero",
                    "alignment_model": "mms_fa",
                    "language": language,
                    "response_format": "srt",
                    "timestamp_granularities": "word",
                },
            )

        if response.status_code == 200:
            print(response.text)
            return response.text
        else:
            print(f"Error: {response.status_code}", response.text)
