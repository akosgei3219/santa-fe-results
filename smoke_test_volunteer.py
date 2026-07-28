"""Simple smoke test: POST a volunteer to the running HTTP server.

Usage:
    python smoke_test_volunteer.py http://127.0.0.1:8000/volunteer
"""
import sys, json, urllib.request

def main():
    if len(sys.argv) < 2:
        print("Usage: python smoke_test_volunteer.py http://host:port/volunteer")
        return
    url = sys.argv[1]
    payload = {"name": "Smoke Tester", "email": "smoke@example.com", "role": "expoSupport"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode()
            print('Status:', resp.status)
            print('Body:', body)
    except Exception as e:
        print('Request failed:', e)

if __name__ == '__main__':
    main()
