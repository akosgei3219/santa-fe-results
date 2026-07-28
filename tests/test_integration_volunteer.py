import os
import time
import subprocess
import sys
import urllib.request
import json
import signal

import pytest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, '..')
ROOT = os.path.abspath(ROOT)

SERVER_PY = os.path.join(ROOT, 'server.py')

def wait_for_server(url, timeout=8.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                return True
        except Exception:
            time.sleep(0.2)
    return False

@pytest.mark.timeout(30)
def test_volunteer_endpoint_end_to_end(tmp_path):
    env = os.environ.copy()
    env['MCP_TRANSPORT'] = 'http'
    env['MCP_HOST'] = '127.0.0.1'
    env['MCP_PORT'] = '8002'
    env['VOLUNTEER_RATE_LIMIT'] = '1000'  # avoid hitting rate limiter
    # start server subprocess
    proc = subprocess.Popen([sys.executable, SERVER_PY, 'http'], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert wait_for_server('http://127.0.0.1:8002/leaderboard.json', timeout=10), 'server did not start'
        url = 'http://127.0.0.1:8002/volunteer'
        payload = {"name": "Integration Tester", "email": "itest@example.com", "role": "expoSupport"}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=8) as resp:
            assert resp.status in (200,201)
            body = json.loads(resp.read().decode())
            assert body.get('status') == 'ok'
    finally:
        if os.name == 'nt':
            proc.terminate()
        else:
            proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
