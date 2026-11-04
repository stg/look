"""Check true support and endpoint positions for two unclamped rational splines.
Requires numpy and scipy; evaluates with extrapolation explicitly disabled.
"""
from pathlib import Path
import re
import numpy as np
from scipy.interpolate import BSpline
HERE = Path(__file__).resolve().parent
for case, edge, curve in [(1, 815, 818), (2, 333, 334)]:
    text = (HERE / f'case-{case:02d}.stepdata').read_text(encoding='ascii')
    es = {int(n): value for n, value in re.findall('#(\\d+)\\s*=\\s*(.*?);', text, re.S)}
    m = re.search('B_SPLINE_CURVE\\s*\\(\\s*(\\d+)\\s*,\\s*\\((.*?)\\).*?B_SPLINE_CURVE_WITH_KNOTS\\s*\\(\\s*\\((.*?)\\)\\s*,\\s*\\((.*?)\\).*?RATIONAL_B_SPLINE_CURVE\\s*\\(\\s*\\((.*?)\\)', es[curve], re.S)
    degree = int(m[1])
    ids = [int(x) for x in re.findall('#(\\d+)', m[2])]
    mult = [int(x) for x in m[3].split(',')]
    knots = [float(x) for x in m[4].split(',')]
    weights = np.array([float(x) for x in m[5].split(',')])
    expanded = np.repeat(knots, mult)

    def point(n):
        return np.array([float(x) for x in re.search("CARTESIAN_POINT\\s*\\(\\s*''\\s*,\\s*\\((.*?)\\)\\s*\\)", es[n], re.S)[1].split(',')])
    points = np.array([point(n) for n in ids])
    vertex = int(re.search('#(\\d+)', es[edge])[1])
    target = point(int(re.search('#(\\d+)', es[vertex])[1]))
    curve = BSpline(expanded, np.c_[points * weights[:, None], weights], degree, extrapolate=False)
    support = (expanded[degree], expanded[-degree - 1])
    full = (knots[0], knots[-1])
    dist = []
    for t in support:
        homogeneous = curve(t)
        dist.append(float(np.linalg.norm(homogeneous[:3] / homogeneous[3] - target)))
    assert all((np.isnan(curve(t)).all() for t in full)) and max(dist) < 1e-08
    print(f'case-{case:02d}: degree={degree}; full knots={full}; valid support={support}; endpoint distances={dist}; full-knot evaluations NaN')
