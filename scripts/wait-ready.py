"""Bounded readiness check for local development and CI."""

import time
from urllib.error import URLError
from urllib.request import urlopen

for attempt in range(30):
    try:
        with urlopen("http://127.0.0.1:8000/ready", timeout=2) as response:
            if response.status == 200:
                print("Registry API ready.")
                break
    except (URLError, TimeoutError):
        pass
    time.sleep(1)
else:
    raise SystemExit("Registry API did not become ready within the startup window.")
