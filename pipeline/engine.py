"""Sticky Story week-2 render engine: cairo vector animation + synthesized audio."""
import math, random, subprocess, os, json
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
SR = 48000
FONT = "Inter Display Black"
GROUND = 1540
INK = (0.07, 0.07, 0.09)

def hexc(h, a=1.0):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(ch * 2 for ch in h)
    if len(h) == 8:
        return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4, 6))
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4)) + (a,)

def src(c, col):
    if isinstance(col, str):
        col = hexc(col)
    if len(col) == 3:
        c.set_source_rgb(*col)
    else:
        c.set_source_rgba(*col)

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def ease_out_back(x):
    x = max(0.0, min(1.0, x))
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()

def rect(c, x, y, w, h, col):
    src(c, col); c.rectangle(x, y, w, h); c.fill()

def circle(c, x, y, r, col):
    src(c, col); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

def line(c, pts, col, w, cap=cairo.LINE_CAP_ROUND):
    src(c, col); c.set_line_width(w); c.set_line_cap(cap); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.stroke()

def text(c, s, x, y, size, col="#ffffff", anchor="c", stroke=None, sw=0, font=FONT, weight=1):
    c.select_font_face(font, 0, weight)
    c.set_font_size(size)
    ext = c.text_extents(s)
    if anchor == "c":
        tx = x - ext.width / 2 - ext.x_bearing
    elif anchor == "l":
        tx = x - ext.x_bearing
    else:
        tx = x - ext.width - ext.x_bearing
    ty = y - ext.height / 2 - ext.y_bearing
    c.move_to(tx, ty)
    c.text_path(s)
    if stroke:
        src(c, stroke); c.set_line_width(sw); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    src(c, col); c.fill()
    return ext.x_advance

def text_w(c, s, size, font=FONT):
    c.select_font_face(font, 0, 1); c.set_font_size(size)
    return c.text_extents(s).x_advance

def wrap(c, s, size, maxw):
    words = s.split(); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if text_w(c, t, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

# ---------------------------------------------------------------- stickman
POSES = {}
def pose(name):
    def deco(f):
        POSES[name] = f; return f
    return deco

def P(lean=0, a1=(12, 4), a2=(-12, -4), l1=(8, 3), l2=(-8, -3), bob=0, tilt=0, hip=0):
    return dict(lean=lean, a1=a1, a2=a2, l1=l1, l2=l2, bob=bob, tilt=tilt, hip=hip)

@pose("stand")
def _(t): b = math.sin(t * 2.2) * 3; return P(bob=b, a1=(10 + b, 4), a2=(-10 - b, -4))
@pose("walk")
def _(t):
    s = math.sin(t * 9)
    return P(lean=4, a1=(28 * s, 18 * s + 10), a2=(-28 * s, -18 * s + 10), l1=(30 * s, 30 * s - 12 * abs(s)), l2=(-30 * s, -30 * s - 12 * abs(s)), bob=-abs(s) * 8)
@pose("run")
def _(t):
    s = math.sin(t * 14)
    return P(lean=14, a1=(55 * s, 55 * s + 70), a2=(-55 * s, -55 * s + 70), l1=(50 * s, 50 * s - 40), l2=(-50 * s, -50 * s - 40), bob=-abs(s) * 14)
@pose("shock")
def _(t): j = math.sin(t * 40) * 4; return P(lean=-6, a1=(150 + j, 175), a2=(-150 - j, -175), l1=(16, 8), l2=(-16, -8))
@pose("scared")
def _(t): j = math.sin(t * 35) * 3; return P(lean=-8 + j * .3, a1=(50 + j, 150), a2=(35 - j, 140), l1=(12, 4), l2=(-12, -4), bob=j)
@pose("freeze")
def _(t): j = math.sin(t * 50) * 1.5; return P(lean=0, a1=(6, 2), a2=(-6, -2), l1=(4, 2), l2=(-4, -2), bob=j)
@pose("point")
def _(t): return P(a1=(88, 90), a2=(-12, -4))
@pose("phone")
def _(t): b = math.sin(t * 2.2) * 2; return P(bob=b, a1=(30, 165), a2=(-12, -4), tilt=4)
@pose("text")
def _(t): return P(a1=(30, 115), a2=(18, 120), tilt=14, lean=4)
@pose("hold")
def _(t): b = math.sin(t * 2.2) * 2; return P(bob=b, a1=(62, 95), a2=(48, 95))
@pose("knock")
def _(t): k = abs(math.sin(t * 9)) * 30; return P(a1=(70 + k * .3, 100 + k), a2=(-12, -4), lean=6)
@pose("cheer")
def _(t): b = abs(math.sin(t * 8)); return P(a1=(150, 165), a2=(-150, -165), bob=-b * 30, l1=(14 + b * 10, 0), l2=(-14 - b * 10, 0))
@pose("wave")
def _(t): w = math.sin(t * 10) * 18; return P(a1=(150, 170 + w), a2=(-12, -4))
@pose("sit")
def _(t): b = math.sin(t * 2) * 2; return P(bob=b, a1=(25, 70), a2=(15, 70), l1=(88, 0), l2=(80, 0), hip=105)
@pose("sit_talk")
def _(t): b = math.sin(t * 6) * 10; return P(a1=(55 + b, 120), a2=(15, 70), l1=(88, 0), l2=(80, 0), hip=105)
@pose("facepalm")
def _(t): return P(a1=(25, 170), a2=(-12, -4), tilt=12, lean=6)
@pose("think")
def _(t): return P(a1=(20, 150), a2=(40, -30), tilt=-6)
@pose("shrug")
def _(t): return P(a1=(55, -20), a2=(-55, 20))
@pose("angry")
def _(t): j = math.sin(t * 20) * 6; return P(lean=8, a1=(60 + j, 30), a2=(-30, -60), bob=0)
@pose("swing")
def _(t): s = min(1, t * 5); return P(a1=(40 + 100 * s, 50 + 100 * s), a2=(-30, -10), lean=10)
@pose("sad")
def _(t): return P(lean=10, a1=(4, 0), a2=(-4, 0), tilt=18)
@pose("cry_happy")
def _(t): j = math.sin(t * 12) * 3; return P(a1=(40, 150 + j), a2=(35, 150 - j), tilt=8, bob=j)
@pose("give")
def _(t): return P(a1=(70, 80), a2=(-12, -4), lean=4)
@pose("dance")
def _(t):
    s = math.sin(t * 7)
    return P(a1=(120 + 30 * s, 150), a2=(-60 + 40 * s, -120), l1=(20 + 10 * s, 0), l2=(-20 + 10 * s, 0), bob=-abs(s) * 18, lean=8 * s)
@pose("type")
def _(t): k = math.sin(t * 25) * 6; return P(a1=(60, 100 + k), a2=(52, 100 - k), l1=(88, 0), l2=(80, 0), hip=105, tilt=6)
@pose("lie_up")  # sitting up in bed (upper body only shown)
def _(t): return P(a1=(30, 60), a2=(20, 60), l1=(90, 90), l2=(90, 90), hip=105, lean=-4)

def stick(c, x, y, s=1.0, pose_name="stand", t=0.0, face="neutral", dir=1, acc=None, outline=True, col=None, look=0):
    """x,y = feet on ground point."""
    acc = acc or {}
    p = POSES[pose_name](t)
    ink = col or INK
    lw = 17 * s
    thigh, shin, torso_l, up, low, hr = 112 * s, 112 * s, 185 * s, 92 * s, 88 * s, 50 * s
    hipx, hipy = x, y - (thigh + shin) + p['hip'] * s + p['bob'] * s
    def pt(ox, oy, ang, L):
        a = math.radians(ang)
        return (ox + math.sin(a) * L * dir, oy + math.cos(a) * L)
    lean = math.radians(p['lean'])
    neck = (hipx + math.sin(lean) * torso_l * dir, hipy - math.cos(lean) * torso_l)
    shoulder = (hipx + math.sin(lean) * torso_l * 0.86 * dir, hipy - math.cos(lean) * torso_l * 0.86)
    tilt = math.radians(p['tilt'] + p['lean'] * .5)
    head = (neck[0] + math.sin(tilt) * (hr + 10 * s) * dir, neck[1] - math.cos(tilt) * (hr + 10 * s))
    k1 = pt(hipx, hipy, p['l1'][0], thigh); f1 = pt(*k1, p['l1'][1], shin)
    k2 = pt(hipx, hipy, p['l2'][0], thigh); f2 = pt(*k2, p['l2'][1], shin)
    e1 = pt(*shoulder, p['a1'][0], up); h1 = pt(*e1, p['a1'][1], low)
    e2 = pt(*shoulder, p['a2'][0], up); h2 = pt(*e2, p['a2'][1], low)
    limbs = [[(hipx, hipy), k2, f2], [shoulder, e2, h2], [(hipx, hipy), neck], [(hipx, hipy), k1, f1], [shoulder, e1, h1]]
    if pose_name in ("lie_up",):
        limbs = [[shoulder, e2, h2], [(hipx, hipy), neck], [shoulder, e1, h1]]
    if outline:
        for L in limbs:
            line(c, L, (1, 1, 1, 0.95), lw + 12 * s)
        circle(c, head[0], head[1], hr + 6 * s + lw / 2, (1, 1, 1, 0.95))
    # apron / tie / suit behind arms
    for L in limbs[:2]:
        line(c, L, ink, lw)
    line(c, limbs[2], ink, lw)
    if 'apron' in acc:
        a = acc['apron']; mx = (hipx + neck[0]) / 2
        src(c, a); c.move_to(neck[0] - 26 * s, neck[1] + 70 * s); c.line_to(neck[0] + 26 * s, neck[1] + 70 * s)
        c.line_to(hipx + 40 * s, hipy + 60 * s); c.line_to(hipx - 40 * s, hipy + 60 * s); c.close_path(); c.fill()
    if 'tie' in acc:
        src(c, acc['tie']); tx, ty = neck[0], neck[1] + 12 * s
        c.move_to(tx - 9 * s, ty); c.line_to(tx + 9 * s, ty); c.line_to(tx + 12 * s, ty + 85 * s); c.line_to(tx, ty + 100 * s); c.line_to(tx - 12 * s, ty + 85 * s); c.close_path(); c.fill()
    if 'vest' in acc:
        src(c, acc['vest']); c.move_to(neck[0] - 30 * s, neck[1] + 20 * s); c.line_to(neck[0] + 30 * s, neck[1] + 20 * s)
        c.line_to(hipx + 34 * s, hipy + 8 * s); c.line_to(hipx - 34 * s, hipy + 8 * s); c.close_path(); c.fill()
    if 'dress' in acc:
        src(c, acc['dress']); c.move_to(neck[0] - 18 * s, neck[1] + 30 * s); c.line_to(neck[0] + 18 * s, neck[1] + 30 * s)
        c.line_to(hipx + 62 * s, hipy + 70 * s); c.line_to(hipx - 62 * s, hipy + 70 * s); c.close_path(); c.fill()
    for L in limbs[3:]:
        line(c, L, ink, lw)
    # held items
    hand = h1
    if acc.get('hold'):
        draw_held(c, acc['hold'], hand, s, dir, t)
    if acc.get('hold2'):
        draw_held(c, acc['hold2'], h2, s, dir, t)
    # head
    hx, hy = head
    if 'hair_long' in acc:
        src(c, acc['hair_long']); c.arc(hx - 4 * s * dir, hy + 4 * s, hr + 12 * s, math.pi * 0.9, math.pi * 2.1); c.fill()
        rrect(c, hx - (hr + 12 * s) - 4 * s * dir, hy, (hr + 12 * s) * 2, hr * 1.25, 18 * s); c.fill()
    circle(c, hx, hy, hr + lw / 2, ink)
    circle(c, hx, hy, hr - lw / 2 + 4 * s, "#ffffff")
    draw_face(c, hx, hy, hr, s, face, dir, t, look)
    draw_head_acc(c, acc, hx, hy, hr, s, dir, lw)
    return dict(head=head, hand=h1, hand2=h2, hip=(hipx, hipy), neck=neck)

def draw_face(c, hx, hy, hr, s, face, dir, t, look=0):
    ex = hx + (10 + look * 8) * s * dir
    blink = (t % 3.7) < 0.12 and face not in ("shock", "scared", "terrified")
    e = 13 * s
    def eyes(r, dy=0, white=False):
        for dx in (-17, 17):
            if blink:
                line(c, [(ex + dx * s - r, hy - 6 * s + dy), (ex + dx * s + r, hy - 6 * s + dy)], INK, 5 * s)
            elif white:
                circle(c, ex + dx * s, hy - 6 * s + dy, r, INK); circle(c, ex + dx * s, hy - 6 * s + dy, r * 0.62, "#ffffff")
                circle(c, ex + dx * s + 2 * s * dir, hy - 6 * s + dy, r * 0.32, INK)
            else:
                circle(c, ex + dx * s, hy - 6 * s + dy, r, INK)
    def brows(a, dy=-26):
        for sgn in (-1, 1):
            cx = ex + sgn * 17 * s; cy = hy + dy * s
            ang = math.radians(a) * sgn
            line(c, [(cx - 11 * s * math.cos(ang), cy - 11 * s * math.sin(ang)), (cx + 11 * s * math.cos(ang), cy + 11 * s * math.sin(ang))], INK, 5 * s)
    my = hy + 20 * s
    if face == "neutral":
        eyes(6 * s); line(c, [(ex - 10 * s, my), (ex + 10 * s, my)], INK, 5 * s)
    elif face == "happy":
        eyes(6 * s); src(c, INK); c.set_line_width(5 * s); c.arc(ex, my - 8 * s, 16 * s, 0.15 * math.pi, 0.85 * math.pi); c.stroke()
    elif face == "grin":
        eyes(6 * s); src(c, INK); c.arc(ex, my - 6 * s, 18 * s, 0, math.pi); c.fill()
    elif face == "smirk":
        eyes(6 * s); brows(-12); line(c, [(ex - 12 * s, my + 2 * s), (ex + 6 * s, my), (ex + 14 * s, my - 8 * s)], INK, 5 * s)
    elif face == "sad":
        eyes(6 * s); brows(18); src(c, INK); c.set_line_width(5 * s); c.arc(ex, my + 16 * s, 13 * s, 1.2 * math.pi, 1.8 * math.pi); c.stroke()
    elif face == "worried":
        eyes(7 * s); brows(20); line(c, [(ex - 12 * s, my + 2 * s), (ex - 4 * s, my - 3 * s), (ex + 4 * s, my + 2 * s), (ex + 12 * s, my - 3 * s)], INK, 4 * s)
        sweat(c, hx - 34 * s * dir, hy - 22 * s, s, t)
    elif face in ("scared", "terrified"):
        eyes(12 * s, white=True); brows(24, -34); circle(c, ex, my + 4 * s, 9 * s, INK)
        sweat(c, hx - 36 * s * dir, hy - 20 * s, s, t)
        if face == "terrified": sweat(c, hx + 40 * s * dir, hy - 30 * s, s, t + 0.4)
    elif face == "shock":
        eyes(13 * s, white=True); brows(0, -38); src(c, INK); c.save(); c.translate(ex, my + 6 * s); c.scale(1, 1.4); c.arc(0, 0, 11 * s, 0, 2 * math.pi); c.restore(); c.fill()
    elif face == "angry":
        eyes(6 * s); brows(-25, -22); src(c, INK); c.set_line_width(5 * s); c.arc(ex, my + 14 * s, 12 * s, 1.15 * math.pi, 1.85 * math.pi); c.stroke()
    elif face == "grumpy":
        eyes(5 * s); brows(-18, -20); line(c, [(ex - 12 * s, my + 4 * s), (ex + 12 * s, my + 4 * s)], INK, 6 * s)
    elif face == "cry":
        eyes(6 * s); brows(18); src(c, INK); c.set_line_width(5 * s); c.arc(ex, my - 8 * s, 14 * s, 0.15 * math.pi, 0.85 * math.pi); c.stroke()
        for dx in (-17, 17):
            yy = hy + ((t * 60) % 40) * s
            src(c, "#4fa3ff"); c.arc(ex + dx * s, yy, 5 * s, 0, 2 * math.pi); c.fill()
    elif face == "blank":
        eyes(5 * s); line(c, [(ex - 6 * s, my), (ex + 6 * s, my)], INK, 4 * s)
    elif face == "sleepy":
        for dx in (-17, 17):
            line(c, [(ex + dx * s - 8 * s, hy - 6 * s), (ex + dx * s + 8 * s, hy - 6 * s)], INK, 5 * s)
        circle(c, ex, my + 2 * s, 5 * s, INK)

def sweat(c, x, y, s, t):
    yy = y + ((t * 40) % 30) * s
    src(c, "#5ab8ff"); c.move_to(x, yy - 14 * s); c.curve_to(x + 9 * s, yy, x + 9 * s, yy + 9 * s, x, yy + 9 * s)
    c.curve_to(x - 9 * s, yy + 9 * s, x - 9 * s, yy, x, yy - 14 * s); c.fill()

def draw_head_acc(c, acc, hx, hy, hr, s, dir, lw):
    if 'cap' in acc:
        src(c, acc['cap']); c.arc(hx, hy - 8 * s, hr + 6 * s, math.pi, 2 * math.pi); c.fill()
        rrect(c, hx + (10 if dir > 0 else -70) * s, hy - 16 * s, 60 * s, 16 * s, 8 * s); c.fill()
    if 'beanie' in acc:
        src(c, acc['beanie']); c.arc(hx, hy - 6 * s, hr + 8 * s, math.pi, 2 * math.pi); c.fill(); circle(c, hx, hy - hr - 12 * s, 12 * s, acc['beanie'])
    if 'flatcap' in acc:
        src(c, acc['flatcap']); c.arc(hx, hy - 12 * s, hr + 4 * s, math.pi * 1.05, math.pi * 1.95); c.fill()
        rrect(c, hx - (hr + 6 * s) + (14 * s * dir), hy - 26 * s, (hr + 6 * s) * 2, 16 * s, 8 * s); c.fill()
    if 'bun' in acc:
        circle(c, hx - 6 * s * dir, hy - hr - 18 * s, 24 * s, acc['bun'])
        src(c, acc['bun']); c.arc(hx, hy - 4 * s, hr + 7 * s, math.pi * 1.0, math.pi * 2.0); c.set_line_width(14 * s); c.stroke()
    if 'bow' in acc:
        bx, by = hx - 20 * s * dir, hy - hr - 6 * s
        src(c, acc['bow']); c.move_to(bx, by); c.line_to(bx - 22 * s, by - 14 * s); c.line_to(bx - 22 * s, by + 14 * s); c.close_path(); c.fill()
        c.move_to(bx, by); c.line_to(bx + 22 * s, by - 14 * s); c.line_to(bx + 22 * s, by + 14 * s); c.close_path(); c.fill()
        circle(c, bx, by, 7 * s, acc['bow'])
    if 'hair' in acc:  # short spiky hair
        src(c, acc['hair'])
        for i in range(5):
            a = math.pi * (1.1 + i * 0.2)
            x0, y0 = hx + math.cos(a) * hr, hy + math.sin(a) * hr
            c.move_to(x0 - 12 * s, y0 + 4 * s); c.line_to(hx + math.cos(a) * (hr + 26 * s), hy + math.sin(a) * (hr + 26 * s)); c.line_to(x0 + 12 * s, y0 + 4 * s); c.close_path(); c.fill()
    if 'glasses' in acc:
        ex = hx + 10 * s * dir
        for dx in (-17, 17):
            src(c, INK); c.set_line_width(4 * s); c.arc(ex + dx * s, hy - 6 * s, 12 * s, 0, 2 * math.pi); c.stroke()
        line(c, [(ex - 5 * s, hy - 6 * s), (ex + 5 * s, hy - 6 * s)], INK, 4 * s)
    if 'beard' in acc:
        src(c, acc['beard']); c.arc(hx + 6 * s * dir, hy + 18 * s, 30 * s, 0.05 * math.pi, 0.95 * math.pi); c.fill()
    if 'mustache' in acc:
        src(c, acc['mustache']); c.save(); c.translate(hx + 10 * s * dir, hy + 12 * s); c.scale(1, 0.45); c.arc(0, 0, 18 * s, 0, 2 * math.pi); c.restore(); c.fill()
    if 'headset' in acc:
        src(c, "#333333"); c.set_line_width(7 * s); c.arc(hx, hy, hr + 8 * s, math.pi * 1.05, math.pi * 1.95); c.stroke()
        circle(c, hx - (hr + 4 * s) * dir, hy, 14 * s, "#333333")
        line(c, [(hx - (hr) * dir, hy + 10 * s), (hx + 4 * s * dir, hy + 30 * s)], "#333333", 5 * s)
    if 'police' in acc:
        src(c, "#1d2b55"); c.arc(hx, hy - 12 * s, hr + 4 * s, math.pi, 2 * math.pi); c.fill()
        rrect(c, hx - hr - 10 * s, hy - 22 * s, (hr + 10 * s) * 2, 16 * s, 6 * s); c.fill()
        circle(c, hx, hy - hr - 4 * s, 9 * s, "#f4c430")
    if 'mask' in acc:
        src(c, "#222222"); c.arc(hx, hy, hr - 2 * s, 0, 2 * math.pi); c.fill()
        for dx in (-17, 17): circle(c, hx + 10 * s * dir + dx * s, hy - 6 * s, 8 * s, "#ffffff")

def draw_held(c, item, hand, s, dir, t):
    x, y = hand
    if item == "phone":
        c.save(); c.translate(x, y); c.rotate(-0.2 * dir)
        rrect(c, -16 * s, -48 * s, 32 * s, 58 * s, 6 * s); src(c, "#222"); c.fill()
        rrect(c, -12 * s, -43 * s, 24 * s, 46 * s, 3 * s); src(c, "#6fd3ff"); c.fill(); c.restore()
    elif item == "umbrella":
        c.save(); c.translate(x, y); c.rotate(-0.6 * dir)
        line(c, [(0, 20 * s), (0, -170 * s)], "#3a2a1a", 8 * s)
        src(c, "#c0392b"); c.move_to(0, -170 * s); c.line_to(-30 * s, -60 * s); c.line_to(30 * s, -60 * s); c.close_path(); c.fill(); c.restore()
    elif item == "ticket":
        c.save(); c.translate(x, y); c.rotate(-0.15)
        rrect(c, -10 * s, -50 * s, 70 * s, 44 * s, 4 * s); src(c, "#ffe35a"); c.fill()
        src(c, INK); c.set_line_width(3 * s); rrect(c, -10 * s, -50 * s, 70 * s, 44 * s, 4 * s); c.stroke(); c.restore()
    elif item == "envelope":
        c.save(); c.translate(x, y)
        rect(c, -10 * s, -40 * s, 80 * s, 52 * s, "#f3e6c4"); line(c, [(-10 * s, -40 * s), (30 * s, -12 * s), (70 * s, -40 * s)], "#b49a62", 3 * s); c.restore()
    elif item == "cane":
        line(c, [(x, y), (x + 6 * s * dir, y + 150 * s)], "#5b3a1e", 8 * s)
        src(c, "#5b3a1e"); c.set_line_width(8 * s); c.arc(x - 12 * s * dir, y, 14 * s, math.pi, 2 * math.pi); c.stroke()
    elif item == "knife":
        c.save(); c.translate(x, y); c.rotate(-0.9 * dir)
        rect(c, -5 * s, -6 * s, 10 * s, 30 * s, "#3b2a1a"); src(c, "#d9dde3"); c.move_to(-6 * s, -6 * s); c.line_to(6 * s, -6 * s); c.line_to(0, -80 * s); c.close_path(); c.fill(); c.restore()
    elif item == "cake_knife":
        c.save(); c.translate(x, y); c.rotate(-0.7 * dir)
        rect(c, -5 * s, -6 * s, 10 * s, 30 * s, "#ffffff"); src(c, "#d9dde3"); rrect(c, -7 * s, -70 * s, 14 * s, 64 * s, 6 * s); c.fill(); c.restore()
    elif item == "coffee":
        rrect(c, x - 18 * s, y - 34 * s, 36 * s, 40 * s, 6 * s); src(c, "#ffffff"); c.fill()
        src(c, INK); c.set_line_width(3 * s); rrect(c, x - 18 * s, y - 34 * s, 36 * s, 40 * s, 6 * s); c.stroke()
    elif item == "key":
        src(c, "#f4c430"); c.set_line_width(7 * s); c.arc(x, y - 30 * s, 14 * s, 0, 2 * math.pi); c.stroke(); line(c, [(x, y - 16 * s), (x, y + 30 * s)], "#f4c430", 7 * s)
    elif item == "briefcase":
        rrect(c, x - 40 * s, y, 80 * s, 56 * s, 6 * s); src(c, "#5a3b22"); c.fill()
    elif item == "cupcake":
        rect(c, x - 20 * s, y - 30 * s, 40 * s, 26 * s, "#d98ab0"); circle(c, x, y - 36 * s, 22 * s, "#fff1f5")
        line(c, [(x, y - 58 * s), (x, y - 82 * s)], "#5ab8ff", 5 * s); circle(c, x, y - 90 * s + math.sin(t * 20) * 2 * s, 7 * s, "#ffb000")
    elif item == "flowers":
        line(c, [(x, y), (x + 10 * s, y - 70 * s)], "#2f8f3a", 6 * s)
        for i, col in enumerate(["#ff5c8a", "#ffcc33", "#ff7b2e"]):
            circle(c, x + (i - 1) * 22 * s + 10 * s, y - 80 * s - (i % 2) * 14 * s, 15 * s, col)

# ---------------------------------------------------------------- props
def prop(c, name, x, y, s=1.0, t=0.0, **k):
    f = PROPS.get(name)
    if f: f(c, x, y, s, t, **k)

PROPS = {}
def P_(name):
    def d(f): PROPS[name] = f; return f
    return d

@P_("door")
def _(c, x, y, s, t, open=0.0, col="#7a4b2a", frame="#3e2a1a", dark=False, peep=False):
    w, h = 230 * s, 470 * s
    rect(c, x - w / 2 - 16 * s, y - h - 16 * s, w + 32 * s, h + 16 * s, frame)
    rect(c, x - w / 2, y - h, w, h, "#05060a" if dark else "#141820")
    ow = w * (1 - open * 0.85)
    rect(c, x - w / 2, y - h, ow, h, col)
    src(c, (0, 0, 0, 0.18)); c.set_line_width(4 * s); c.rectangle(x - w / 2 + 24 * s, y - h + 30 * s, ow - 48 * s, h * 0.38); c.stroke()
    c.rectangle(x - w / 2 + 24 * s, y - h * 0.5, ow - 48 * s, h * 0.42); c.stroke()
    circle(c, x - w / 2 + ow - 30 * s, y - h * 0.5, 12 * s, "#e8c15a")
    if peep and open == 0: circle(c, x, y - h * 0.78, 7 * s, "#111")

@P_("window_night")
def _(c, x, y, s, t, w=260, h=300, moon=True):
    w *= s; h *= s
    rect(c, x - w / 2 - 14 * s, y - 14 * s, w + 28 * s, h + 28 * s, "#d8d4cc")
    g = cairo.LinearGradient(0, y, 0, y + h); g.add_color_stop_rgb(0, .03, .05, .14); g.add_color_stop_rgb(1, .1, .12, .28)
    c.set_source(g); c.rectangle(x - w / 2, y, w, h); c.fill()
    rnd = random.Random(int(x))
    for i in range(14):
        circle(c, x - w / 2 + rnd.random() * w, y + rnd.random() * h * 0.7, 2 * s, (1, 1, 1, 0.5 + 0.5 * math.sin(t * 3 + i)))
    if moon: circle(c, x + w * 0.22, y + h * 0.25, 30 * s, "#f3efd2")
    line(c, [(x, y), (x, y + h)], "#d8d4cc", 10 * s); line(c, [(x - w / 2, y + h / 2), (x + w / 2, y + h / 2)], "#d8d4cc", 10 * s)

@P_("window_day")
def _(c, x, y, s, t, w=260, h=300):
    w *= s; h *= s
    rect(c, x - w / 2 - 14 * s, y - 14 * s, w + 28 * s, h + 28 * s, "#ffffff")
    g = cairo.LinearGradient(0, y, 0, y + h); g.add_color_stop_rgb(0, .55, .8, 1); g.add_color_stop_rgb(1, .8, .93, 1)
    c.set_source(g); c.rectangle(x - w / 2, y, w, h); c.fill()
    circle(c, x - w * 0.2 + (t * 6) % 80, y + h * 0.3, 26 * s, (1, 1, 1, 0.9)); circle(c, x - w * 0.2 + 30 * s + (t * 6) % 80, y + h * 0.3 + 6 * s, 22 * s, (1, 1, 1, 0.9))
    line(c, [(x, y), (x, y + h)], "#ffffff", 10 * s); line(c, [(x - w / 2, y + h / 2), (x + w / 2, y + h / 2)], "#ffffff", 10 * s)

@P_("bed")
def _(c, x, y, s, t):
    rect(c, x - 300 * s, y - 120 * s, 600 * s, 120 * s, "#5d4a8a")
    rect(c, x - 320 * s, y - 260 * s, 40 * s, 260 * s, "#4a3a2a"); rect(c, x + 280 * s, y - 170 * s, 40 * s, 170 * s, "#4a3a2a")
    rrect(c, x - 270 * s, y - 175 * s, 130 * s, 60 * s, 25 * s); src(c, "#e8e6f5"); c.fill()

@P_("blanket")
def _(c, x, y, s, t):
    rrect(c, x - 290 * s, y - 135 * s, 570 * s, 80 * s, 30 * s); src(c, "#7b68c9"); c.fill()

@P_("clock")
def _(c, x, y, s, t, txt="3:07", col="#ff3b3b"):
    rrect(c, x - 110 * s, y - 50 * s, 220 * s, 100 * s, 14 * s); src(c, "#111"); c.fill()
    text(c, txt, x, y, 64 * s, col)

@P_("nightstand")
def _(c, x, y, s, t):
    rect(c, x - 80 * s, y - 150 * s, 160 * s, 150 * s, "#4a3a2a"); rect(c, x - 60 * s, y - 110 * s, 120 * s, 6 * s, "#2e231a")

@P_("couch")
def _(c, x, y, s, t, col="#c2593e"):
    rrect(c, x - 280 * s, y - 230 * s, 560 * s, 140 * s, 30 * s); src(c, col); c.fill()
    rrect(c, x - 300 * s, y - 130 * s, 600 * s, 110 * s, 24 * s); src(c, hexc(col)[:3] + (1,)); c.fill()
    src(c, (0, 0, 0, 0.15)); rrect(c, x - 300 * s, y - 130 * s, 600 * s, 110 * s, 24 * s); c.fill()
    rect(c, x - 280 * s, y - 20 * s, 24 * s, 20 * s, "#3a2a1a"); rect(c, x + 256 * s, y - 20 * s, 24 * s, 20 * s, "#3a2a1a")

@P_("tv")
def _(c, x, y, s, t, lines=None, glow="#2b5cff"):
    rrect(c, x - 200 * s, y - 130 * s, 400 * s, 250 * s, 14 * s); src(c, "#15161c"); c.fill()
    rect(c, x - 185 * s, y - 115 * s, 370 * s, 220 * s, glow)
    if lines:
        for i, l in enumerate(lines):
            text(c, l, x, y - 70 * s + i * 62 * s, 44 * s, "#ffffff")
    rect(c, x - 20 * s, y + 120 * s, 40 * s, 40 * s, "#15161c"); rect(c, x - 90 * s, y + 160 * s, 180 * s, 14 * s, "#15161c")

@P_("table")
def _(c, x, y, s, t, w=420, col="#8a5a35"):
    rect(c, x - w / 2 * s, y - 200 * s, w * s, 26 * s, col); rect(c, x - w / 2 * s + 20 * s, y - 174 * s, 18 * s, 174 * s, col); rect(c, x + w / 2 * s - 38 * s, y - 174 * s, 18 * s, 174 * s, col)

@P_("counter")
def _(c, x, y, s, t, w=600, col="#6b7b8c", top="#d6dbe0"):
    rect(c, x - w / 2 * s, y - 260 * s, w * s, 260 * s, col); rect(c, x - w / 2 * s - 20 * s, y - 280 * s, w * s + 40 * s, 26 * s, top)

@P_("register")
def _(c, x, y, s, t):
    rect(c, x - 70 * s, y - 90 * s, 140 * s, 90 * s, "#30343c"); rect(c, x - 50 * s, y - 150 * s, 100 * s, 60 * s, "#20242c"); rect(c, x - 40 * s, y - 140 * s, 80 * s, 36 * s, "#3dd17a")

@P_("landline")
def _(c, x, y, s, t):
    rrect(c, x - 50 * s, y - 40 * s, 100 * s, 40 * s, 10 * s); src(c, "#b22222"); c.fill()
    rrect(c, x - 60 * s, y - 62 * s, 120 * s, 24 * s, 12 * s); c.fill()

@P_("coffee")
def _(c, x, y, s, t):
    rrect(c, x - 30 * s, y - 60 * s, 60 * s, 60 * s, 8 * s); src(c, "#ffffff"); c.fill()
    src(c, INK); c.set_line_width(4 * s); rrect(c, x - 30 * s, y - 60 * s, 60 * s, 60 * s, 8 * s); c.stroke()
    c.arc(x + 34 * s, y - 32 * s, 14 * s, -math.pi / 2, math.pi / 2); c.stroke()
    for i in range(3):
        ph = t * 2 + i
        src(c, (1, 1, 1, 0.6)); c.set_line_width(5 * s)
        c.move_to(x - 14 * s + i * 14 * s, y - 70 * s)
        c.curve_to(x - 24 * s + i * 14 * s + math.sin(ph) * 8 * s, y - 95 * s, x - 4 * s + i * 14 * s, y - 110 * s, x - 14 * s + i * 14 * s + math.sin(ph) * 6 * s, y - 135 * s); c.stroke()

@P_("plate")
def _(c, x, y, s, t):
    src(c, "#ffffff"); c.save(); c.translate(x, y - 10 * s); c.scale(1, 0.3); c.arc(0, 0, 70 * s, 0, 2 * math.pi); c.restore(); c.fill()
    circle(c, x - 20 * s, y - 14 * s, 18 * s, "#ffd23f"); circle(c, x + 22 * s, y - 12 * s, 18 * s, "#ffd23f")

@P_("booth")
def _(c, x, y, s, t, col="#c0392b"):
    rrect(c, x - 30 * s, y - 380 * s, 70 * s, 380 * s, 20 * s); src(c, col); c.fill()
    rect(c, x - 30 * s, y - 160 * s, 220 * s, 60 * s, col)

@P_("car")
def _(c, x, y, s, t, col="#3b6fd9", dir=1, lights=False, shadow_in_back=False):
    c.save(); c.translate(x, y); c.scale(dir, 1)
    src(c, col); c.move_to(-300 * s, -60 * s); c.line_to(-290 * s, -150 * s); c.line_to(-150 * s, -165 * s); c.line_to(-90 * s, -250 * s)
    c.line_to(140 * s, -250 * s); c.line_to(220 * s, -160 * s); c.line_to(300 * s, -140 * s); c.line_to(310 * s, -60 * s); c.close_path(); c.fill()
    src(c, "#a9d4f5"); c.move_to(-70 * s, -235 * s); c.line_to(20 * s, -235 * s); c.line_to(20 * s, -165 * s); c.line_to(-125 * s, -165 * s); c.close_path(); c.fill()
    c.move_to(40 * s, -235 * s); c.line_to(130 * s, -235 * s); c.line_to(195 * s, -165 * s); c.line_to(40 * s, -165 * s); c.close_path(); c.fill()
    if shadow_in_back:
        src(c, (0.02, 0.02, 0.03, 0.95)); c.arc(-40 * s, -185 * s, 26 * s, 0, 2 * math.pi); c.fill()
        circle(c, -50 * s, -190 * s, 4 * s, "#ffffff"); circle(c, -32 * s, -190 * s, 4 * s, "#ffffff")
    for wx in (-180, 190):
        circle(c, wx * s, -60 * s, 52 * s, "#15161c"); circle(c, wx * s, -60 * s, 24 * s, "#9aa0a8")
    if lights:
        circle(c, 300 * s, -120 * s, 14 * s, "#fff6b0")
    c.restore()

@P_("police_car")
def _(c, x, y, s, t, dir=1):
    PROPS["car"](c, x, y, s, t, col="#f1f2f5", dir=dir)
    c.save(); c.translate(x, y); c.scale(dir, 1)
    rect(c, -280 * s, -130 * s, 580 * s, 36 * s, "#1d2b55")
    text(c, "POLICE", 20 * s, -112 * s, 30 * s, "#ffffff")
    on = int(t * 6) % 2
    rect(c, -40 * s, -280 * s, 50 * s, 30 * s, "#ff2a2a" if on else "#5a1010"); rect(c, 10 * s, -280 * s, 50 * s, 30 * s, "#1e5bff" if not on else "#0d1f55")
    c.restore()
    if True:
        col = (1, 0.15, 0.15, 0.18) if on else (0.1, 0.3, 1, 0.18)
        g = cairo.RadialGradient(x, y - 260 * s, 10, x, y - 260 * s, 700 * s); g.add_color_stop_rgba(0, *col); g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        c.set_source(g); c.paint()

@P_("pump")
def _(c, x, y, s, t, screen="APPROVED"):
    rect(c, x - 70 * s, y - 330 * s, 140 * s, 330 * s, "#e8e8ea"); rect(c, x - 70 * s, y - 330 * s, 140 * s, 40 * s, "#d62828")
    rect(c, x - 50 * s, y - 270 * s, 100 * s, 60 * s, "#0f2a1a"); text(c, screen[:8], x, y - 240 * s, 18 * s, "#3dff8a")
    line(c, [(x + 70 * s, y - 200 * s), (x + 110 * s, y - 180 * s), (x + 110 * s, y - 60 * s)], "#222", 8 * s)

@P_("bus")
def _(c, x, y, s, t, open=0.0):
    rrect(c, x - 420 * s, y - 380 * s, 840 * s, 330 * s, 26 * s); src(c, "#f2b705"); c.fill()
    for i in range(5):
        rrect(c, x - 380 * s + i * 140 * s, y - 340 * s, 110 * s, 120 * s, 10 * s); src(c, "#a9d4f5"); c.fill()
    rect(c, x + 300 * s, y - 300 * s, 90 * s, 240 * s, "#1c1c22")
    dw = 45 * s * (1 - open)
    rect(c, x + 300 * s, y - 300 * s, dw, 240 * s, "#a9d4f5"); rect(c, x + 390 * s - dw, y - 300 * s, dw, 240 * s, "#a9d4f5")
    rect(c, x - 420 * s, y - 210 * s, 700 * s, 16 * s, "#c48f00")
    text(c, "42", x - 330 * s, y - 120 * s, 60 * s, "#1c1c22")
    for wx in (-260, 250):
        circle(c, wx * s, y - 50 * s if False else 0, 0, "#000")
        circle(c, x + wx * s, y - 50 * s, 55 * s, "#15161c"); circle(c, x + wx * s, y - 50 * s, 24 * s, "#9aa0a8")

@P_("busstop")
def _(c, x, y, s, t):
    line(c, [(x, y), (x, y - 420 * s)], "#555", 12 * s); circle(c, x, y - 450 * s, 50 * s, "#1e6bd6"); text(c, "BUS", x, y - 450 * s, 34 * s, "#ffffff")

@P_("desk_monitors")
def _(c, x, y, s, t, map_=True):
    rect(c, x - 360 * s, y - 230 * s, 720 * s, 30 * s, "#3a3f4a"); rect(c, x - 340 * s, y - 200 * s, 30 * s, 200 * s, "#3a3f4a"); rect(c, x + 310 * s, y - 200 * s, 30 * s, 200 * s, "#3a3f4a")
    for i, dx in enumerate((-220, 0, 220)):
        rrect(c, x + dx * s - 100 * s, y - 420 * s, 200 * s, 140 * s, 8 * s); src(c, "#1a1d24"); c.fill()
        rect(c, x + dx * s - 90 * s, y - 410 * s, 180 * s, 120 * s, "#0c3b5e" if i != 1 else "#103d22")
        for j in range(4):
            rect(c, x + dx * s - 80 * s, y - 395 * s + j * 26 * s, (60 + ((i * 7 + j * 13 + int(t * 3)) % 5) * 22) * s, 10 * s, (0.6, 0.9, 1, 0.6))
        rect(c, x + dx * s - 10 * s, y - 280 * s, 20 * s, 50 * s, "#1a1d24")

@P_("cake")
def _(c, x, y, s, t, knife=False):
    rect(c, x - 110 * s, y - 120 * s, 220 * s, 120 * s, "#ffb6c9"); rect(c, x - 110 * s, y - 130 * s, 220 * s, 22 * s, "#fff4f7")
    for i in range(5):
        cx = x - 80 * s + i * 40 * s
        line(c, [(cx, y - 130 * s), (cx, y - 175 * s)], "#5ab8ff", 7 * s); circle(c, cx, y - 185 * s + math.sin(t * 18 + i) * 2 * s, 9 * s, "#ffb000")
    if knife:
        rect(c, x + 120 * s, y - 20 * s, 120 * s, 16 * s, "#d9dde3"); rect(c, x + 230 * s, y - 24 * s, 50 * s, 24 * s, "#ffffff")

@P_("balloons")
def _(c, x, y, s, t):
    for i, col in enumerate(["#ff4d6d", "#ffd23f", "#3ec1ff", "#7c4dff"]):
        bx = x + (i - 1.5) * 70 * s + math.sin(t * 2 + i) * 8 * s; by = y - (i % 2) * 60 * s
        line(c, [(bx, by + 50 * s), (x, y + 260 * s)], "#ffffff", 2 * s)
        src(c, col); c.save(); c.translate(bx, by); c.scale(1, 1.2); c.arc(0, 0, 42 * s, 0, 2 * math.pi); c.restore(); c.fill()

@P_("banner")
def _(c, x, y, s, t, txt="HAPPY BIRTHDAY"):
    n = len(txt); w = 1000 * s
    src(c, "#ffffff"); c.set_line_width(3); c.move_to(x - w / 2, y); c.curve_to(x - w / 4, y + 60 * s, x + w / 4, y + 60 * s, x + w / 2, y); c.stroke()
    cols = ["#ff4d6d", "#ffd23f", "#3ec1ff", "#7cdb5a", "#b07cff"]
    for i, ch in enumerate(txt):
        u = (i + 0.5) / n; px = x - w / 2 + u * w; py = y + math.sin(u * math.pi) * 45 * s
        if ch == " ": continue
        src(c, cols[i % 5]); c.move_to(px - 30 * s, py); c.line_to(px + 30 * s, py); c.line_to(px, py + 80 * s); c.close_path(); c.fill()
        text(c, ch, px, py + 28 * s, 34 * s, "#ffffff")

@P_("speech")
def _(c, x, y, s, t, txt="", col="#ffffff", tc="#111111", size=46, tail=-1, maxw=640):
    lines = wrap(c, txt, size * s, maxw * s)
    lh = size * 1.18 * s
    w = max(text_w(c, l, size * s) for l in lines) + 70 * s; h = lh * len(lines) + 46 * s
    rrect(c, x - w / 2, y - h / 2, w, h, 30 * s); src(c, col); c.fill_preserve(); src(c, INK); c.set_line_width(6 * s); c.stroke()
    src(c, col); tx = x + tail * w * 0.25
    c.move_to(tx - 22 * s, y + h / 2 - 3 * s); c.line_to(tx + tail * 10 * s, y + h / 2 + 46 * s); c.line_to(tx + 26 * s, y + h / 2 - 3 * s); c.fill()
    line(c, [(tx - 22 * s, y + h / 2), (tx + tail * 10 * s, y + h / 2 + 46 * s), (tx + 26 * s, y + h / 2)], INK, 6 * s)
    for i, l in enumerate(lines):
        text(c, l, x, y - h / 2 + 23 * s + lh * (i + 0.5), size * s, tc)

@P_("sign")
def _(c, x, y, s, t, txt="DINER", col="#ff3b6b", bg="#1a1a22"):
    w = text_w(c, txt, 70 * s) + 80 * s
    rrect(c, x - w / 2, y - 60 * s, w, 120 * s, 20 * s); src(c, bg); c.fill()
    flick = 0.8 + 0.2 * math.sin(t * 30) * (1 if (t % 4) < 0.3 else 0)
    text(c, txt, x, y, 70 * s, hexc(col)[:3] + (flick,), stroke=hexc(col)[:3] + (0.35,), sw=14 * s)

@P_("shadowman")
def _(c, x, y, s, t, alpha=1.0, eyes=True):
    c.push_group()
    stick(c, x, y, s, "stand", t, "neutral", dir=-1, outline=False, col=(0.01, 0.01, 0.02))
    circle(c, x, y - 430 * s, 64 * s, (0.01, 0.01, 0.02))
    rrect(c, x - 55 * s, y - 400 * s, 110 * s, 260 * s, 30 * s); src(c, (0.01, 0.01, 0.02)); c.fill()
    if eyes:
        for dx in (-18, 14): circle(c, x + dx * s, y - 440 * s, 6 * s, (1, 1, 1, 0.9))
    c.pop_group_to_source(); c.paint_with_alpha(alpha)

@P_("key")
def _(c, x, y, s, t):
    draw_held(c, "key", (x, y), s, 1, t)

@P_("lamp_glow")
def _(c, x, y, s, t, col=(1, 0.85, 0.5), r=500, a=0.35):
    g = cairo.RadialGradient(x, y, 0, x, y, r * s); g.add_color_stop_rgba(0, col[0], col[1], col[2], a); g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    c.set_source(g); c.paint()

@P_("frame_pic")
def _(c, x, y, s, t, col="#e9c46a"):
    rect(c, x - 70 * s, y - 55 * s, 140 * s, 110 * s, "#5b3a1e"); rect(c, x - 58 * s, y - 43 * s, 116 * s, 86 * s, col)
    src(c, (1, 1, 1, .6)); c.move_to(x - 58 * s, y + 43 * s); c.line_to(x - 10 * s, y - 10 * s); c.line_to(x + 30 * s, y + 43 * s); c.fill()

@P_("plant")
def _(c, x, y, s, t):
    rect(c, x - 40 * s, y - 80 * s, 80 * s, 80 * s, "#c0663a")
    for i in range(5):
        a = -math.pi / 2 + (i - 2) * 0.4 + math.sin(t + i) * 0.03
        src(c, "#2f8f3a"); c.save(); c.translate(x, y - 80 * s); c.rotate(a + math.pi / 2); c.scale(0.35, 1); c.arc(0, -70 * s, 70 * s, 0, 2 * math.pi); c.restore(); c.fill()

# ---------------------------------------------------------------- backgrounds
def grad_bg(c, top, bot):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *hexc(top)[:3]); g.add_color_stop_rgb(1, *hexc(bot)[:3]); c.set_source(g); c.paint()

def room(c, wall, floor, ground=GROUND, base="#00000022", stripes=None):
    rect(c, 0, 0, W, ground, wall)
    if stripes:
        for i in range(0, W, 120): rect(c, i, 0, 60, ground, stripes)
    g = cairo.LinearGradient(0, ground, 0, H); a = hexc(floor); g.add_color_stop_rgb(0, *a[:3]); g.add_color_stop_rgb(1, a[0] * .7, a[1] * .7, a[2] * .7)
    c.set_source(g); c.rectangle(0, ground, W, H - ground); c.fill()
    rect(c, 0, ground - 26, W, 26, (0, 0, 0, 0.18))

BGS = {}
def B_(name):
    def d(f): BGS[name] = f; return f
    return d

@B_("bedroom_night")
def _(c, t, **k):
    room(c, "#1f2340", "#2a2238")
    prop(c, "window_night", 300, 380, 1.0, t)
    prop(c, "frame_pic", 800, 520, 1, t, col="#4b5a8a")
    prop(c, "lamp_glow", 300, 500, 1, t, col=(0.5, 0.6, 1), a=0.18)

@B_("hall_dark")
def _(c, t, **k):
    room(c, "#171a2b", "#1d1a26")
    rect(c, 380, 520, 320, 1020, "#0b0c14")
    prop(c, "frame_pic", 180, 700, 1, t, col="#3a4466"); prop(c, "frame_pic", 900, 700, 1, t, col="#3a4466")

@B_("hall_out")
def _(c, t, **k):
    room(c, "#5b5e6e", "#3d3a44")
    for i in range(0, W, 270): rect(c, i, 260, 6, GROUND - 260, (0, 0, 0, 0.15))
    prop(c, "lamp_glow", 540, 200, 1, t, col=(1, .9, .6), r=700, a=0.3)
    rrect(c, 470, 180, 140, 30, 10); src(c, "#fff6c8"); c.fill()

@B_("peephole")
def _(c, t, who=None, **k):
    rect(c, 0, 0, W, H, "#050507")
    c.save(); c.arc(540, 900, 470, 0, 2 * math.pi); c.clip()
    rect(c, 0, 0, W, H, "#4d5060")
    prop(c, "lamp_glow", 540, 450, 1, t, col=(1, .9, .6), r=600, a=0.4)
    c.save(); c.translate(540, 900); c.scale(1.35, 1.35); c.translate(-540, -900)
    if who: who(c, t)
    c.restore()
    g = cairo.RadialGradient(540, 900, 250, 540, 900, 470); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    c.set_source(g); c.paint(); c.restore()
    src(c, "#2a2a30"); c.set_line_width(30); c.arc(540, 900, 485, 0, 2 * math.pi); c.stroke()

@B_("cctv")
def _(c, t, draw=None, stamp="03:07:12", **k):
    rect(c, 0, 0, W, H, "#0a0a0c")
    rrect(c, 60, 380, 960, 1100, 30); src(c, "#22252c"); c.fill()
    c.save(); c.rectangle(100, 420, 880, 1000); c.clip()
    rect(c, 100, 420, 880, 1000, "#3a4a42")
    c.save(); c.translate(100, 420); c.scale(880 / W, 1000 / 1500); c.translate(0, -300)
    if draw: draw(c, t)
    c.restore()
    # grayscale-ish tint + scanlines
    src(c, (0.2, 0.35, 0.25, 0.35)); c.paint()
    for yy in range(420, 1420, 6): rect(c, 100, yy, 880, 2, (0, 0, 0, 0.18))
    rnd = random.Random(int(t * 30))
    for i in range(60): rect(c, 100 + rnd.random() * 880, 420 + rnd.random() * 1000, 3, 3, (1, 1, 1, 0.15))
    c.restore()
    text(c, "CAM 1  HALLWAY", 130, 470, 34, "#e8ffe8", anchor="l", font="DejaVu Sans Mono", weight=1)
    text(c, stamp, 950, 470, 34, "#e8ffe8", anchor="r", font="DejaVu Sans Mono", weight=1)
    if int(t * 2) % 2 == 0: circle(c, 140, 1380, 12, "#ff2a2a")
    text(c, "REC", 165, 1380, 30, "#ff2a2a", anchor="l", font="DejaVu Sans Mono")

@B_("living")
def _(c, t, **k):
    room(c, "#f1e3c8", "#b9895f", stripes="#ecdcbd")
    prop(c, "window_day", 820, 360, 0.9, t)
    prop(c, "frame_pic", 260, 520, 1, t)
    prop(c, "plant", 980, GROUND, 1, t)

@B_("living_night")
def _(c, t, **k):
    room(c, "#2c3150", "#3b3048", stripes="#2a2e4b")
    prop(c, "window_night", 820, 360, 0.9, t)
    prop(c, "frame_pic", 260, 520, 1, t, col="#6a6aa0")

@B_("office")
def _(c, t, **k):
    room(c, "#dfe6ee", "#8e9aa6")
    for i in range(3): prop(c, "window_day", 200 + i * 340, 300, 0.85, t)

@B_("dispatch")
def _(c, t, **k):
    room(c, "#1b2333", "#232a38")
    for i in range(3): rect(c, 80 + i * 330, 560, 260, 150, "#0f1a2c")
    for i in range(3): text(c, ["911", "EMERGENCY", "DISPATCH"][i], 210 + i * 330, 635, 40, "#ff4d4d")

@B_("kitchen_night")
def _(c, t, **k):
    room(c, "#3a3550", "#4a3f3a")
    rect(c, 0, 900, W, 30, "#5b5070"); rect(c, 0, 1220, W, 320, "#4c4560")
    for i in range(4): rect(c, 40 + i * 260, 420, 220, 300, "#5b5070")
    prop(c, "lamp_glow", 540, 380, 1, t, col=(1, .8, .5), r=500, a=0.25)

@B_("gas_night")
def _(c, t, **k):
    grad_bg(c, "#070a1c", "#1a1f40")
    rnd = random.Random(3)
    for i in range(40): circle(c, rnd.random() * W, rnd.random() * 700, 2, (1, 1, 1, 0.3 + 0.3 * math.sin(t * 2 + i)))
    rect(c, 0, GROUND, W, H - GROUND, "#26262e")
    for i in range(0, W, 160): rect(c, i + ((t * 0) % 160), GROUND + 160, 90, 12, "#d8c25a")
    # canopy
    rect(c, 40, 420, 1000, 80, "#d62828"); rect(c, 40, 500, 1000, 16, "#f2f2f2")
    for x_ in (160, 920): rect(c, x_ - 20, 516, 40, GROUND - 516, "#bfc3c9")
    prop(c, "lamp_glow", 540, 520, 1, t, col=(1, 1, 0.9), r=800, a=0.28)
    text(c, "GAS 24/7", 540, 460, 52, "#ffffff")

@B_("store_in")
def _(c, t, **k):
    room(c, "#e9eef0", "#c9ced2")
    for i in range(3):
        rect(c, 60 + i * 340, 520, 280, 520, "#9aa6b2")
        for j in range(4):
            for q in range(5):
                rect(c, 75 + i * 340 + q * 54, 540 + j * 128, 44, 100, ["#ff6b6b", "#ffd23f", "#4ecdc4", "#7c4dff", "#ff9f1c"][(i + j + q) % 5])
    rect(c, 0, 0, W, 140, "#ffffff"); rect(c, 0, 130, W, 10, "#d62828")
    prop(c, "lamp_glow", 540, 100, 1, t, col=(1, 1, 1), r=1000, a=0.15)

@B_("store_night_window")  # inside store looking out at the car through glass
def _(c, t, **k):
    room(c, "#d9dfe3", "#c9ced2")
    rect(c, 100, 340, 880, 820, "#0b0f22")
    rnd = random.Random(5)
    for i in range(20): circle(c, 120 + rnd.random() * 840, 360 + rnd.random() * 300, 2, (1, 1, 1, .5))
    rect(c, 100, 1000, 880, 160, "#26262e")
    for x_ in (100, 540, 980): rect(c, x_ - 10, 340, 20, 820, "#9aa0a8")
    rect(c, 90, 330, 900, 20, "#9aa0a8"); rect(c, 90, 1150, 900, 20, "#9aa0a8")

@B_("diner")
def _(c, t, **k):
    room(c, "#f6e7c1", "#e5e5e5")
    for i in range(0, W, 80):
        for j in range(GROUND, H, 80):
            if (i // 80 + j // 80) % 2 == 0: rect(c, i, j, 80, 80, "#2b2b33")
    rect(c, 0, 1100, W, 440, "#2fb5a8"); rect(c, 0, 1090, W, 20, "#d0d6db")
    prop(c, "window_day", 280, 330, 0.9, t); prop(c, "window_day", 800, 330, 0.9, t)
    prop(c, "sign", 540, 760, 0.7, t, txt="DINER", col="#ff3b6b")

@B_("street_day")
def _(c, t, **k):
    grad_bg(c, "#8fd3ff", "#d8f1ff")
    for i, (bx, bw, bh, col) in enumerate([(0, 260, 900, "#c97b63"), (240, 240, 1100, "#8a9bb0"), (470, 300, 820, "#e0b45e"), (760, 330, 1000, "#7d8fa8")]):
        rect(c, bx, GROUND - bh, bw, bh, col)
        for wy in range(int(GROUND - bh + 50), GROUND - 150, 130):
            for wx in range(int(bx + 30), int(bx + bw - 60), 80): rect(c, wx, wy, 50, 80, "#dff3ff")
    rect(c, 0, GROUND, W, H - GROUND, "#9a9a9e"); rect(c, 0, GROUND, W, 30, "#c8c8cc")

@B_("party")
def _(c, t, **k):
    room(c, "#3b2a6a", "#5a3a4a")
    prop(c, "banner", 540, 330, 1, t, txt=k.get("banner", "HAPPY 30TH MIA"))
    rnd = random.Random(int(t * 4))
    cols = ["#ff4d6d", "#ffd23f", "#3ec1ff", "#7cdb5a", "#b07cff"]
    for i in range(80):
        r2 = random.Random(i)
        x_ = r2.random() * W; y_ = (r2.random() * H + t * (200 + r2.random() * 200)) % H
        c.save(); c.translate(x_, y_); c.rotate(t * 3 + i); rect(c, -8, -4, 16, 8, cols[i % 5]); c.restore()
    prop(c, "balloons", 140, 620, 1, t); prop(c, "balloons", 940, 620, 1, t)

@B_("dark")
def _(c, t, **k):
    rect(c, 0, 0, W, H, "#060608")

@B_("solid")
def _(c, t, col="#15161c", **k):
    grad_bg(c, col, "#050507")

@B_("rays")
def _(c, t, col="#1d1e26", col2="#26283a", **k):
    rect(c, 0, 0, W, H, col)
    c.save(); c.translate(540, 900); c.rotate(t * 0.15)
    src(c, col2)
    for i in range(16):
        a = i * math.pi / 8
        c.move_to(0, 0); c.arc(0, 0, 2000, a, a + math.pi / 16); c.close_path(); c.fill()
    c.restore()

# --------- closeups
def phone_screen(c, t, msgs, header="Unknown", bt=0, accent="#2f7cf6", sub=None, bg="#0e0f13", typing_after=None):
    """msgs: list of (side, text, appear_time) side 'l' incoming 'r' outgoing; 'n' notification."""
    rect(c, 0, 0, W, H, bg)
    px, py, pw, ph = 130, 470, 820, 1170
    rrect(c, px - 24, py - 24, pw + 48, ph + 48, 90); src(c, "#1b1c22"); c.fill()
    rrect(c, px, py, pw, ph, 70); src(c, "#f4f5f8"); c.fill()
    c.save(); rrect(c, px, py, pw, ph, 70); c.clip()
    rect(c, px, py, pw, 190, "#ffffff"); rect(c, px, py + 190, pw, 3, "#dcdde3")
    circle(c, px + 110, py + 120, 42, "#9aa3b5"); text(c, header[0], px + 110, py + 120, 40, "#ffffff")
    text(c, header, px + 175, py + 105, 44, "#16171c", anchor="l")
    if sub: text(c, sub, px + 175, py + 150, 28, "#7a7f8c", anchor="l", font="Inter", weight=0)
    yy = py + 240
    for side, txt, at in msgs:
        if bt < at: continue
        pop = ease_out_back((bt - at) / 0.25)
        lines_ = wrap(c, txt, 50, 560)
        bw = max(text_w(c, l, 50) for l in lines_) + 64; bh = len(lines_) * 62 + 44
        bx = px + 40 if side == 'l' else px + pw - 40 - bw
        c.save(); c.translate(bx + bw / 2, yy + bh / 2); c.scale(pop, pop); c.translate(-(bx + bw / 2), -(yy + bh / 2))
        rrect(c, bx, yy, bw, bh, 34); src(c, "#e4e6eb" if side == 'l' else accent); c.fill()
        for i, l in enumerate(lines_):
            text(c, l, bx + 32, yy + 53 + i * 62, 50, "#16171c" if side == 'l' else "#ffffff", anchor="l", font="Inter", weight=1)
        c.restore()
        yy += bh + 26
    if typing_after is not None and bt > typing_after:
        rrect(c, px + 40, yy, 150, 80, 34); src(c, "#e4e6eb"); c.fill()
        for i in range(3): circle(c, px + 80 + i * 35, yy + 40 - abs(math.sin(t * 6 + i)) * 10, 10, "#8a8f9c")
    c.restore()

@B_("phone")
def _(c, t, **k):
    phone_screen(c, t, k.get("msgs", []), k.get("header", "Unknown"), k.get("bt", 0), sub=k.get("sub"), accent=k.get("accent", "#2f7cf6"), typing_after=k.get("typing_after"))

@B_("call")
def _(c, t, name="911", sub="00:42", bt=0, **k):
    grad_bg(c, "#1d2b55", "#0a0f22")
    for i in range(3):
        r = 140 + ((t * 120 + i * 90) % 270)
        src(c, (1, 1, 1, max(0, 0.25 - r / 1600))); c.set_line_width(4); c.arc(540, 760, r, 0, 2 * math.pi); c.stroke()
    circle(c, 540, 760, 130, "#3a4a7a"); text(c, name[0], 540, 760, 110, "#ffffff")
    text(c, name, 540, 990, 72, "#ffffff"); text(c, sub, 540, 1070, 44, "#aab4d4", font="Inter", weight=0)

@B_("ticket")
def _(c, t, nums=(7, 14, 21, 33, 42), date="NOV 3", tag="", glow=False, **k):
    rect(c, 0, 0, W, H, "#1a1530") if not glow else None
    if glow:
        BGS["rays"](c, t, col="#2a1f05", col2="#4a3606")
    c.save(); c.translate(540, 900); c.rotate(-0.05 + math.sin(t) * 0.01)
    rrect(c, -400, -260, 800, 520, 24); src(c, "#fff3b0"); c.fill()
    src(c, "#e0b400"); c.set_line_width(10); rrect(c, -400, -260, 800, 520, 24); c.stroke()
    text(c, "MEGA LOTTO", 0, -190, 64, "#d62828")
    for i, n in enumerate(nums):
        cx = -300 + i * 150
        circle(c, cx, -30, 62, "#ffffff"); src(c, INK); c.set_line_width(5); c.arc(cx, -30, 62, 0, 2 * math.pi); c.stroke()
        text(c, str(n), cx, -30, 56, INK)
    text(c, "DRAW: " + date, 0, 110, 44, "#444")
    if tag: text(c, tag, 0, 190, 40, "#d62828")
    c.restore()

@B_("note")
def _(c, t, lines=(), bt=0, cps=40, **k):
    rect(c, 0, 0, W, H, "#2b211a")
    for i in range(0, H, 90): rect(c, 0, i, W, 3, (0, 0, 0, 0.2))
    c.save(); c.translate(540, 900); c.rotate(0.02)
    rect(c, -420, -560, 840, 1120, "#fbf6e6")
    for i in range(14): rect(c, -380, -460 + i * 75, 760, 2, "#cfd8e6")
    shown = int(bt * cps); n = 0
    for i, l in enumerate(lines):
        part = l[:max(0, shown - n)]; n += len(l)
        text(c, part, -370, -310 + i * 75, 46, "#203060", anchor="l", font="DejaVu Serif", weight=0)
    c.restore()

@B_("map")
def _(c, t, bt=0, dur=3, **k):
    rect(c, 0, 0, W, H, "#0d1520")
    rrect(c, 80, 360, 920, 1140, 30); src(c, "#e9efe4"); c.fill()
    c.save(); rrect(c, 80, 360, 920, 1140, 30); c.clip()
    for i in range(6): rect(c, 80, 420 + i * 200, 920, 26, "#ffffff")
    for i in range(5): rect(c, 150 + i * 200, 360, 26, 1140, "#ffffff")
    rect(c, 640, 600, 160, 140, "#b9dca8"); rect(c, 260, 1100, 220, 160, "#b9dca8")
    hx, hy = 760, 860
    circle(c, hx, hy, 34 + 6 * math.sin(t * 6), (1, .2, .2, .35)); circle(c, hx, hy, 20, "#ff2a2a")
    u = ease(bt / dur); px = 200 + (hx - 200) * u; py = 1380 + (hy - 1380) * u
    rrect(c, px - 30, py - 20, 60, 40, 10); src(c, "#1e5bff"); c.fill()
    circle(c, px, py, 60 + 10 * math.sin(t * 8), (0.1, 0.3, 1, 0.25))
    c.restore()

@B_("pump_close")
def _(c, t, txt="APPROVED", **k):
    BGS["gas_night"](c, t)
    c.save(); c.translate(540, 1000); c.scale(3, 3); c.translate(-540, -1300)
    prop(c, "pump", 540, 1500, 1, t, screen=txt)
    c.restore()

def cta_card(c, t, line1, line2="FOLLOW FOR PART 2", **k):
    BGS["rays"](c, t, col="#14151d", col2="#1d1f2b")

# ---------------------------------------------------------------- overlay helpers
def draw_title(c, s, bt, y=330, col="#ffe600", box="#111111", size=82):
    if not s: return
    p = ease_out_back(bt / 0.28)
    lines_ = wrap(c, s, size, 900)
    lh = size * 1.12
    w = max(text_w(c, l, size) for l in lines_) + 70; h = lh * len(lines_) + 44
    c.save(); c.translate(540, y); c.scale(p, p); c.rotate(-0.02)
    rrect(c, -w / 2, -h / 2, w, h, 22); src(c, box); c.fill()
    for i, l in enumerate(lines_):
        text(c, l, 0, -h / 2 + 22 + lh * (i + 0.5), size, col)
    c.restore()

def draw_caption(c, words, idx, bt_word, y=1720):
    """words: list of words in current chunk, idx highlighted."""
    size = 94
    full = " ".join(words)
    while text_w(c, full, size) > 980 and size > 60: size -= 4
    x = 540 - (sum(text_w(c, w_, size) for w_ in words) + size * 0.3 * (len(words) - 1)) / 2
    sp = size * 0.3
    for i, w_ in enumerate(words):
        ww = text_w(c, w_, size)
        sc = 1.0
        if i == idx: sc = 1 + 0.12 * (1 - ease(bt_word / 0.15))
        c.save(); c.translate(x + ww / 2, y); c.scale(sc, sc)
        text(c, w_, 0, 0, size, "#ffe600" if i == idx else "#ffffff", stroke="#000000", sw=16)
        c.restore()
        x += ww + sp

def vignette(c, a=0.55):
    g = cairo.RadialGradient(540, 960, 500, 540, 960, 1250); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, a)
    c.set_source(g); c.paint()
