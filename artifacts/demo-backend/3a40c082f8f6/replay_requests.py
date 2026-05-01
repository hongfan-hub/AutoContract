import json
import requests

BASE_URL = "http://127.0.0.1:8001"

payload_1 = null
response = requests.request("GET", BASE_URL + "/health", json=payload_1, headers={})
print("GET /health", response.status_code, response.text)

payload_2 = {"name": "demo", "email": "demo@example.com", "age": 18}
response = requests.request("POST", BASE_URL + "/users", json=payload_2, headers={"Content-Type": "application/json"})
print("POST /users", response.status_code, response.text)

payload_3 = null
response = requests.request("GET", BASE_URL + "/users/1", json=payload_3, headers={})
print("GET /users/1", response.status_code, response.text)
