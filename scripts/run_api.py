import sys
import os
from pathlib import Path

# Ensure paths
root_dir = Path(__file__).resolve().parent.parent
api_dir = root_dir / "apps" / "api"
sys.path.insert(0, str(api_dir))
sys.path.insert(0, str(root_dir))

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://pench:pench@localhost:5432/pench")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
