import os, time, requests
from tenacity import retry, wait_fixed, stop_after_delay

BASE = os.getenv("API_BASE", "http://localhost:8000")

@retry(wait=wait_fixed(2), stop=stop_after_delay(60))
def wait_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    r.raise_for_status()

def test_health():
    wait_health()

def test_estados_list():
    wait_health()
    r = requests.get(f"{BASE}/estados", timeout=5)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_contactos_list():
    wait_health()
    r = requests.get(f"{BASE}/contactos?limit=5", timeout=5)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
