"""SYNTHETIC documented demo launcher, real process/network and clean shutdown."""
import signal
import subprocess
import time
from uuid import uuid4
import httpx
from apps.core.storage import REPO
from test_m1_domain import isolated

ORIGIN = 'http://127.0.0.1:8765'


def launch(root):
    process = subprocess.Popen(['bash', 'scripts/demo.sh', str(root),ORIGIN.rsplit(':',1)[1]], cwd=REPO,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    code = None
    # stdout contains only the initializer and launcher; keep the code memory-only.
    for _ in range(5):
        line = process.stdout.readline()
        if line.startswith('One-time unlock code (5 min): '):
            code = line.split(': ', 1)[1].strip()
            break
        if not line:
            break
    if not code:
        stop(process)
        raise AssertionError('Synthetic demo did not produce its local unlock prompt')
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            if httpx.get(ORIGIN, timeout=.2).status_code == 200:
                return process, code
        except httpx.HTTPError:
            pass
        if process.poll() is not None:
            break
        time.sleep(.02)
    stop(process)
    raise AssertionError('Synthetic demo did not become ready on loopback')


def stop(process):
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate(); process.wait(timeout=5)
    if process.stdout:
        process.stdout.close()


def test_A09_documented_demo_start_unlock_restart_stop(isolated,isolated_preflight_port,monkeypatch):
    monkeypatch.setattr(__import__(__name__),'ORIGIN',f'http://127.0.0.1:{isolated_preflight_port}')
    root = isolated / 'launcher-demo'
    process, code = launch(root)
    try:
        with httpx.Client(base_url=ORIGIN, headers={'Origin':ORIGIN}, timeout=5) as client:
            unlock = client.post('/api/v1/auth/unlock', json={'code':code})
            assert unlock.status_code == 200
            client.headers['X-CSRF-Token'] = unlock.json()['csrf_token']
            assert client.get('/api/v1/status').json()['provider'] == 'OFF'
            entries = client.get('/api/v1/entries').json()['items']
            assert {e['type'] for e in entries} == {'inbox','daily','sleep','creative'}
            assert all(e['raw_text'].startswith('SYNTHETIC') for e in entries)
            request = {'operation_id':str(uuid4()),'entry_id':str(uuid4()),'base_revision':0,
                       'payload':{'raw_text':'SYNTHETIC · launcher committed note'}}
            assert client.post('/api/v1/entries',json=request).status_code == 201
            stop(process)
            process, code = launch(root)
            assert client.get('/api/v1/status').status_code == 401
            unlock = client.post('/api/v1/auth/unlock',json={'code':code})
            assert unlock.status_code == 200
            entry = client.get('/api/v1/entries/' + request['entry_id']).json()
            assert entry['raw_text'] == request['payload']['raw_text']
            assert len(client.get('/api/v1/entries').json()['items']) == 5  # no reseed on restart
    finally:
        stop(process)
    assert process.returncode == 0
