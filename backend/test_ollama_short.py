import httpx
import time

print("Starting short Ollama API request...")
start = time.time()
try:
    with httpx.Client(base_url="http://localhost:11434", timeout=120.0) as client:
        response = client.post("/api/generate", json={
            "model": "llama3.1:8b",
            "prompt": "Say 'hello'.",
            "stream": False
        })
        response.raise_for_status()
        end = time.time()
        print(f"Success! Response: {response.json().get('response', '')}")
        print(f"Time taken: {end - start:.2f} seconds.")
except Exception as e:
    print(f"Error: {e}")
