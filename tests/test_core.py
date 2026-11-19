import math

import pytest

import atlaskit

def _raises(fn, exc=ValueError):
    try:
        fn()
    except exc:
        return True
    return False


def _pt_seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def _packer(w=64, h=64, rot=False):
    return atlaskit.Packer(w, h, rot)


def _no_overlap():
    p = _packer()
    for i, size in enumerate([(16, 16)] * 8):
        p.add(str(i), size)
    rs = [r[:4] for r in p.rects()]
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            a, b = rs[i], rs[j]
            if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                return False
    return True


def _inside():
    p = _packer()
    for i in range(8):
        p.add(str(i), (16, 16))
    return all(r[0] + r[2] <= 64 and r[1] + r[3] <= 64 for r in p.rects())


def _fill():
    p = _packer()
    for i, size in enumerate([(16, 16)] * 12):
        p.add(str(i), size)
    return p.stats()["fill"] >= 0.70


def _fill_mixed():
    p = _packer(80, 80)
    sizes = [(20, 20), (16, 12), (24, 8), (8, 8), (30, 10), (12, 20), (10, 10), (18, 14)]
    for i, size in enumerate(sizes):
        p.add(str(i), size)
    return p.stats()["fill"] >= 0.60


def _overflow_rollback():
    p = _packer(20, 20)
    p.add("a", (10, 10))
    before = p.rects()
    ok = _raises(lambda: p.add("b", (15, 10)))
    return ok and p.rects() == before


def _dup():
    p = _packer()
    p.add("a", (5, 5))
    return _raises(lambda: p.add("a", (5, 5)))


def _too_big():
    return _raises(lambda: _packer(10, 10).add("a", (20, 20)))


def _negative():
    return _raises(lambda: _packer().add("a", (-4, 4)))


def _multipage():
    p = _packer(16, 16)
    p.add("a", (16, 16))
    p.next_page()
    p.add("b", (16, 16))
    return p.stats()["pages"] == 2


def _uv_page():
    p = _packer(16, 16)
    p.add("a", (16, 16))
    p.next_page()
    p.add("b", (8, 8))
    u0, v0, u1, v1 = p.uv("b")
    return abs(u1 - 0.5) < 1e-9 and abs(v0 - 1.0) < 1e-9


def _rotate():
    p = atlaskit.Packer(20, 10, allow_rotate=True)
    p.add("a", (10, 20))
    r = p.rects()[0]
    return r[0] + r[2] <= 20 and r[1] + r[3] <= 10


def _deterministic():
    def run():
        p = _packer()
        for rid, size in [("a", (10, 10)), ("b", (12, 8)), ("c", (6, 6))]:
            p.add(rid, size)
        return p.rects()
    return run() == run()


def _rollback_empty():
    return _raises(lambda: _packer().rollback())

CASES = [
        ("no_overlap", lambda: _no_overlap()),
        ("inside", lambda: _inside()),
        ("fill", lambda: _fill()),
        ("fill_mixed", lambda: _fill_mixed()),
        ("overflow_rollback", lambda: _overflow_rollback()),
        ("dup", lambda: _dup()),
        ("too_big", lambda: _too_big()),
        ("negative", lambda: _negative()),
        ("multipage", lambda: _multipage()),
        ("uv_page", lambda: _uv_page()),
        ("rotate", lambda: _rotate()),
        ("deterministic", lambda: _deterministic()),
        ("rollback_empty", lambda: _rollback_empty()),
        ("stats_count", lambda: (lambda p: (p.add("a", (4, 4)), p.stats()["count"] == 1)[1])(_packer())),
        ("pages_initial", lambda: _packer().stats()["pages"] >= 1),
    ]


@pytest.mark.parametrize("name,check", CASES, ids=[c[0] for c in CASES])
def test_spec(name, check):
    assert check() is True
