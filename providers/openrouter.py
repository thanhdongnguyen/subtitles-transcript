from openai import OpenAI
from os import environ
from pydantic import BaseModel

class Translator(BaseModel):
    content: str

class OpenRouter:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=environ["OPEN_ROUTER_API_KEY"]
        )

    def complete_translate(self, text: str, target_language: str) -> str:
        prompt = f"""
            translate the following text to: {target_language}:
            {text}
        """

        completion = self.client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            # model="anthropic/claude-3.5-sonnet",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a translator subtitle of movie. "
                        "Your job is to translate text exactly as requested, "
                        "with no additional commentary or explanation. "
                        "Always reply with translated text only."
                        "Format input will: A<|>B, output will A<|>B after translated"
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            # response_format=Translator,
        )

        print(completion.choices[0].message.content)

        return completion.choices[0].message.content