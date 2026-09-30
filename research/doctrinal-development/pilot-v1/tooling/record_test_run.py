"""Retain real focused unittest execution and pre-run snapshots. No fabricated logs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
name, *tests = sys.argv[1:]
if not name or Path(name).name != name:
    raise SystemExit('use a single evidence directory name')
target = HERE / 'evidence' / name
target.mkdir(parents=True, exist_ok=False)
command = [sys.executable, '-B', '-m', 'unittest', '-v', *(tests or ['test_verify_pilot'])]
files = [HERE / 'test_verify_pilot.py', HERE / 'verify_pilot.py',
         HERE.parent / 'PROTOCOL.md', HERE.parent / 'ARTIFACT-CONTRACT.md',
         HERE.parent.parents[2] / 'src' / 'models' / 'quotation_verifier.py']
snapshots = {}
for path in files:
    if path.is_file():
        data = path.read_bytes()
        (target / (path.name + '.snapshot')).write_bytes(data)
        snapshots[str(path)] = hashlib.sha256(data).hexdigest()
    else:
        snapshots[str(path)] = None
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
result = subprocess.run(command, cwd=HERE, env=env, capture_output=True,
                        text=True, encoding='utf-8', errors='replace')
record = dict(command=command, cwd=str(HERE), env_overrides={'PYTHONDONTWRITEBYTECODE': '1'},
              exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
              pre_run_sha256=snapshots)
(target / 'execution.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
raise SystemExit(result.returncode)
