"""Browser tests for RVR Sim Lab. Run: python3 tests/test_sim.py

Needs Playwright with Chromium. The Python cases also run through real CPython, so the sim's
translator is checked against the language itself rather than against expected strings.
"""
import asyncio, contextlib, functools, http.server, io, sys, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = str(Path(__file__).resolve().parent.parent / "rvr-sim-lab")
FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
    else:
        FAILS.append(name)
        print(f"FAIL {name}: {detail}")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
BASE = f"http://127.0.0.1:{server.server_address[1]}"
threading.Thread(target=server.serve_forever, daemon=True).start()


def open_sim(browser, **kw):
    page = browser.new_context(**kw).new_page()
    page.errs, page.reqs = [], []
    page.on("pageerror", lambda e: page.errs.append(str(e)[:200]))
    page.on("console", lambda m: page.errs.append(m.text[:200]) if m.type in ("error", "warning") else None)
    page.on("request", lambda r: page.reqs.append(r.url))
    page.goto(BASE + "/rvr-sim-lab.html", wait_until="networkidle")
    page.wait_for_timeout(200)
    return page


def run(page, timeout=40):
    page.click('[data-speed="4"]')
    page.click("#runBtn")
    end = time.time() + timeout
    while time.time() < end:
        page.wait_for_timeout(50)
        if page.is_disabled("#stopBtn"):
            return page.inner_text("#result")
    return "TIMEOUT"


def text_run(page, lang, src, timeout=40):
    page.click("#langPy" if lang == "py" else "#langJs")
    page.click("#modeText")
    page.fill("#codeEdit", src)
    return run(page, timeout)


def output(page):
    lines = page.inner_text("#console").split("\n")
    return [l for l in lines if l and not l.startswith(("▶", "■"))]


def mission(page, n):
    page.click(f"#levels button:nth-child({n})")
    page.wait_for_timeout(80)


# Each body runs inside start_program. CPython's printed output must match the sim's, except for
# `5` vs `5.0`: JavaScript has one number type, so whole-number floats print without the .0.
DIFF = """
a, b = 1, 2
print(a, b)
---
a = 1
b = 2
a, b = b, a
print(a, b)
---
pts = [(0, 10), (90, 20)]
print(pts)
print(pts[1][0])
---
for h, s in [(0, 10), (90, 20)]:
    print(h, s)
---
def f():
    return 1, 2
print(f())
a, b = f()
print(a + b)
---
x = 50
print(0 < x < 10, 0 < x < 100, 1 < 2 > 1)
---
print([0] * 4, 2 * [1, 2], (1, 2) * 2, [1] + [2], (1,) + (2,))
---
print('ab' * 3, 'a' + 'b', 3 * 'x')
---
l = [1, 2, 3]
print(l[-1], l[-3], l[0:2], l[1:], l[:1], l[::-1], l[::2], l[-2:])
s = 'hello'
print(s[0], s[-1], s[1:3], s[::-1])
---
print((0 - 90) % 360, 7 % -3, -7 % 3, 7 % 3, 5.5 % 2)
print(7 // 2, -7 // 2, 7 // -2)
x = 7
x //= 2
print(x)
---
x = 2
print(-x ** 2, 2 ** 3, 2 ** -1, (-2) ** 2, 2 ** 3 ** 2)
---
x = 1.234
print(f'{x:.1f}', f'{x:.2f}', f'{3:03d}', f'{5:>4}|', f'{5:<4}|', f'{5:^5}|', f'{1234567:,}', f'{0.5:.0%}')
n = 'bot'
print(f'{n!r} {n} {{x}} {[1, 2][0]} {1 + 2}', f"{'k'}")
---
print('a', end='')
print('b')
print('a', 'b', sep='-')
print('x', 'y', sep='', end='!\\n')
---
l = [10, 9, 1]
l.sort()
print(l)
l.sort(reverse=True)
print(l)
print(sorted([3, 1, 2]), sorted([3, 1, 2], reverse=True), sorted('cab'))
---
print(2 in [1, 2], 3 in [1, 2], 3 not in [1, 2], 'a' in 'cat', 'k' in {'k': 1}, 'z' not in {'k': 1})
---
print(sum([1, 2, 3]), min(3, 1), max([3, 1]), abs(-2), len('abc'), len([1]), len({'a': 1}))
---
for i, v in enumerate(['a', 'b']):
    print(i, v)
for a, b in zip([1, 2], 'xy'):
    print(a, b)
print(list(range(3)), list('ab'), tuple([1, 2]), any([0, 1]), all([0, 1]), bool([]), bool('a'))
print(list(reversed([1, 2])), int('12'), int(3.9), int(-3.9), str(5) + 'x', float('1.5'))
---
d = {'a': 1}
d['b'] = 2
for k, v in d.items():
    print(k, v)
for k in d:
    print(k)
print(d, d.get('a'), d.get('z'), d.get('z', 9), list(d.keys()), list(d.values()), len(d))
---
def f():
    pass
print(f() is None, f() is not None, f() == None, None is None)
---
print(', '.join(['a', 'b']), 'a b'.split(), 'a,b'.split(','), ' x '.strip(), 'Hi'.upper(), 'Hi'.lower())
print('aXbX'.replace('X', '-'), 'hello'.startswith('he'), 'hello'.endswith('x'), 'hello'.find('l'), 'hello'.count('l'), '{} {}'.format(1, 'a'))
---
l = []
if l:
    print('full')
else:
    print('empty')
if not l:
    print('still empty')
s = ''
print('yes' if s else 'no', 'yes' if 'x' else 'no', 'yes' if {} else 'no', 'yes' if 0 else 'no')
---
print(0 or 'x', 1 or 'x', 0 and 'x', 1 and 'x', [] or [1], None or 0 or 3, not 0, not [1])
---
x = 5
y = 'big' if x > 3 else 'small'
print(y, 1 if x > 9 else 2 if x > 4 else 3)
---
def add(a, b=2, c=3):
    return a + b + c
print(add(1), add(1, 1), add(1, c=0), add(a=1, b=0, c=0))
---
n = 0
while n < 3:
    n += 1
    if n == 2:
        continue
    print(n)
for i in range(5):
    if i == 2:
        break
print(i)
---
for i in range(10, 0, -3):
    print(i)
---
l = [1, 2, 3]
l.append(4)
l.insert(0, 0)
print(l.pop(), l.pop(0), l, l.index(2), l.count(9))
l.remove(2)
l.extend([7, 8])
l.reverse()
print(l)
l[0] = 99
l[-1] += 1
print(l)
m = l
m += [5]
print(l)
---
d = {'n': 1}
d['n'] += 1
print(d['n'])
a = b = 3
print(a, b)
(c, e) = (1, 2)
[f, g] = [3, 4]
print(c, e, f, g)
---
if(1 > 0):
    print('parens ok')
while(False):
    pass
---
print(1 == 1.0, True == 1, [1, 2] == [1, 2], (1, 2) == [1, 2], {'a': 1} == {'a': 1}, 'a' != 'b', [1, 2] < [1, 3], 'a' < 'b')
---
print(round(2.5), round(3.5), round(2.567, 2), round(7), abs(-1.5))
---
import math
print(math.sqrt(16) == 4, math.floor(2.5), math.ceil(2.1), round(math.pi, 2), math.hypot(3, 4) == 5)
---
from math import sqrt, floor as fl
import math as m
print(sqrt(16) == 4, fl(2.9), m.ceil(1.2))
---
import random
print(1 <= random.randint(1, 6) <= 6, random.choice([7]), 0 <= random.random() < 1)
---
print('n=' + str(1), "it's", 'say "hi"', ['a', "it's"], {'k': 'v'}, (1,), (), [])
print(True, False, None, 1.5, -2, 'x' 'y')
---
def outer():
    total = 0
    def inner():
        nonlocal total
        total += 1
    inner()
    inner()
    return total
print(outer())
---
def fact(n):
    return 1 if n < 2 else n * fact(n - 1)
print(fact(5))
---
go = len
print(go('abc'))
def twice(f, x):
    return f(f(x))
def inc(x):
    return x + 1
print(twice(inc, 1))
"""
# Programs CPython rejects or that raise. The sim must stop with an error instead of carrying on.
MUST_ERROR = [
    ("str + int", "print('n=' + 1)\n"),
    ("index past end", "print([1, 2][5])\n"),
    ("missing key", "print({'a': 1}['b'])\n"),
    ("divide by zero", "print(1 / 0)\n"),
    ("mod by zero", "print(1 % 0)\n"),
    ("unbound None math", "h = None\nh = h + 90\n"),
    ("str - int", "print('a' - 1)\n"),
    ("compare str int", "print('a' < 1)\n"),
    ("too many unpack", "a, b = 1, 2, 3\n"),
    ("tuple assign", "t = (1, 2)\nt[0] = 5\n"),
    ("float index", "print([1][0.5])\n"),
    ("int of text", "print(int('abc'))\n"),
    ("wrong arg count", "def f(a):\n    pass\nf(1, 2)\n"),
    ("missing arg", "def f(a):\n    pass\nf()\n"),
    ("unknown keyword", "def f(a):\n    pass\nf(b=1)\n"),
]
# Fine in Python syntax but won't work on the robot: these must be caught before the program runs.
REJECTED = [
    ("async call with no await", "    async def f():\n        pass\n    f()\n", "await"),
    ("await in plain def", "    def f():\n        await delay(0.01)\n    f()\n", "async def"),
    ("await a plain def", "    def f():\n        pass\n    await f()\n", "without await"),
    ("roll with no await", "    roll(0, 50, 1)\n", "await"),
    ("await set_speed", "    await set_speed(50)\n", "doesn't use await"),
    ("list comprehension", "    x = [i for i in range(3)]\n", "comprehension"),
    ("generator", "    print(sum(i for i in range(3)))\n", "comprehension"),
    ("set literal", "    x = {1, 2}\n", "Sets"),
    ("slice assign", "    l = [1]\n    l[0:1] = [2]\n", "slice"),
    ("star call", "    print(*[1, 2])\n", "*"),
    ("single = in if", "    if 1 = 2:\n        pass\n", "=="),
    ("lambda", "    f = lambda x: x\n", "lambda"),
    ("class", "    class A:\n        pass\n", "Classes"),
    ("del", "    l = [1]\n    del l[0]\n", "del"),
    ("import time", "    import time\n", "delay"),
    ("unknown module", "    import os\n", "isn't available"),
]


def cpython_output(body):
    stub = "async def delay(s):\n    pass\n"
    src = stub + "async def start_program():\n" + "".join("    " + l + "\n" for l in body.split("\n"))
    out = io.StringIO()
    ns = {}
    with contextlib.redirect_stdout(out):
        exec(compile(src, "case", "exec"), ns)
        asyncio.run(ns["start_program"]())
    return out.getvalue().rstrip("\n")


def norm(s):
    # the one documented difference: whole floats print as 5, not 5.0
    import re
    return re.sub(r"(?<![\w.'])(-?\d+)\.0(?![\d])", r"\1", s)


CASES = [(c, norm(cpython_output(c))) for c in DIFF.strip().split("\n---\n")]   # before Playwright starts its event loop

with sync_playwright() as pw:
    b = pw.chromium.launch()

    # --- boot
    p = open_sim(b)
    ext = [u for u in p.reqs if not u.startswith(BASE)]
    check("no third-party requests", not ext, ext)
    check("clean boot", not p.errs, p.errs)
    check("blockly loaded", p.evaluate("!!document.querySelector('.blocklyToolboxDiv')"))

    # --- every mission solved in both languages, blocks starters run
    SOL = {
        2: ("async function startProgram(){ await roll(0,80,1.7); await roll(90,80,1.7); await roll(180,80,1.7); await roll(270,80,1.7); }",
            "async def start_program():\n    for h in [0, 90, 180, 270]:\n        await roll(h, 80, 1.7)\n"),
        3: ("async function startProgram(){ await roll(0,100,2.4); await roll(90,100,1.8); await roll(180,100,2.3); await roll(90,100,1.9); }",
            "async def start_program():\n    await roll(0, 100, 2.4)\n    await roll(90, 100, 1.8)\n    await roll(180, 100, 2.3)\n    await roll(90, 100, 1.9)\n"),
        4: ("async function startProgram(){ setSpeed(60); while(!isColor(getColor(),'red')){ await delay(0.05);} stopRoll(); }",
            "async def start_program():\n    set_speed(60)\n    while not is_color(get_color(), 'red'):\n        await delay(0.05)\n    stop_roll()\n"),
    }
    p = open_sim(b)
    for n, (js, py) in SOL.items():
        mission(p, n)
        for lang, src in (("js", js), ("py", py)):
            r = text_run(p, lang, src)
            check(f"mission {n} {lang}", "complete" in r.lower() or "Parked with zero" in r, r)
    p = open_sim(b)
    for lang in ("js", "py"):
        p.click("#langPy" if lang == "py" else "#langJs")
        for n in range(1, 5):
            mission(p, n)
            r = run(p)
            check(f"starter {n} {lang}", r != "TIMEOUT" and "error" not in r and "didn't start" not in r, r)
    mission(p, 1)
    r = run(p)
    check("free roam earns its check", "done" in p.get_attribute("#levels button:nth-child(1)", "class"), r)

    # --- Python vs CPython
    p = open_sim(b)
    p.click("#langPy")
    p.click("#modeText")
    for case, want in CASES:
        src = "async def start_program():\n" + "".join("    " + l + "\n" for l in case.split("\n"))
        p.fill("#codeEdit", src)
        run(p, 15)
        got = norm("\n".join(output(p)))
        check("cpython: " + case.split("\n")[0][:50], got == want, f"\n  want {want!r}\n  got  {got!r}")
    for name, body in MUST_ERROR:
        src = "async def start_program():\n" + "".join("    " + l + "\n" for l in body.strip().split("\n"))
        p.fill("#codeEdit", src)
        r = run(p, 15)
        check("errors: " + name, "error" in r or "didn't start" in r, (r, output(p)))
    for name, body, needle in REJECTED:
        p.fill("#codeEdit", "async def start_program():\n" + body)
        r = run(p, 15)
        msg = " ".join(output(p))
        check("rejected: " + name, "didn't start" in r and needle in msg, (r, msg))
    p.fill("#codeEdit", "def start_program():\n    pass\n")
    check("rejected: plain start_program", "didn't start" in run(p, 10))
    p.fill("#codeEdit", "async def go():\n    await delay(0.01)\n    print('ran')\nasync def start_program():\n    await go()\n    print('done')\n")
    run(p, 10)
    check("async def + await works", output(p) == ["ran", "done"], output(p))

    # --- Python mission helper pasted back in, and the copied JS helper too
    p = open_sim(b)
    p.context.grant_permissions(["clipboard-read", "clipboard-write"])
    mission(p, 4)
    for lang, src in (("js", SOL[4][0]), ("py", SOL[4][1])):
        p.click("#langPy" if lang == "py" else "#langJs")
        p.click("#modeText")
        p.fill("#codeEdit", src)
        p.click("#copyBtn")
        p.wait_for_timeout(100)
        copied = p.evaluate("navigator.clipboard.readText()")
        check(f"helper added {lang}", "isColor(c, name)" in copied or "is_color(c, name)" in copied)
        p.fill("#codeEdit", copied)
        r = run(p)
        check(f"copied helper runs in the sim {lang}", "Mission complete" in r, (r, output(p)))

    # --- JS loop handling
    p = open_sim(b)
    r = text_run(p, "js", "function sum(n){ let s=0; for(let i=0;i<n;i++){ s+=i; } return s; }\nasync function startProgram(){ await delay(0.05); }\n")
    check("loop in plain function", "error" not in r and "didn't start" not in r, r)
    r = text_run(p, "js", "async function startProgram(){ [1,2].forEach(x => { let i = 0; while (i < 3) { i++; } }); }\n")
    check("loop in arrow function", "didn't start" not in r, r)
    r = text_run(p, "js", "let delay = 1;\nasync function startProgram(){ }\n")
    check("top-level name matches a command", "didn't start" not in r, r)

    p = open_sim(b)
    p.click("#modeText")
    p.fill("#codeEdit", "async function startProgram(){ let x = 0; while (true) x++; }")
    p.click("#runBtn")
    p.wait_for_timeout(600)
    check("page alive during endless loop", p.evaluate("1 + 1") == 2)
    p.click("#stopBtn")
    p.wait_for_timeout(200)
    check("Stop ends endless loop", "Stopped" in p.inner_text("#result"), p.inner_text("#result"))
    p.fill("#codeEdit", "function spin2(){ while (true) { } }\nasync function startProgram(){ spin2(); }")
    p.click("#runBtn")
    p.wait_for_timeout(4500)
    check("endless loop in plain function is stopped", "error" in p.inner_text("#result"), p.inner_text("#result"))
    t0 = time.time()
    r = text_run(p, "js", "async function startProgram(){ let s=0; for(let i=0;i<1000;i++){ s+=i; } }")
    check("math loop costs no sim time", p.inner_text("#tTime") == "0.0 s", p.inner_text("#tTime"))
    r = text_run(p, "py", "async def start_program():\n    s = 0\n    for i in range(1000):\n        s += i\n    print(s)\n")
    check("python math loop costs no sim time", p.inner_text("#tTime") == "0.0 s" and output(p) == ["499500"], (p.inner_text("#tTime"), output(p)))
    r = text_run(p, "js", "async function startProgram(){ const t = /[\"']/; setSpeed(50); while (getElapsedTime() < 1) { } stopRoll(); }")
    check("sensor poll loop advances time", "1.0 s" in p.inner_text("#tTime") and "0, " in p.inner_text("#tLoc"), (r, p.inner_text("#tTime"), p.inner_text("#tLoc")))

    # --- negative speed
    p = open_sim(b)
    r = text_run(p, "js", "async function startProgram(){ await roll(0, 100, 1); await roll(0, -100, 1); }")
    check("reverse returns to start", p.inner_text("#tLoc") == "0, 0", p.inner_text("#tLoc"))
    text_run(p, "js", "async function startProgram(){ await roll(0, 100, 2); setSpeed(-100); await delay(0.5); }")
    check("setSpeed negative backs up", p.inner_text("#tLoc") == "0, 88", p.inner_text("#tLoc"))
    text_run(p, "js", "async function startProgram(){ await roll(0, 100, 1); stopRoll(90); await delay(0.5); }")
    check("stopRoll(heading) turns", p.inner_text("#tHeading") == "90°", p.inner_text("#tHeading"))
    text_run(p, "py", "async def start_program():\n    print(get_color('red'), get_color()['g'])\n")
    check("get_color channel", output(p) == ["34 36"], output(p))

    # --- text survives
    p = open_sim(b)
    p.click("#modeText")
    p.wait_for_timeout(50)
    untouched = p.input_value("#codeEdit")
    check("text starts from blocks", "startProgram" in untouched)
    p.click("#modeBlocks")
    p.evaluate("""() => { const w = Blockly.getMainWorkspace(); const s = w.getBlocksByType('sphero_start')[0]; let b = s.getInputTargetBlock('DO'); while (b.getNextBlock()) b = b.getNextBlock(); const n = w.newBlock('sphero_stop'); n.initSvg(); n.render(); b.nextConnection.connect(n.previousConnection); }""")
    p.wait_for_timeout(100)
    p.click("#modeText")
    p.wait_for_timeout(50)
    check("untouched text follows blocks", "stopRoll" in p.input_value("#codeEdit"))
    p.fill("#codeEdit", "// MINE\n")
    p.click("#modeBlocks"); p.wait_for_timeout(50); p.click("#modeText"); p.wait_for_timeout(50)
    check("typed text survives toggle", "MINE" in p.input_value("#codeEdit"))
    p.reload(wait_until="networkidle"); p.wait_for_timeout(200)
    check("typed text survives reload", "MINE" in p.input_value("#codeEdit"), p.input_value("#codeEdit"))
    p.click("#langPy"); p.wait_for_timeout(50); p.click("#langJs"); p.wait_for_timeout(50)
    check("typed text survives language switch", "MINE" in p.input_value("#codeEdit"))
    mission(p, 2); mission(p, 1)
    check("typed text survives mission switch", "MINE" in p.input_value("#codeEdit"))
    p.once("dialog", lambda d: d.dismiss())
    p.click("#rebuildBtn"); p.wait_for_timeout(50)
    check("rebuild can be cancelled", "MINE" in p.input_value("#codeEdit"))
    p.once("dialog", lambda d: d.accept())
    p.click("#rebuildBtn"); p.wait_for_timeout(50)
    check("rebuild replaces on confirm", "MINE" not in p.input_value("#codeEdit") and "startProgram" in p.input_value("#codeEdit"))

    # --- blocks variables in both languages (mission 2 hint, including "change by")
    def n_(v): return {"shadow": {"type": "math_number", "fields": {"NUM": v}}}
    roll = {"type": "sphero_roll", "inputs": {"HEADING": {"block": {"type": "variables_get", "fields": {"VAR": {"id": "h1"}}}}, "SPEED": n_(80), "DURATION": n_(1.7)},
            "next": {"block": {"type": "math_change", "fields": {"VAR": {"id": "h1"}}, "inputs": {"DELTA": n_(90)}}}}
    init = {"type": "variables_set", "fields": {"VAR": {"id": "h1"}}, "inputs": {"VALUE": n_(0)}, "next": {"block": {"type": "controls_repeat_ext", "inputs": {"TIMES": n_(4), "DO": {"block": roll}}}}}
    ws = {"variables": [{"name": "h", "id": "h1"}], "blocks": {"languageVersion": 0, "blocks": [{"type": "sphero_start", "x": 24, "y": 24, "deletable": False, "inputs": {"DO": {"block": init}}}]}}
    for lang in ("js", "py"):
        p = open_sim(b)
        mission(p, 2)
        p.click("#langPy" if lang == "py" else "#langJs")
        p.evaluate("ws => Blockly.serialization.workspaces.load(ws, Blockly.getMainWorkspace())", ws)
        p.wait_for_timeout(100)
        r = run(p)
        check(f"change-by block {lang}", "Mission complete" in r, (r, output(p)))
        if lang == "py":
            check("change-by python is plain", "h = h + 90" in p.inner_text("#codeView"), p.inner_text("#codeView"))

    # --- calibration
    p = open_sim(b)
    p.click("#calib summary")
    check("default top speed", p.inner_text("#calOut") == "150 cm/s", p.inner_text("#calOut"))
    p.fill("#calDist", "160")
    p.click("#calApply")
    check("measured distance sets speed", p.inner_text("#calOut") == "204 cm/s", p.inner_text("#calOut"))
    mission(p, 3)
    check("hint follows calibration", "about 80 cm" in p.text_content("#mHint"), p.text_content("#mHint"))
    mission(p, 2)
    check("square hint follows calibration", "1.3 seconds" in p.text_content("#mHint"), p.text_content("#mHint"))
    r = text_run(p, "js", "async function startProgram(){ await roll(0,80,1.3); await roll(90,80,1.3); await roll(180,80,1.3); await roll(270,80,1.3); }")
    check("hint's numbers still solve it", "Mission complete" in r, r)
    mission(p, 1)
    text_run(p, "js", "async function startProgram(){ await roll(0, 100, 1); }")   # 2 s would hit the top wall
    check("sim drives measured distance", p.inner_text("#tLoc") == "0, 80", p.inner_text("#tLoc"))
    p.reload(wait_until="networkidle"); p.wait_for_timeout(200)
    check("calibration survives reload", p.text_content("#calOut") == "204 cm/s" and "204" in p.text_content("#calBadge"), p.text_content("#calOut"))
    guide = p.context.new_page()
    guide.goto(BASE + "/rvr-sim-lab-guide.html", wait_until="networkidle")
    check("guide reads calibration", guide.inner_text("#cms") == "80" and "204" in guide.inner_text("#match"), guide.inner_text("#cms"))
    p.click("#calib summary")
    p.click("#calReset")
    guide.wait_for_timeout(150)
    check("guide updates live", guide.inner_text("#cms") == "59", guide.inner_text("#cms"))
    p.fill("#calDist", "5000")
    p.click("#calApply")
    check("silly distance refused", p.inner_text("#calOut") == "150 cm/s" and "doesn't look right" in p.inner_text("#calNote"), p.inner_text("#calNote"))
    p.context.grant_permissions(["clipboard-read", "clipboard-write"])
    p.click("#calCopy"); p.wait_for_timeout(100)
    check("speed test copied", "roll(0, 100, 2)" in p.evaluate("navigator.clipboard.readText()"))
    for lang in ("js", "py"):
        p.click("#langPy" if lang == "py" else "#langJs")
        p.click("#colorCopy"); p.wait_for_timeout(100)
        code = p.evaluate("navigator.clipboard.readText()")
        p.click("#modeText")
        p.fill("#codeEdit", code)
        p.click("#runBtn")
        p.wait_for_timeout(300)
        p.click("#stopBtn")
        check(f"color test runs in the sim {lang}", "problem" not in " ".join(output(p)) and "Error" not in " ".join(output(p)), output(p))

    # --- colors: sim tiles and off-white-balance readings a real sensor might give
    p = open_sim(b)
    p.click("#modeText")
    cases = {"{r:230,g:60,b:52}": "red", "{r:242,g:138,b:36}": "orange", "{r:244,g:200,b:48}": "yellow", "{r:46,g:165,b:90}": "green", "{r:44,g:110,b:220}": "blue",
             "{r:140,g:84,b:214}": "purple", "{r:255,g:255,b:255}": "white", "{r:150,g:40,b:45}": "red", "{r:60,g:120,b:70}": "green", "{r:40,g:60,b:130}": "blue", "{r:34,g:36,b:38}": "none", "{r:120,g:120,b:125}": "none"}
    src = "async function startProgram(){ const names=['red','orange','yellow','green','blue','purple','white']; const out=[]; for (const c of [" + ",".join(cases) + "]) { const hit = names.filter(n => isColor(c, n)); out.push(hit[0] || 'none'); } await speak(out.join(' ')); }"
    p.fill("#codeEdit", src)
    run(p)
    got = " ".join(output(p)).replace("Robot says: ", "").split()
    check("hue colors", got == list(cases.values()), got)

    # --- CSP from the README
    CSP = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'"
    p = b.new_context().new_page()
    errs = []
    p.on("console", lambda m: errs.append(m.text[:140]) if m.type == "error" else None)
    p.on("pageerror", lambda e: errs.append(str(e)[:140]))
    def add_csp(route):
        r = route.fetch()
        route.fulfill(response=r, headers={**r.headers, "content-security-policy": CSP})
    p.route("**/*.html", add_csp)
    p.goto(BASE + "/rvr-sim-lab.html", wait_until="networkidle")
    p.wait_for_timeout(300)
    check("README CSP has no violations", not errs, errs[:3])
    check("sim runs under CSP", "didn't start" not in run(p))
    p.goto(BASE + "/rvr-sim-lab-guide.html", wait_until="networkidle")
    check("guide has no CSP violations", not errs, errs[:3])

    # --- UI details
    p = open_sim(b)
    p.click("#modeText"); p.wait_for_timeout(80)
    hit = p.evaluate("""(() => { const t = document.querySelector('.blocklyToolboxDiv').getBoundingClientRect(); const e = document.elementFromPoint(t.left + t.width / 2, t.top + 30); return !!e.closest('.blocks-cover'); })()""")
    check("cover is above the toolbox", hit)
    p.click("#modeBlocks"); p.wait_for_timeout(80)
    p.click(".blocklyToolboxCategory >> nth=0"); p.wait_for_timeout(150)
    check("toolbox still works", p.evaluate("[...document.querySelectorAll('.blocklyFlyout')].some(f => f.getBoundingClientRect().width > 50)"))
    p.keyboard.press("Escape")

    p = open_sim(b)
    mission(p, 2)
    p.evaluate("() => { const w = Blockly.getMainWorkspace(); const n = w.newBlock('sphero_stop'); n.initSvg(); n.render(); }")
    p.wait_for_timeout(100)
    mission(p, 3)
    check("undo cleared between missions", p.evaluate("Blockly.getMainWorkspace().undoStack_.length") == 0)

    p = open_sim(b)
    check("code labels follow language", p.get_attribute("#codeView", "aria-label") == "Generated JavaScript")
    p.click("#langPy")
    check("code labels follow language py", p.get_attribute("#codeView", "aria-label") == "Generated Python")

    # speech bubble leaves after the run; compare the arena with a clean one
    p = open_sim(b, viewport={"width": 1400, "height": 900})
    p.click("#modeText")
    p.fill("#codeEdit", "async function startProgram(){ await speak('Sticky'); }")
    p.click("#runBtn")
    p.wait_for_timeout(5000)
    a = p.evaluate("document.getElementById('arena').toDataURL()")
    p.click("#resetBtn"); p.wait_for_timeout(200)
    c = p.evaluate("document.getElementById('arena').toDataURL()")
    check("speech bubble fades", a == c)

    # mission 4 message when overshooting a tile
    p = open_sim(b)
    p.evaluate("Math.random = () => 0")   # red tile at its lowest spot, y 112 to 136
    mission(p, 4)
    r = text_run(p, "js", "async function startProgram(){ await roll(0, 100, 2); }")
    check("overshoot message", "past the red tile" in r, r)

    # clipboard blocked: fallback must include the helper
    p = open_sim(b)
    p.evaluate("Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true })")
    mission(p, 4)
    p.click("#modeText")
    p.fill("#codeEdit", SOL[4][0])
    p.click("#modeBlocks")
    p.click("#modeText")
    p.evaluate("document.execCommand = () => false")
    p.click("#copyBtn"); p.wait_for_timeout(50)
    check("copy fallback includes helper", p.is_visible("#copyBox") and "function isColor" in p.input_value("#copyBox"), p.input_value("#copyBox")[:80])

    # text-only mode
    q = b.new_context().new_page()
    q.route("**/vendor/blockly/*.js", lambda r: r.abort())
    q.goto(BASE + "/rvr-sim-lab.html")
    q.wait_for_timeout(400)
    check("text-only fallback", q.is_visible("#codeEdit") and q.is_disabled("#modeBlocks") and q.is_hidden("#rebuildBtn"))
    check("text-only runs", "didn't start" not in run(q))

    # layouts
    for url in ("/rvr-sim-lab.html", "/rvr-sim-lab-guide.html"):
        for w in (360, 800, 1280):
            q = b.new_context(viewport={"width": w, "height": 800}).new_page()
            q.goto(BASE + url, wait_until="networkidle")
            q.wait_for_timeout(150)
            if "guide" not in url:
                q.click("#calib summary")
            size = q.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            check(f"no sideways scroll {url} {w}", size[0] <= size[1], size)

    b.close()

print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
