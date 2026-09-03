import httpx
import time

print("Starting direct Ollama API request...")
start = time.time()
try:
    with httpx.Client(base_url="http://localhost:11434", timeout=120.0) as client:
        response = client.post("/api/generate", json={
            "model": "llama3.1:8b",
            "prompt": "Write a 500 word detailed report about a mock bank fraud investigation.",
            "stream": False
        })
        response.raise_for_status()
        end = time.time()
        print(f"Success! Response length: {len(response.json().get('response', ''))}")
        print(f"Time taken: {end - start:.2f} seconds.")
except Exception as e:
    print(f"Error: {e}")
