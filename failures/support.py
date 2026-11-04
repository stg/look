"""Temporary inputs, diagnostic logs and bounded child processes for the reproducers."""
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def temporary(prefix):
    base = os.environ.get("LOOK_FAILURE_WORK_DIR")
    if base:
        Path(base).mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix=prefix, dir=base)


def output_dir():
    path = Path(os.environ.get("LOOK_FAILURE_OUTPUT_DIR", ROOT / "out"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(command, timeout):
    """Kill and reap the child on timeout or interruption. No detached workers."""
    child = subprocess.Popen(
        [str(arg) for arg in command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=0x08000000 if os.name == "nt" else 0,
    )
    try:
        try:
            log, _ = child.communicate(timeout=timeout)
            return child.returncode, log, False
        except subprocess.TimeoutExpired:
            child.kill()
            log, _ = child.communicate()
            return child.returncode, log, True
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def record(name, log):
    (output_dir() / (name + ".log")).write_text(log, encoding="utf-8")
