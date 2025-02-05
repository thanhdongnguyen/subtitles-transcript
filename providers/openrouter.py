from openai import AsyncOpenAI
from os import environ
from loguru import logger

class OpenRouter:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=environ["OPEN_ROUTER_API_KEY"]
        )
        self.model = "google/gemini-flash-1.5-8b"

    async def complete_translate(self, text: str, origin_lang: str, target_language: str, model: str = "") -> str:
        prompt = f"Translate this from origin_lang: {origin_lang} to {target_language}: {text}"
        system = """
                    You are an experienced semantic translator, specialized in creating SRT files. Separate translation segments with the '<<<>>>' symbol.
                    Note: 
                        - Only return translated text
                    """
        translated_text, total_token = await self.call_provider(prompt=prompt, system_prompt=system, model=model)

        return translated_text

    async def complete_translate_segment(self, chunk: str = "", text: str = "", origin_lang: str = "", target_lang: str = "") -> str:
        prompt = f"""
        You are an experienced semantic translator, specialized in creating SRT files. 
        Note: 
            - Only return translated text
        This is text original of {origin_lang} language: 
        {chunk}
        
    
        Translate this segment from {origin_lang} to {target_lang}: {text}
        """

        translated_text = await self.call_provider(prompt=prompt, model="google/gemini-flash-1.5")

        return translated_text

    async def call_provider(self, model: str = "", prompt: str = "", system_prompt: str = "") -> str:
        messages = []
        if system_prompt != "":
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })


        model = self.model if model == "" else model
        print(f"model: {model}")
        completion = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            top_p=0,
        )

        logger.info(f"model: {model}, completion: {completion}\n")
        return completion.choices[0].message.content

