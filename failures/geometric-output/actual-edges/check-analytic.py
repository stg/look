"""Check analytic endpoint distances for source circle and hyperbola edges.
Requires numpy and scipy. Hyperbola closest-point search is numerical over
parameter [-5, 5], subdivided into 40 intervals; it is not a formal proof.
"""
from pathlib import Path
import re
import numpy as np
from scipy.optimize import minimize_scalar
HERE=Path(__file__).resolve().parent
def entities(case):return {int(n):s for n,s in re.findall(r'#(\d+)\s*=\s*(.*?);',(HERE/f'case-{case:02d}.stepdata').read_text(encoding='ascii'),re.S)}
def vec(es,n):return np.array([float(x) for x in re.search(r"\(([-+0-9.Ee,\s]+)\)\s*\)",es[n],re.S)[1].split(',')])
e=entities(6);center=vec(e,118);axis=vec(e,119);axis/=np.linalg.norm(axis);out=[]
for n in [5303,5307]:
 v=vec(e,n)-center;along=float(np.dot(v,axis));radius=np.linalg.norm(v-along*axis);out.append(float(np.hypot(radius-.0625,along)))
print('case-06: circle endpoint distances in source inches',out,'declared closure uncertainty',.001);assert max(out)<.001

e=entities(7);origin=vec(e,578);z=vec(e,579);x=vec(e,580);z/=np.linalg.norm(z);x-=z*np.dot(z,x);x/=np.linalg.norm(x);y=np.cross(z,x);a=8.751993625783;b=2.704311113925
distances=[]
for n in [97,575]:
 p=vec(e,n);f=lambda t:float(np.linalg.norm(origin+a*np.cosh(t)*x+b*np.sinh(t)*y-p));best=min(minimize_scalar(f,bounds=(lo,hi),method='bounded',options={'xatol':1e-14}).fun for lo,hi in zip(np.linspace(-5,5,41)[:-1],np.linspace(-5,5,41)[1:]));print('case-07: endpoint',n,'numerical hyperbola distance in mm',best,'declared uncertainty',2e-5);distances.append(best)
assert distances[0]>2e-5 and distances[1]<2e-5
