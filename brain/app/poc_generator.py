import json

class PoCGenerator:
    """
    Converts a successful Fuzzer payload into standard, reproducible Proof-of-Concept scripts.
    Automatically generates `curl` commands and Python `requests` scripts so security
    teams can verify the vulnerability independently of the XForge platform.
    """

    @staticmethod
    def generate_curl(method: str, url: str, headers: dict = None, body: str = None) -> str:
        """
        Translates HTTP parameters into a functional bash curl command.
        """
        curl_cmd = f"curl -X {method} '{url}'"
        
        if headers:
            for k, v in headers.items():
                # Escape single quotes in header values to prevent command injection/breakage
                safe_val = v.replace("'", "'\\''")
                curl_cmd += f" -H '{k}: {safe_val}'"
                
        if body:
            # Safely wrap JSON body in single quotes
            safe_body = body.replace("'", "'\\''")
            curl_cmd += f" -d '{safe_body}'"
            
        return curl_cmd

    @staticmethod
    def generate_python(method: str, url: str, headers: dict = None, body: str = None) -> str:
        """
        Translates HTTP parameters into a functional Python `requests` script.
        """
        # Format headers safely
        header_str = json.dumps(headers, indent=4) if headers else "{}"
        
        # If the body is JSON, we prefer formatting it as a dict. Otherwise, a raw string.
        data_param = "None"
        try:
            if body:
                body_dict = json.loads(body)
                body_str = json.dumps(body_dict, indent=4)
                data_param = f"json={body_str}"
        except json.JSONDecodeError:
            if body:
                data_param = f"data='''{body}'''"

        py_script = f"""import requests

url = "{url}"
headers = {header_str}

response = requests.request(
    method="{method}",
    url=url,
    headers=headers,
    {data_param}
)

print(f"Status Code: {{response.status_code}}")
print(f"Response Body: {{response.text}}")
"""
        return py_script

    @staticmethod
    def create_poc_bundle(method: str, target_url: str, path: str, headers: dict = None, body: str = None) -> dict:
        """
        Creates a bundled dictionary containing both PoC formats for the reporting engine.
        """
        full_url = f"{target_url.rstrip('/')}/{path.lstrip('/')}"
        
        return {
            "curl": PoCGenerator.generate_curl(method, full_url, headers, body),
            "python": PoCGenerator.generate_python(method, full_url, headers, body)
        }
