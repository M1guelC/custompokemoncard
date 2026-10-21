import os
import sys
from pathlib import Path


def main():
    try:
        from cardmaker.server import serve
    except ImportError:
        venv = Path(__file__).resolve().parent / ".venv" / "bin" / "python"
        if venv.exists() and Path(sys.executable).resolve() != venv.resolve():
            os.execv(str(venv), [str(venv), *sys.argv])
        raise SystemExit(
            "Install the dependencies with:\n  .venv/bin/pip install -r requirements.txt"
        )
    serve()


if __name__ == "__main__":
    main()
