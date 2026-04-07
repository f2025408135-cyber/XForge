import uuid

class RaceConditionModule:
    """
    Identifies endpoints likely susceptible to Time-of-Check to Time-of-Use (TOCTOU)
    race conditions and constructs high-concurrency execution payloads.
    """
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        
        # High-risk keywords often tied to stateful transactions
        self.risk_keywords = ["transfer", "redeem", "checkout", "apply", "coupon", "claim", "submit", "vote", "pay"]

    def identify_targets(self, openapi_spec: dict) -> list:
        """
        Parses an OpenAPI spec looking for POST/PUT endpoints with paths or names
        matching high-risk transaction keywords.
        """
        targets = []
        paths = openapi_spec.get("paths", {})
        
        for path, methods in paths.items():
            for method in methods.keys():
                if method.lower() not in ["post", "put", "patch"]:
                    continue
                
                # Check path string for risk keywords
                is_risky = any(keyword in path.lower() for keyword in self.risk_keywords)
                
                # Check operationId or summary if present
                if not is_risky:
                    operation = methods[method]
                    summary = operation.get("summary", "").lower()
                    op_id = operation.get("operationId", "").lower()
                    is_risky = any(kw in summary or kw in op_id for kw in self.risk_keywords)
                
                if is_risky:
                    targets.append({
                        "path": path,
                        "method": method.upper()
                    })
        return targets

    def generate_workflows(self, target_url: str, targets: list, concurrency_count: int = 20) -> list:
        """
        Generates individual task workflows for each risky endpoint.
        Each workflow duplicates the exact same payload N times to execute simultaneously.
        """
        tasks = []
        
        for target in targets:
            task_id = f"race-run-{uuid.uuid4().hex[:8]}"
            payloads = []
            
            # Construct a dummy JSON body - in reality, we'd infer schema from the spec.
            dummy_body = '{"amount": 100, "code": "WINTER25"}'
            
            base_payload = {
                "method": target["method"],
                "path": target["path"].replace("{id}", "999").replace("{user_id}", "999"),
                "headers": {
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json",
                    "X-Race-Identifier": task_id
                },
                "body": dummy_body
            }
            
            # Duplicate the request exactly N times
            for _ in range(concurrency_count):
                payloads.append(base_payload)

            tasks.append({
                "task_id": task_id,
                "target_url": target_url,
                "attack_type": "race_condition",
                "payloads": payloads
            })

        return tasks
