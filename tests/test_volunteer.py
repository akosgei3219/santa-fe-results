import os
import json
import types
import builtins
import urllib.request

import pytest

from server import check_rate_limit, verify_recaptcha, _get_redis_client

class DummyResp:
    def __init__(self, data: dict):
        self._data = json.dumps(data).encode('utf-8')
    def read(self):
        return self._data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

# -------------------- recaptcha tests --------------------

def test_verify_recaptcha_requires_secret(monkeypatch):
    os.environ.pop('RECAPTCHA_SECRET', None)
    with pytest.raises(RuntimeError):
        verify_recaptcha('token')


def test_verify_recaptcha_success(monkeypatch):
    os.environ['RECAPTCHA_SECRET'] = 'secret'
    def fake_urlopen(req, timeout=6):
        return DummyResp({"success": True, "score": 0.92, "action": "volunteer"})
    monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen)
    v = verify_recaptcha('token')
    assert v['success'] is True
    assert v['score'] == 0.92
    assert v['action'] == 'volunteer'

# -------------------- rate limiter tests --------------------

def test_check_rate_limit_in_memory(monkeypatch):
    os.environ['VOLUNTEER_RATE_LIMIT'] = '2'
    os.environ['VOLUNTEER_RATE_WINDOW'] = '60'
    # clear store
    if hasattr(check_rate_limit, '_store'):
        delattr(check_rate_limit, '_store')
    allowed, retry = check_rate_limit('1.2.3.4')
    assert allowed
    allowed, retry = check_rate_limit('1.2.3.4')
    assert allowed
    allowed, retry = check_rate_limit('1.2.3.4')
    assert not allowed
    assert retry > 0


def test_check_rate_limit_redis(monkeypatch):
    os.environ['VOLUNTEER_RATE_LIMIT'] = '2'
    os.environ['VOLUNTEER_RATE_WINDOW'] = '60'
    class FakeRedis:
        def __init__(self):
            self.cnts = {}
            self.ttls = {}
        def incr(self, key):
            v = self.cnts.get(key, 0) + 1
            self.cnts[key] = v
            return v
        def expire(self, key, seconds):
            self.ttls[key] = seconds
        def ttl(self, key):
            return self.ttls.get(key, 1)
    fake = FakeRedis()
    monkeypatch.setattr('server._get_redis_client', lambda: fake)
    # calls
    allowed, retry = check_rate_limit('10.0.0.1')
    assert allowed
    allowed, retry = check_rate_limit('10.0.0.1')
    assert allowed
    allowed, retry = check_rate_limit('10.0.0.1')
    assert not allowed
    assert retry >= 0
