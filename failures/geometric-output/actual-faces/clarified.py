"""Verify rejection of the clarified source face and its original inch context."""
import argparse, json, os, pathlib, re, shutil, subprocess, sys, tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--look-exe',required=True,type=pathlib.Path);p.add_argument('--timeout',type=float,default=5);a=p.parse_args()
if not 0<a.timeout<=10:p.error('timeout must be in (0,10]')
exe=a.look_exe.resolve(strict=True);here=pathlib.Path(__file__).resolve().parent;fixture=here/'case-06-clarified.stepdata';text=fixture.read_text(encoding='ascii')
if not ("CONVERSION_BASED_UNIT('INCH'" in text and re.search(r'UNCERTAINTY_MEASURE_WITH_UNIT\s*\(\s*LENGTH_MEASURE\s*\(\s*1\.E-3\s*\)',text,re.I) and 'GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT' in text):sys.exit('original inch/uncertainty context missing')
base=pathlib.Path(os.environ['LOCALAPPDATA'])/'StepThumbnail/private-probes';base.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='look-clarified-face-',dir=base) as tmp:
 source=pathlib.Path(tmp)/'case.step';shutil.copyfile(fixture,source)
 try:r=subprocess.run([str(exe),'inspect',str(source),'--up-axis','z','--json'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,encoding='utf8',errors='replace',timeout=a.timeout)
 except subprocess.TimeoutExpired:sys.exit('external timeout: probe killed and reaped')
 records=[]
 for line in r.stderr.splitlines():
  if line.startswith('{'):
   try:records.append(json.loads(line))
   except json.JSONDecodeError:pass
 found=any(x.get('source_face_id')==7209 and x.get('refusal_tag')=='EdgeCurveConversionFailed' and x.get('declared_shell_faces')==1 and x.get('surviving_shell_faces')==0 for x in records)
 if r.returncode==0 or not found:sys.exit('expected clarified-face refusal not reproduced')
 print('verified: inch context and 0.001-inch source closure uncertainty retained')
 print('verified: source face #7209 refused in edge conversion; 0 of 1 faces survive')
 print('current Look inspect exits nonzero because the reduced scene has no triangles')
