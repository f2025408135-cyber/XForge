import pytest
from app.poc_generator import PoCGenerator

def test_generate_curl_simple():
    method = "GET"
    url = "https://example.com/api/users"
    headers = {"Authorization": "Bearer test1234"}
    
    curl_cmd = PoCGenerator.generate_curl(method, url, headers)
    
    assert curl_cmd == "curl -X GET 'https://example.com/api/users' -H 'Authorization: Bearer test1234'"

def test_generate_curl_complex_json():
    method = "POST"
    url = "https://example.com/api/admin"
    headers = {"Content-Type": "application/json", "X-Role": "admin's_role"}
    body = '{"status": "bypassed", "admin": true}'
    
    curl_cmd = PoCGenerator.generate_curl(method, url, headers, body)
    
    assert "curl -X POST 'https://example.com/api/admin'" in curl_cmd
    assert "-H 'Content-Type: application/json'" in curl_cmd
    # Assert single quote escaping works
    assert "-H 'X-Role: admin'\\''s_role'" in curl_cmd
    assert "-d '{\"status\": \"bypassed\", \"admin\": true}'" in curl_cmd

def test_generate_python():
    method = "PUT"
    url = "https://example.com/api/item/5"
    headers = {"Authorization": "Bearer admin"}
    body = '{"price": 0}'
    
    py_script = PoCGenerator.generate_python(method, url, headers, body)
    
    assert "import requests" in py_script
    assert 'url = "https://example.com/api/item/5"' in py_script
    assert '"Authorization": "Bearer admin"' in py_script
    assert 'method="PUT"' in py_script
    assert 'json={\n    "price": 0\n}' in py_script

def test_create_poc_bundle():
    method = "GET"
    target_url = "https://example.com"
    path = "/api/data"
    headers = {"X-Custom": "test"}
    
    bundle = PoCGenerator.create_poc_bundle(method, target_url, path, headers)
    
    assert "curl" in bundle
    assert "python" in bundle
    assert bundle["curl"] == "curl -X GET 'https://example.com/api/data' -H 'X-Custom: test'"
    assert "requests.request" in bundle["python"]
