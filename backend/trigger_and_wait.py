import urllib.request
import json
import time

def main():
    print("Triggering new mock investigation...")
    req = urllib.request.Request('http://localhost:8000/api/investigations?account_id=ACC-MOCK-001', method='POST')
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        case_id = data['case_id']
        print(f"Created case: {case_id}")
    except Exception as e:
        print(f"Failed to trigger mock: {e}")
        return

    # Now we need to start the background run
    print(f"Starting run for case {case_id}...")
    req = urllib.request.Request(f'http://localhost:8000/api/investigations/{case_id}/run', method='POST')
    try:
        res = urllib.request.urlopen(req)
        print("Run started.")
    except Exception as e:
        print(f"Failed to start run: {e}")
        return

    print("Polling for completion...")
    for i in range(300):
        time.sleep(5)
        req = urllib.request.Request(f'http://localhost:8000/api/investigations/{case_id}', method='GET')
        try:
            res = urllib.request.urlopen(req)
            state = json.loads(res.read().decode('utf-8'))
            stage = state.get('current_stage')
            errors = state.get('errors', [])
            print(f"Stage: {stage}, Errors count: {len(errors)}")
            if errors:
                print("Errors:")
                print(json.dumps(errors, indent=2))
                break
        except Exception as e:
            print(f"Failed to poll: {e}")
            break

if __name__ == '__main__':
    main()
