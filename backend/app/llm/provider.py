import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLMProvider:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set."
            )

        self.client = OpenAI(api_key=api_key)

        # CHANGE TO YOUR WANTED MODEL HERE
        self.model = "gpt-5.6-sol"

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        return response.output_text

    def generate_json(self, prompt: str) -> dict:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        return json.loads(response.output_text)