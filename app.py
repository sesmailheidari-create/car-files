import os
from pathlib import Path

env = Path(__file__).parent / ".env"
if env.exists():
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT") or os.getenv("PORT") or 8000)
    uvicorn.run("server.main:app", host="0.0.0.0", port=port)
