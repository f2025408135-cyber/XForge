import json
import os
import httpx
from openai import AsyncOpenAI
# Pydantic 2.x migration makes openapi_schema_pydantic tricky sometimes,
# we use standard dict parsing for safety in the Brain if needed.

class TheoristAgent:
    """
    Analyzes API definitions to hypothesize multi-user stateful attacks (BOLA, Logic Flaws)
    and constructs Task payloads for the Executor.
    """
    def __init__(self):
        # Uses standard environment variable for API key
        self.llm_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy_key"))

    async def fetch_spec(self, url: str) -> dict:
        """Fetches the OpenAPI JSON spec from a target."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

    async def generate_hypotheses(self, spec: dict, attack_type: str, max_workflows: int = 5) -> list:
        """
        Feeds the spec to the LLM and requests `max_workflows` payloads formatted to the Task schema.
        """
        system_prompt = f"""
You are an expert security researcher. You are given a truncated OpenAPI JSON specification.
Your goal is to generate JSON workflows for a fuzzer to test for {attack_type} vulnerabilities.

Return ONLY valid JSON matching this schema structure exactly:
{{
  "workflows": [
    {{
      "attack_type": "{attack_type}",
      "payloads": [
        {{ "method": "POST", "path": "/api/resource", "headers": {{"Authorization": "Bearer admin"}}, "body": "{{\\"name\\":\\"test\\"}}" }},
        {{ "method": "PUT", "path": "/api/resource/123", "headers": {{"Authorization": "Bearer standard"}}, "body": "{{\\"name\\":\\"pwned\\"}}" }}
      ]
    }}
  ]
}}

Generate exactly {max_workflows} distinct workflows. Ensure the paths and methods match those available in the provided spec.
"""
        
        # Truncate spec to fit typical context windows
        spec_str = json.dumps(spec)[:8000]

        try:
            response = await self.llm_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": spec_str}
                ],
                response_format={ "type": "json_object" },
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed.get("workflows", [])
            
        except Exception as e:
            print(f"Theorist LLM generation failed: {e}")
            return []
