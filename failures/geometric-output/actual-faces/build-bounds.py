"""Build bounded standalone mesh probes against existing matching rlibs."""
import argparse,os,pathlib,platform,subprocess,sys,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rlib',required=True,type=pathlib.Path);p.add_argument('--triangles',action='store_true',help='check triangle deviation and actual meshing tolerance');p.add_argument('--stepio-rlib',type=pathlib.Path);p.add_argument('--meshalgo-rlib',type=pathlib.Path);p.add_argument('--native-lib-dir',type=pathlib.Path,action='append',default=[]);p.add_argument('--static-crt',action='store_true');a=p.parse_args()
if a.triangles and (not a.stepio_rlib or not a.meshalgo_rlib):p.error('--triangles needs --stepio-rlib and --meshalgo-rlib from the matching build')
here=pathlib.Path(__file__).resolve().parent;rlib=a.rlib.resolve(strict=True)
with tempfile.TemporaryDirectory(prefix='look-bounds-probe-') as temp:
 exe=pathlib.Path(temp)/('mesh.exe' if os.name=='nt' else 'mesh');cmd=['rustc','--edition=2021','-O','-C','lto=thin','-C','codegen-units=1'];features=[]
 if a.static_crt:features.append('+crt-static')
 if platform.machine().lower() in ('x86_64','amd64'):features.extend(['+avx','+fma'])
 if features:cmd+=['-C','target-feature='+','.join(features)]
 cmd+=['-L','dependency='+str(rlib.parent)]
 for native in a.native_lib_dir:cmd+=['-L','native='+str(native.resolve(strict=True))]
 result=subprocess.run(cmd+['--extern','look='+str(rlib),str(here/('triangles.rs' if a.triangles else 'bounds.rs')),'-o',str(exe)],timeout=180)
 if result.returncode:sys.exit(result.returncode)
 check=[sys.executable,str(here/('triangles-check.py' if a.triangles else 'bounds-check.py')),'--exe',str(exe)]
 if a.triangles:
  step=a.stepio_rlib.resolve(strict=True);mesh=a.meshalgo_rlib.resolve(strict=True);tol=pathlib.Path(temp)/('tolerance.exe' if os.name=='nt' else 'tolerance')
  extra=['-L','dependency='+str(step.parent),'-L','dependency='+str(mesh.parent),'--extern','truck_stepio='+str(step),'--extern','truck_meshalgo='+str(mesh),str(here/'tolerance.rs'),'-o',str(tol)]
  result=subprocess.run(cmd+extra,timeout=180)
  if result.returncode:sys.exit(result.returncode)
  check+=['--tolerance-exe',str(tol)]
 result=subprocess.run(check,timeout=20);sys.exit(result.returncode)
