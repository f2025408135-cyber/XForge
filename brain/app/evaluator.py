from typing import List, Dict
import os
from openai import AsyncOpenAI

class EvaluatorAgent:
    """
    Analyzes raw execution results (status codes, body lengths) to determine 
    if a vulnerability was successfully exploited. Minimizes false positives.
    """
    def __init__(self):
        self.llm_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy_key"))

    def evaluate_bola(self, results: List[Dict]) -> Dict:
        """
        Evaluates BOLA (Broken Object Level Authorization) results.
        Looks for unauthorized roles successfully modifying or accessing restricted resources.
        
        Expected input format:
        [
            {"method": "GET", "path": "/api/users/1", "status_code": 200, "role": "admin", "body_len": 500},
            {"method": "GET", "path": "/api/users/1", "status_code": 200, "role": "standard", "body_len": 500} # BOLA anomaly
        ]
        """
        score = 0.0
        findings = []

        # Simple heuristic: Did the lower privileged request succeed?
        for res in results:
            role = res.get("role", "unknown")
            status = res.get("status_code", 0)

            if role != "admin" and status in [200, 201, 204]:
                # Warning sign, need to compare body length to admin to ensure it's not a generic public response
                admin_res = next((r for r in results if r.get("role") == "admin"), None)
                if admin_res:
                    size_diff = abs(admin_res.get("body_len", 0) - res.get("body_len", 0))
                    # If sizes are extremely similar, it's highly likely they accessed the same restricted object
                    if size_diff < 50:
                        score += 0.9
                        findings.append(f"High confidence BOLA on {res.get('path')}: Non-admin role achieved {status} with similar payload size to admin.")
                    else:
                        score += 0.5
                        findings.append(f"Possible BOLA on {res.get('path')}: Non-admin role achieved {status}, but response sizes differ significantly.")
                else:
                    score += 0.4
                    findings.append(f"Unauthorized success on {res.get('path')} (Status {status}), but no baseline to compare.")

            elif status in [401, 403]:
                findings.append(f"Authorization boundary held firm for {role} on {res.get('path')}.")

            elif status >= 500:
                score += 0.3
                findings.append(f"Unhandled exception (Status {status}) on {res.get('path')}. Potential logic flaw or crash.")

        return {
            "vuln_score": min(score, 1.0),
            "findings": findings
        }

    async def evaluate_complex_logic_flaw(self, context_str: str, raw_responses: List[Dict]) -> Dict:
        """
        When simple heuristics fail, feed the raw HTTP responses (truncated) to the LLM 
        to determine if a multi-step logic flaw occurred (e.g., negative balance transfer bypass).
        """
        system_prompt = """
You are an expert security evaluator. You are given the context of a multi-step attack and the raw HTTP responses.
Analyze the responses to determine if the attack successfully bypassed business logic.

Return ONLY valid JSON matching this structure:
{
  "is_vulnerable": true/false,
  "confidence": 0.0 to 1.0,
  "explanation": "Brief explanation of why"
}
"""
        try:
            response = await self.llm_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context_str}\\nResponses: {raw_responses}"}
                ],
                response_format={ "type": "json_object" },
                temperature=0.2
            )
            
            import json
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            return {"is_vulnerable": False, "confidence": 0.0, "explanation": f"LLM Evaluation failed: {e}"}
