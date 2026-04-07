import json
import uuid
from typing import List, Dict

class LogicFlowModule:
    """
    Identifies multi-step business logic workflows (e.g., Create User -> Add Item -> Checkout)
    and constructs TaskPayloads to deliberately abuse state transitions (e.g., skipping Checkout).
    """
    def __init__(self, theorist_agent):
        # We inject the LLM-powered TheoristAgent to handle the complex reasoning 
        # required to piece together an application's specific business flow.
        self.theorist = theorist_agent

    async def generate_abuse_workflows(self, target_url: str, openapi_spec: dict, auth_token: str) -> List[Dict]:
        """
        Feeds the spec to the LLM and requests it to map out the standard business logic flow,
        then asks for 3 deliberate mutations (skipping steps, repeating steps, modifying states out of order).
        """
        system_prompt = """
You are an expert security researcher. You are given a truncated OpenAPI JSON specification.
Your goal is to map out a multi-step business logic flow (e.g., creating an order and paying for it).
Then, generate 3 mutated workflows that attempt to abuse the state logic (e.g., calling the /pay endpoint before /create).

Return ONLY valid JSON matching this schema exactly:
{
  "workflows": [
    {
      "attack_type": "logic_abuse",
      "payloads": [
        { "method": "POST", "path": "/api/cart/checkout", "headers": {"Authorization": "Bearer token"}, "body": "{\\"amount\\": 0}" },
        { "method": "POST", "path": "/api/cart/add", "headers": {"Authorization": "Bearer token"}, "body": "{\\"item_id\\": 1}" }
      ]
    }
  ]
}
"""
        # Truncate spec to fit typical context windows
        spec_str = json.dumps(openapi_spec)[:8000]

        try:
            response = await self.theorist.llm_client.chat.completions.create(
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
            raw_workflows = parsed.get("workflows", [])
            
            # Structure into proper Task schemas
            tasks = []
            for wf in raw_workflows:
                # Ensure the auth token is injected dynamically
                for p in wf.get("payloads", []):
                    if "headers" not in p:
                        p["headers"] = {}
                    p["headers"]["Authorization"] = f"Bearer {auth_token}"
                    
                tasks.append({
                    "task_id": f"logic-run-{uuid.uuid4().hex[:8]}",
                    "target_url": target_url,
                    "attack_type": "logic_abuse",
                    "payloads": wf.get("payloads", [])
                })
                
            return tasks
            
        except Exception as e:
            print(f"LogicFlow LLM generation failed: {e}")
            return []
