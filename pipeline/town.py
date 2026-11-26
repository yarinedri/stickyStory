"""Sticky Town: a growing world where every subscriber is a stickman.

Usage: python3 town.py <out.mp4> [preview_frames]
Reads ../state/town.json: {"day": n, "population": subs, "prev_population": subs_yesterday,
  "named": ["name", ...], "new_named": ["name", ...], "lines": optional custom narration list}
"""
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E
from engine import rect, circle, text, rrect, src, grad_bg, stick, GROUND, W

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "..", "state", "town.json")

PALETTE = ["#e76f51", "#f4a261", "#e9c46a", "#2a9d8f", "#8ab17d", "#b56576", "#6d6875", "#4d908e"]
SHIRTS = ["#ff4d6d", "#3ec1ff", "#7cdb5a", "#ffd23f", "#b07cff", "#ff8c42", "#00c2a8"]


def house(c, x, y, s, col, roof="#7a2e2e", alpha=1.0, ghost=False):
    c.save(); c.translate(x, y); c.scale(s, s)
    if ghost:
        c.set_dash([14, 10]); c.set_line_width(5); src(c, (1, 1, 1, 0.55))
        c.rectangle(-90, -170, 180, 170); c.stroke()
        c.move_to(-110, -170); c.line_to(0, -270); c.line_to(110, -170); c.close_path(); c.stroke()
        c.set_dash([])
        text(c, "?", 0, -90, 80, "#ffffff")
    else:
        rect(c, -90, -170, 180, 170, col)
        c.move_to(-110, -168); c.line_to(0, -270); c.line_to(110, -168); c.close_path(); src(c, roof); c.fill()
        rect(c, -25, -95, 50, 95, "#4a2f1d")
        rect(c, -70, -140, 38, 38, "#fff3c4"); rect(c, 32, -140, 38, 38, "#fff3c4")
    c.restore()


def name_tag(c, x, y, name, col="#111111", fg="#ffffff", size=30):
    w = E.text_w(c, name, size) + 28
    rrect(c, x - w / 2, y - size * 0.75, w, size * 1.5, 12); src(c, col); c.fill()
    text(c, name, x, y, size, fg)


def town_bg(st):
    pop = st["population"]

    def d(c, t, **k):
        grad_bg(c, "#7ec8ff", "#e6f6ff")
        circle(c, 880, 330, 90, "#ffe27a")
        for i, (cx, cy, r) in enumerate([(200, 420, 60), (300, 400, 80), (650, 300, 55), (740, 290, 70)]):
            ox = (t * 12 + i * 90) % 1300 - 120
            circle(c, (cx + ox) % 1200 - 60, cy, r, "#ffffff")
        # hills
        c.move_to(0, 1250)
        for x in range(0, W + 1, 40):
            c.line_to(x, 1250 - 90 * math.sin(x / 260) - 40 * math.sin(x / 90 + 1))
        c.line_to(W, GROUND); c.line_to(0, GROUND); c.close_path(); src(c, "#9bd37a"); c.fill()
        rect(c, 0, GROUND, W, 400, "#6fbf5a"); rect(c, 0, GROUND + 80, W, 70, "#c9b48a")
        # trees
        for tx, ts in [(60, 1.0), (1010, 1.1), (560, 0.7), (150, 0.6)]:
            rect(c, tx - 12 * ts, 1290 - 40 * ts, 24 * ts, 120 * ts, "#6b4423")
            circle(c, tx, 1250 - 60 * ts, 75 * ts, "#3f9a4a"); circle(c, tx - 40 * ts, 1270 - 40 * ts, 55 * ts, "#4fae58")
        # big town sign (top area)
        rect(c, 528, 760, 24, 420, "#5b3a22")
        rrect(c, 250, 560, 580, 230, 26); src(c, "#2f6b3a"); c.fill()
        c.set_line_width(10); rrect(c, 250, 560, 580, 230, 26); src(c, "#f4f1de"); c.stroke()
        text(c, "STICKY TOWN", 540, 640, 76, "#ffffff")
        text(c, f"POPULATION: {pop + 1}", 540, 730, 54, "#ffe600")
    return d


def residents_layer(st, show_named=True, ghosts=0, highlight_new=True):
    pop = st["population"]
    named = st.get("named", [])
    new = set(st.get("new_named", []))
    n_houses = max(1, min(9, pop // 3 + 1))
    rnd = random.Random(42)
    hx = [rnd.choice(PALETTE) for _ in range(12)]

    def d(c, tt, bt, dur):
        # houses in a back row
        for i in range(n_houses):
            x = 620 + (i % 4) * 150 - (i // 4) * 75
            y = GROUND - 20 - (i // 4) * 70
            house(c, x, y, 0.8, hx[i])
        for g in range(ghosts):
            house(c, 620 + ((n_houses + g) % 4) * 150, GROUND - 20, 0.8, "#000", ghost=True)
        # mayor
        my = GROUND + 120
        stick(c, 250, my, 0.8, "wave", tt, "happy", 1, {'hair': '#2a2a2a'})
        name_tag(c, 250, my - 610 * 0.8, "MAYOR STICKY", "#ffe600", "#111111", 30)
        # citizens
        shown = min(pop, 40)
        for i in range(shown):
            col_i = i % 8; row = i // 8
            x = 380 + col_i * 88 + (row % 2) * 40
            y = GROUND + 120 + row * 70
            s = 0.55 - row * 0.03
            nm = named[i] if i < len(named) else None
            pose = "cheer" if (nm in new and highlight_new) else ("wave" if i % 3 == 0 else "stand")
            face = "grin" if nm in new else "happy"
            stick(c, x, y, s, pose, tt + i * 0.37, face, 1 if i % 2 else -1, {'hair': SHIRTS[i % 7]})
            if show_named and nm:
                name_tag(c, x, y - 610 * s, nm[:14], "#ff4d6d" if nm in new else "#111111", "#ffffff", 22)
        if pop > shown:
            text(c, f"+{pop - shown} MORE", 760, GROUND + 380, 46, "#ffffff", stroke="#000", sw=10)
    return d


def build_story(st):
    day = st.get("day", 1)
    pop = st["population"]; prev = st.get("prev_population", 0)
    new_named = st.get("new_named", [])
    grow = pop - prev
    E.BGS["town"] = town_bg(st)
    lines = st.get("lines")
    if not lines:
        if day == 1 or pop == 0:
            lines = [
                ("This is Sticky Town. Population: one.", f"STICKY TOWN · DAY {day}"),
                ("That's me. The mayor. And yeah... it's really empty.", None),
                ("But here's the deal. Every new subscriber moves into town.", "1 SUBSCRIBER = 1 CITIZEN"),
                ("Comment I'm in, and your stickman gets your name.", "COMMENT: I'M IN"),
                ("Tomorrow I'll show you who moved in.", None),
                ("Will this become a city... or stay a ghost town?", "SUBSCRIBE TO MOVE IN"),
            ]
        else:
            nn = ", ".join(new_named[:4])
            lines = [
                (f"Sticky Town, day {day}. Yesterday we had {prev} citizens.", f"STICKY TOWN · DAY {day}"),
                (f"Today? {pop}." if grow > 0 else f"Today? Still {pop}. The mayor is worried.", f"POPULATION {pop + 1}"),
            ]
            if new_named:
                lines.append((f"Welcome to town, {nn}!", "NEW CITIZENS"))
            lines += [
                ("Every new subscriber moves in. Comment I'm in to get your name on a stickman.", "COMMENT: I'M IN"),
                (f"Can we hit {((pop // 50) + 1) * 50} by next week?", "SUBSCRIBE TO MOVE IN"),
            ]
    beats = []
    for i, (say, title) in enumerate(lines):
        b = dict(say=say, bg="town", tension=1 if i < len(lines) - 1 else 2,
                 cam=(1.0, 1.06, 540, 1300) if i % 2 == 0 else (1.15, 1.08, 600, 1450))
        if title: b["title"] = title
        ghosts = 0
        if "moves into town" in say or "moves in" in say: ghosts = 3
        b["draw"] = residents_layer(st, ghosts=ghosts)
        if i == 0: b["sfx"] = [("ding", 0.1, 0.6)]
        if "COMMENT" in (title or ""): b["sfx"] = [("pop", 0.2, 0.8)]
        beats.append(b)
    return dict(slug=f"town{day}", mood="comedy", tag="STICKY TOWN", speed=1.05,
                voices={'n': 'am_michael'}, chars={}, beats=beats, tail=0.8)


if __name__ == "__main__":
    import render
    st = json.load(open(sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].endswith('.json') else STATE))
    out = sys.argv[1]
    pf = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
    total, tl = render.build(build_story(st), out, pf)
    print("total", round(total, 2))
