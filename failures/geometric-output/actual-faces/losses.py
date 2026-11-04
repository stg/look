"""Verify reduced actual-face conversion and meshing losses with a bounded importer."""
import argparse,json,os,pathlib,shutil,subprocess,sys,tempfile
p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True);group.add_argument('--exe',type=pathlib.Path);group.add_argument('--look-exe',type=pathlib.Path);p.add_argument('--timeout',type=float,default=5);a=p.parse_args()
if not 0<a.timeout<=10:p.error('timeout must be in (0,10]')
exe=(a.look_exe or a.exe).resolve(strict=True);root=pathlib.Path(__file__).resolve().parent;base=pathlib.Path(os.environ['LOCALAPPDATA'])/'StepThumbnail/private-probes';base.mkdir(parents=True,exist_ok=True);failed=False
for n,face,suffix in [(1,811,''),(2,320,''),(2,119,'-parity'),(4,17,''),(5,560,''),(6,14018,''),(6,7209,'-plane'),(7,559,'')]:
 with tempfile.TemporaryDirectory(prefix='look-lost-face-',dir=base) as d:
  src=pathlib.Path(d)/'case.step';shutil.copyfile(root/(f'case-{n:02d}' + suffix + '.stepdata'),src);request=json.dumps({'path':str(src),'colours':True,'seconds':4})+'\n'
  try:
   child=subprocess.run([str(exe),'inspect',str(src),'--up-axis','z','--json'] if a.look_exe else [str(exe),'--import-worker','1'],input=None if a.look_exe else request.encode(),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=a.timeout)
  except subprocess.TimeoutExpired:print(f'case-{n:02d}: TIMEOUT');failed=True;continue
  log=child.stderr.decode('utf8',errors='replace');records=[]
  for line in log.splitlines():
   if line.startswith('{'):
    try:records.append(json.loads(line))
    except json.JSONDecodeError:pass
  matched=any(r.get('source_face_id')==face and ((r.get('terminal_reason')=='ContradictoryDualParity') if suffix=='-parity' else (r.get('refusal_tag')=='EdgeCurveConversionFailed' and r.get('declared_shell_faces')==2 and r.get('surviving_shell_faces')==1)) for r in records)
  ok=child.returncode==0 and matched and 'warning: 1 of 2 STEP faces' in log
  print(f'case-{n:02d}'+suffix+':', 'verified: source face refused; one of two faces lost' if ok else 'unexpected result',flush=True);failed |= not ok
for n in [6,7]:
 with tempfile.TemporaryDirectory(prefix='look-loss-control-',dir=base) as d:
  src=pathlib.Path(d)/'case.step';shutil.copyfile(root/f'case-{n:02d}-control.stepdata',src);request=json.dumps({'path':str(src),'colours':True,'seconds':4})+'\n'
  try:
   child=subprocess.run([str(exe),'inspect',str(src),'--up-axis','z','--json'] if a.look_exe else [str(exe),'--import-worker','1'],input=None if a.look_exe else request.encode(),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=a.timeout)
  except subprocess.TimeoutExpired:print(f'case-{n:02d}-control: TIMEOUT');failed=True;continue
  log=child.stderr.decode('utf8',errors='replace');ok=child.returncode==0 and 'warning:' not in log and 'EdgeCurveConversionFailed' not in log
  print(f'case-{n:02d}-control:', 'verified: neither face was refused' if ok else 'unexpected result',flush=True);failed |= not ok
sys.exit(1 if failed else 0)
