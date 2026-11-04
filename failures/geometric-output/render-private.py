"""Private end-to-end Look thumbnail regression probe (Windows only)."""
import argparse, ctypes, gzip, hashlib, json, os, pathlib, shutil, sqlite3, subprocess, sys, tempfile, time
from ctypes import wintypes as w
ROOT=pathlib.Path(__file__).resolve().parent
PRIVATE=ROOT.parent/'private'/'cases'
BASE=pathlib.Path(os.environ['LOCALAPPDATA'])/'StepThumbnail'/'private-probes'
SETTINGS={'Roots':[],'Exclude':[],'Renderer':'look','Transparent':True,'Background':'#ffffff','SourceColours':True,'AmbientOcclusion':True,'AOStrength':1.0,'AORadius':14.0,'Edges':True,'EdgeStrength':0.75,'EdgeWidth':1.0,'Antialias':True,'Ambient':0.18,'LightIntensity':1.2,'LightDirection':'-1,-2,-3','LightColour':'#ffffff','LightingPreset':'technical','ImportTimeoutSeconds':8}
class BASIC(ctypes.Structure):
 _fields_=[('PerProcessUserTimeLimit',ctypes.c_longlong),('PerJobUserTimeLimit',ctypes.c_longlong),('LimitFlags',w.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',w.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
class ACCOUNT(ctypes.Structure):
 _fields_=[('TotalUserTime',ctypes.c_longlong),('TotalKernelTime',ctypes.c_longlong),('ThisPeriodTotalUserTime',ctypes.c_longlong),('ThisPeriodTotalKernelTime',ctypes.c_longlong),('TotalPageFaultCount',w.DWORD),('TotalProcesses',w.DWORD),('ActiveProcesses',w.DWORD),('TotalTerminatedProcesses',w.DWORD)]
class IO(ctypes.Structure): _fields_=[(n,ctypes.c_ulonglong) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class EXT(ctypes.Structure): _fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
k=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll'); k.CreateJobObjectW.argtypes=[w.LPVOID,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE;k.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,w.LPVOID,w.DWORD];k.SetInformationJobObject.restype=w.BOOL;k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];k.AssignProcessToJobObject.restype=w.BOOL;k.CloseHandle.argtypes=[w.HANDLE];k.TerminateJobObject.argtypes=[w.HANDLE,w.UINT];k.TerminateJobObject.restype=w.BOOL;k.QueryInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,w.LPVOID,w.DWORD,w.LPVOID];k.QueryInformationJobObject.restype=w.BOOL;nt.NtResumeProcess.argtypes=[w.HANDLE];nt.NtResumeProcess.restype=ctypes.c_long

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(exe,source,out,data,deadline):
 job=k.CreateJobObjectW(None,None)
 if not job: raise ctypes.WinError(ctypes.get_last_error())
 info=EXT(); info.BasicLimitInformation.LimitFlags=0x2000
 if not k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info)): raise ctypes.WinError(ctypes.get_last_error())
 env=os.environ.copy();env['STEPTHUMBNAIL_DATA_DIR']=str(data)
 start=time.monotonic(); timed=False
 try:
  with tempfile.TemporaryFile(mode='w+b') as stream:
   child=subprocess.Popen([str(exe),'--render-test',str(source),str(out)],env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=0x4|0x08000000)
   try:
    if not k.AssignProcessToJobObject(job,w.HANDLE(int(child._handle))): raise ctypes.WinError(ctypes.get_last_error())
    if nt.NtResumeProcess(w.HANDLE(int(child._handle)))!=0: raise OSError('resume failed')
    try: code=child.wait(timeout=deadline)
    except subprocess.TimeoutExpired: timed=True;code=None
   finally:
    # Terminate the entire job and wait until every inherited handle closes.
    if not k.TerminateJobObject(job,1): raise ctypes.WinError(ctypes.get_last_error())
    child.wait()
    until=time.monotonic()+5
    while True:
     account=ACCOUNT()
     if not k.QueryInformationJobObject(job,1,ctypes.byref(account),ctypes.sizeof(account),None): raise ctypes.WinError(ctypes.get_last_error())
     if account.ActiveProcesses==0:break
     if time.monotonic()>=until:raise TimeoutError('job processes did not exit after termination')
     time.sleep(0.01)
    k.CloseHandle(job);job=None
   stream.seek(0);log=stream.read().decode('utf8',errors='replace')
  return code,timed,round(time.monotonic()-start,3),log
 finally:
  if job: k.CloseHandle(job)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exe',type=pathlib.Path,required=True);parser.add_argument('--case',action='append',help='neutral case id; repeat or omit for all');parser.add_argument('--deadline',type=float,default=10);parser.add_argument('--variant',choices=['normal','no-edges','no-ao','plain'],default='normal');args=parser.parse_args()
 if not 0<args.deadline<=10: parser.error('deadline must be in (0,10]')
 exe=args.exe.resolve(strict=True);cases=json.loads((PRIVATE/'manifest.json').read_text());wanted=set(args.case or [c['id'] for c in cases]);unknown=wanted-{c['id'] for c in cases}
 if unknown: parser.error('unknown case ids: '+','.join(sorted(unknown)))
 BASE.mkdir(parents=True,exist_ok=True);all_ok=True
 for c in cases:
  if c['id'] not in wanted: continue
  folder=PRIVATE/c['id'];archive=folder/'source.gz';cached=folder/'cached.png'
  assert sha(cached)==c['cached_png_sha256'], c['id']+' cached PNG hash mismatch'
  with tempfile.TemporaryDirectory(prefix='look-repro-',dir=BASE) as temp:
   work=pathlib.Path(temp);source=work/('source'+c['extension']); source.write_bytes(gzip.decompress(archive.read_bytes()))
   assert sha(source)==c['source_sha256'],c['id']+' source hash mismatch'
   data=work/'data';data.mkdir();settings=dict(SETTINGS, Roots=[str(work)]); settings['Edges']=args.variant not in ('no-edges','plain');settings['AmbientOcclusion']=args.variant not in ('no-ao','plain');(data/'settings.json').write_text(json.dumps(settings),encoding='utf8')
   output=work/'output.png';code,timed,seconds,log=run(exe,source,output,data,args.deadline)
   good=code==0 and output.is_file() and not timed; record={'case':c['id'],'exit':code,'timeout':timed,'seconds':seconds,'rendered':good,'cached_profile':c['profile']}
   db=data/'cache-v1'/'index.sqlite3'
   if db.exists():
    con=sqlite3.connect(str(db));rows=con.execute('select distinct profile from images').fetchall();con.close();record['rendered_profiles']=[r[0] for r in rows];record['profile_matches']=c['profile'] in record['rendered_profiles']
   if good:
    shutil.copyfile(output,folder/('rendered.png' if args.variant=='normal' else 'rendered-'+args.variant+'.png'));record['rendered_png_sha256']=sha(output);record['cached_png_sha256']=c['cached_png_sha256'];record['png_byte_match']=record['rendered_png_sha256']==record['cached_png_sha256']
    try:
     from PIL import Image,ImageChops,ImageStat
     a=Image.open(cached).convert('RGBA');b=Image.open(output).convert('RGBA');record['dimensions']=[a.size,b.size]
     if a.size==b.size:record['mean_absolute_channel_difference']=round(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/4,4)
    except ImportError:pass
   (folder/('result.json' if args.variant=='normal' else 'result-'+args.variant+'.json')).write_text(json.dumps(record,indent=2),encoding='utf8');(folder/('render.log' if args.variant=='normal' else 'render-'+args.variant+'.log')).write_text(log,encoding='utf8')
   print(json.dumps(record),flush=True);all_ok &= good and (args.variant!='normal' or (record.get('profile_matches',False) and record.get('png_byte_match',False)))
 return 0 if all_ok else 1
if __name__=='__main__':sys.exit(main())
