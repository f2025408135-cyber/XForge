import uuid

class BolaModule:
    """
    Identifies endpoints likely susceptible to Broken Object Level Authorization (BOLA/IDOR)
    and constructs multi-user state-chaining workflows.
    """
    
    def __init__(self, admin_token: str, standard_token: str):
        self.admin_token = admin_token
        self.standard_token = standard_token

    def identify_targets(self, openapi_spec: dict) -> list:
        """
        Parses an OpenAPI spec looking for endpoints with path parameters (e.g. /users/{id})
        that support GET, PUT, or DELETE.
        """
        targets = []
        paths = openapi_spec.get("paths", {})
        
        for path, methods in paths.items():
            if "{" in path and "}" in path:
                # We found an endpoint with a path parameter
                for method in methods.keys():
                    if method.lower() in ["get", "put", "delete", "patch"]:
                        targets.append({
                            "path": path,
                            "method": method.upper()
                        })
        return targets

    def generate_workflows(self, target_url: str, targets: list) -> dict:
        """
        Takes the identified target endpoints and generates the dual-role payload chain
        matching the task_schema.json contract for the Golang Executor.
        """
        task_id = f"bola-run-{uuid.uuid4().hex[:8]}"
        payloads = []
        
        for target in targets:
            # We construct a fake ID for fuzzing. In a true dynamic engine, 
            # this ID would be captured from a previous 'setup' POST request.
            test_path = target["path"].replace("{id}", "999").replace("{user_id}", "999")
            
            # Request 1: The privileged user accessing the object (Baseline)
            payloads.append({
                "method": target["method"],
                "path": test_path,
                "headers": {
                    "Authorization": f"Bearer {self.admin_token}",
                    "X-Role-Tag": "admin" # Used by the evaluator agent to identify the baseline
                },
                "body": ""
            })
            
            # Request 2: The unprivileged user attempting to access the SAME object
            payloads.append({
                "method": target["method"],
                "path": test_path,
                "headers": {
                    "Authorization": f"Bearer {self.standard_token}",
                    "X-Role-Tag": "standard"
                },
                "body": ""
            })

        return {
            "task_id": task_id,
            "target_url": target_url,
            "attack_type": "bola",
            "payloads": payloads
        }
