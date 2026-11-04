from pathlib import Path
import argparse, subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--exe',required=True,type=Path);p.add_argument('--timeout',type=float,default=2);a=p.parse_args()
if not 0<a.timeout<=10:p.error('timeout must be in (0,10]')
r=Path(__file__).resolve().parent
cases=[(1,815,'(NaN, NaN)'),(2,333,'(NaN, NaN)'),(4,21,'1.257e-4'),(5,586,'1.536e-2'),(6,7163,'5.012e-5'),(7,573,'8.598e-4')];fail=False
for number,edge,expected in cases:
 c=subprocess.Popen([str(a.exe.resolve(strict=True)),str(r/f'case-{number:02d}.stepdata'),str(edge)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  try:out,err=c.communicate(timeout=a.timeout)
  except subprocess.TimeoutExpired:c.kill();c.communicate();print(f'case-{number:02d}: TIMEOUT');fail=True;continue
  ok=c.returncode!=0 and expected in err; print(f'case-{number:02d}:', 'observed expected diagnostic' if ok else 'unexpected result',err.strip());fail |= not ok
 finally:
  if c.poll() is None:c.kill();c.wait()
sys.exit(1 if fail else 0)
