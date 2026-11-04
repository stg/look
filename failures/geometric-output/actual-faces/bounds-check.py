"""Verify the known excessive compiled axial bound of the reduced conical face."""
import argparse, os, pathlib, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from support import temporary, record
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--exe', type=pathlib.Path, required=True)
p.add_argument('--timeout', type=float, default=3)
a = p.parse_args()
if not 0 < a.timeout <= 10:
    p.error('timeout must be in (0,10]')
exe = a.exe.resolve(strict=True)
here = pathlib.Path(__file__).resolve().parent
with temporary('look-bounds-') as temp:
    model = pathlib.Path(temp) / 'case.step'
    shutil.copyfile(here / 'case-03.stepdata', model)
    try:
        r = subprocess.run([str(exe), str(model)], capture_output=True, text=True, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print('bounds probe exceeded external timeout')
        sys.exit(1)
    record('cone-bounds', r.stdout + r.stderr)
    print(r.stdout.strip())
    print(r.stderr.strip(), file=sys.stderr)
    m = re.search('max \\[[^,]+,\\s*([-+0-9.eE]+),', r.stdout)
    if r.returncode or not m:
        sys.exit('failed to read compiled bounds')
    actual = float(m.group(1))
    expected = 2.927071885719
    if actual <= expected + 0.001:
        sys.exit('observed oversized bound no longer reproduced')
    print('verified: compiled axial maximum', actual, 'exceeds source maximum', expected)
