"""Check mesh centroid deviation from the two declared surfaces in fan fixtures."""
import argparse,os,pathlib,re,shutil,subprocess,sys,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=pathlib.Path,required=True);p.add_argument('--tolerance-exe',type=pathlib.Path,required=True);p.add_argument('--timeout',type=float,default=3);a=p.parse_args()
if not 0<a.timeout<=10:p.error('timeout must be in (0,10]')
exe=a.exe.resolve(strict=True);tolerance_exe=a.tolerance_exe.resolve(strict=True);here=pathlib.Path(__file__).resolve().parent;base=pathlib.Path(os.environ['LOCALAPPDATA'])/'StepThumbnail/private-probes';base.mkdir(parents=True,exist_ok=True)
cases=[('04-streak',[2,1.96,.04,4.04]),('05-streak',[5.1,4.6,.5,10.9,.11,0]),('08',[6.5,6.,.5,6.5]),('09',[2.5,2.3,.2,3.7]),('10',[3.75,3.35,.4,12.6])];failure=False
for name,params in cases:
 with tempfile.TemporaryDirectory(prefix='look-triangles-',dir=base) as temp:
  model=pathlib.Path(temp)/'case.step';shutil.copyfile(here/f'case-{name}.stepdata',model)
  try:r=subprocess.run([str(exe),str(model),*map(str,params)],capture_output=True,text=True,timeout=a.timeout)
  except subprocess.TimeoutExpired:print(name,'TIMEOUT');failure=True;continue
  match=re.search(r'centroids > 0\.05 source units from either surface (\d+), maximum ([\d.]+)',r.stdout)
  vertices=re.search(r'vertices near source surfaces (\d+)/(\d+)',r.stdout)
  try:measurement=subprocess.run([str(tolerance_exe),str(model)],capture_output=True,text=True,timeout=a.timeout)
  except subprocess.TimeoutExpired:print(name,'TOLERANCE TIMEOUT');failure=True;continue
  tol=re.search(r'model diameter ([\d.]+), chord tolerance ([\d.]+)',measurement.stdout)
  ok=not r.returncode and not measurement.returncode and match and vertices and tol and int(match[1])>0 and int(vertices[1])==int(vertices[2]) and float(match[2])>10*float(tol[2])
  print(name,measurement.stdout.strip(),r.stdout.strip(), 'ratio' if ok else 'UNEXPECTED', round(float(match[2])/float(tol[2]),1) if ok else '',flush=True);failure |= not bool(ok)
sys.exit(1 if failure else 0)
