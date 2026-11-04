"""Numerically search every knot span of the two actual quartic edge curves.

Requires numpy and scipy. This is numerical evidence, not a formal global
minimum certificate: bounded minimization is applied to each knot span and
all span endpoints are also tested.
"""
from pathlib import Path
import re
import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import minimize_scalar
HERE = Path(__file__).resolve().parent

def check(case, edge, uncertainty):
    text = (HERE / f'case-{case:02d}.stepdata').read_text(encoding='ascii')
    entities = {int(n): value for n, value in re.findall('#(\\d+)\\s*=\\s*(.*?);', text, re.S)}
    refs = [int(n) for n in re.findall('#(\\d+)', entities[edge])]

    def point(n):
        match = re.search("CARTESIAN_POINT\\s*\\(\\s*''\\s*,\\s*\\((.*?)\\)\\s*\\)", entities[n], re.S)
        return np.array([float(v) for v in match.group(1).split(',')])
    endpoints = [point(int(re.search('#(\\d+)', entities[n]).group(1))) for n in refs[:2]]
    pattern = "B_SPLINE_CURVE_WITH_KNOTS\\s*\\(\\s*''\\s*,\\s*(\\d+)\\s*,\\s*\\((.*?)\\)\\s*,\\s*\\.\\w+\\.\\s*,\\s*\\.\\w+\\.\\s*,\\s*\\.\\w+\\.\\s*,\\s*\\((.*?)\\)\\s*,\\s*\\((.*?)\\)"
    m = re.match(pattern, entities[refs[2]], re.S)
    degree = int(m.group(1))
    ids = [int(x) for x in re.findall('#(\\d+)', m.group(2))]
    mult = [int(x) for x in m.group(3).split(',')]
    knots = [float(x) for x in m.group(4).split(',')]
    spline = BSpline(np.repeat(knots, mult), np.array([point(n) for n in ids]), degree)
    minima = []
    for endpoint in endpoints:
        best = (float('inf'), None)
        for lo, hi in zip(knots, knots[1:]):
            f = lambda u: float(np.sum((spline(u) - endpoint) ** 2))
            result = minimize_scalar(f, bounds=(lo, hi), method='bounded', options={'xatol': 1e-14})
            best = min(best, (result.fun, result.x), (f(lo), lo), (f(hi), hi))
        minima.append((float(np.sqrt(best[0])), best[1]))
    full_end = float(np.linalg.norm(spline(knots[-1]) - endpoints[1]))
    print(f'case-{case:02d}: degree {degree}, {len(ids)} controls; nearest distances/parameters {minima}; full-curve end residual {full_end:g} mm; source uncertainty {uncertainty:g} mm')
    return minima[1][0]
r4 = check(4, 21, 5e-06)
r5 = check(5, 586, 1e-07)
assert r4 > 5e-06 and r5 < 1e-07, 'source-distance observation changed'
