"""Render reduced geometry using an isolated, bounded Look or StepThumbs executable."""
import argparse, importlib.util, json, os, pathlib, shutil, struct, subprocess, sys, tempfile, time
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('private_renderer', HERE.parent/'render-private.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
CASES=['03','04-streak','05-streak','06','06-control','07','07-control','08','09','10','11','11-consistent']
def check_stl(p):
 raw=p.read_bytes(); assert struct.unpack_from('<I',raw,80)[0]==2
 triangles=[struct.unpack_from('<12fH',raw,84+50*i) for i in range(2)]
 v=[[tuple(t[3+j*3:6+j*3]) for j in range(3)] for t in triangles]
 edges=[[(x[j],x[(j+1)%3]) for j in range(3)] for x in v]
 same=[(a,b) for a,b in edges[0] for c,d in edges[1] if a==c and b==d]
 opposed=[(a,b) for a,b in edges[0] for c,d in edges[1] if a==d and b==c]
 dot=sum(triangles[0][j]*triangles[1][j] for j in range(3))
 if 'consistent' in p.name: assert len(opposed)==1 and not same and dot>0.99
 else: assert len(same)==1 and not opposed and dot<-.99
 print(p.name,'same-directed shared edges',len(same),'opposite-directed',len(opposed),'normal dot',round(dot,6),flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True);group.add_argument('--exe',type=pathlib.Path,help='StepThumbs executable');group.add_argument('--look-exe',type=pathlib.Path,help='standalone Look CLI');p.add_argument('--case',action='append',choices=CASES);p.add_argument('--deadline',type=float,default=10);p.add_argument('--no-edges',action='store_true');a=p.parse_args()
 if not 0<a.deadline<=10:p.error('deadline must be in (0,10]')
 exe=(a.look_exe or a.exe).resolve(strict=True);h.BASE.mkdir(parents=True,exist_ok=True);output=HERE.parent.parent/'private'/'reduced-results';output.mkdir(parents=True,exist_ok=True);success=True
 for name in a.case or CASES:
  stl=name.startswith('11'); fixture=HERE/('case-'+name+('.stldata' if stl else '.stepdata'))
  if stl:check_stl(fixture)
  with tempfile.TemporaryDirectory(prefix='look-reduced-',dir=h.BASE) as temp:
   temp=pathlib.Path(temp);source=temp/('case.stl' if stl else 'case.step');shutil.copyfile(fixture,source);data=temp/'data';data.mkdir();settings=dict(h.SETTINGS,Roots=[str(temp)]);settings['Edges']=not a.no_edges;(data/'settings.json').write_text(json.dumps(settings),encoding='utf8')
   tag='case-'+name+('-no-edges' if a.no_edges else '');dest=output/(tag+'.png');dest.unlink(missing_ok=True)
   if a.look_exe:
    cmd=[str(exe),'render',str(source),'--camera','orthographic','--resolution','512x512','--up-axis','z','--material-mode','source','--ambient','0.18','--light-intensity','1.2','--background','#ffffff00','--antialias','--ambient-occlusion','--output',str(dest)]
    if not a.no_edges:cmd+=['--edges']
    start=time.monotonic()
    try:
     proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=a.deadline,text=True,encoding='utf8',errors='replace');code=proc.returncode;timed=False;log=proc.stdout
    except subprocess.TimeoutExpired as error:code=None;timed=True;log='external timeout';print('Look timed out',file=sys.stderr)
    seconds=round(time.monotonic()-start,3)
   else:code,timed,seconds,log=h.run(exe,source,dest,data,a.deadline)
   ok=code==0 and not timed and dest.is_file();(output/(tag+'.log')).write_text(log,encoding='utf8');print(tag,'rendered' if ok else 'FAILED',seconds,'seconds',flush=True);success &= ok
 return 0 if success else 1
if __name__=='__main__':sys.exit(main())
