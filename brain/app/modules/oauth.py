import uuid

class OAuthModule:
    """
    Identifies OAuth 2.0 endpoints in the OpenAPI spec and generates payloads
    to test for Open Redirects and State Manipulation vulnerabilities.
    """
    def __init__(self):
        # We look for standard OAuth 2.0 / OIDC endpoint signatures
        self.oauth_keywords = ["/authorize", "/callback", "/oauth", "/login/sso", "/auth"]

    def identify_targets(self, openapi_spec: dict) -> list:
        targets = []
        paths = openapi_spec.get("paths", {})
        
        for path, methods in paths.items():
            is_oauth = any(keyword in path.lower() for keyword in self.oauth_keywords)
            if is_oauth:
                for method, operation in methods.items():
                    if method.lower() == "get":
                        targets.append({"path": path, "method": "GET"})
        return targets

    def generate_workflows(self, target_url: str, targets: list) -> list:
        tasks = []
        for target in targets:
            task_id = f"oauth-run-{uuid.uuid4().hex[:8]}"
            payloads = []
            
            base_path = target["path"]
            separator = "&" if "?" in base_path else "?"
            
            # Fuzz 1: Open Redirect via redirect_uri manipulation
            evil_redirects = ["https://evil.com", "//evil.com", "\\\\evil.com"]
            for r in evil_redirects:
                payloads.append({
                    "method": "GET",
                    "path": f"{base_path}{separator}redirect_uri={r}",
                    "headers": {},
                    "body": ""
                })
            
            # Fuzz 2: State parameter removal/manipulation (CSRF on OAuth)
            payloads.append({
                "method": "GET",
                "path": f"{base_path}{separator}state=fixed_state_123&code=hacked",
                "headers": {},
                "body": ""
            })

            tasks.append({
                "task_id": task_id,
                "target_url": target_url,
                "attack_type": "oauth_abuse",
                "payloads": payloads
            })

        return tasks
