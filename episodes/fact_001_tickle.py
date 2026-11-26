# Daily fact: why you can't tickle yourself
from engine import *
A = {'acc': {'hair': '#2a2a2a'}}
B = {'acc': {'hair_long': '#7a3a18', 'dress': '#3aa0a0'}}
def brain(c, tt, bt, dur):
    import math
    p = min(1, bt / 0.4); s = 1 + 0.03 * math.sin(tt * 4)
    c.save(); c.translate(620, 1000); c.scale(p * s, p * s)
    for dx, dy, r in [(-120, -40, 130), (0, -90, 140), (120, -40, 130), (-60, 60, 120), (80, 60, 120)]:
        circle(c, dx, dy, r, "#ff9fb8")
    for dx, dy, r in [(-120, -40, 80), (0, -90, 90), (120, -40, 80)]:
        c.set_line_width(10); src(c, "#e06b8b"); c.arc(dx, dy, r, 0.5, 2.6); c.stroke()
    circle(c, 60, 170, 70, "#ffd23f"); text(c, "!", 60, 170, 80, "#111111")
    c.restore()

STORY = dict(
    slug="fact_tickle", mood="comedy", tag="STICKY FACTS", speed=1.07,
    voices={'n': 'af_heart'}, chars={'a': A, 'b': B},
    beats=[
        dict(say="Try to tickle yourself. Go on. Nothing, right?", title="TRY TO TICKLE YOURSELF", bg="living",
             actors=[dict(c='a', x=540, pose='shrug', face='blank')], tension=1, sfx=[("boing", 0.3, 0.5)]),
        dict(say="But when someone else does it, you lose your mind.", bg="living",
             actors=[dict(c='a', x=450, pose='cry_happy', face='cry'), dict(c='b', x=700, pose='point', face='smirk', dir=-1)],
             tension=1, shake=6),
        dict(say="Here's why. Your brain has a part called the cerebellum.", title="THE CEREBELLUM", bg="rays", draw=brain, tension=1),
        dict(say="Every time you move, it predicts exactly what you'll feel.", bg="rays", title="IT PREDICTS EVERYTHING", draw=brain, actors=[dict(c='a', x=300, pose='think', face='neutral')], tension=1),
        dict(say="So when your own fingers move, your brain already knows. No surprise. No tickle.", bg="living",
             actors=[dict(c='a', x=540, pose='think', face='neutral')], tension=1),
        dict(say="Scientists even built a robot to tickle people on a delay.", title="TICKLE ROBOT", bg="office", actors=[dict(c='a', x=380, pose='sit', face='worried'), dict(x=720, pose='point', face='blank', dir=-1, acc={'glasses': 1}, col='#8899aa')], tension=2),
        dict(say="Add just a fraction of a second, and suddenly, it tickles again!", bg="office",
             actors=[dict(c='a', x=540, pose='cry_happy', face='cry')], shake=8, tension=2, sfx=[("pop", 0.3)]),
        dict(say="Your brain is basically spoiling the surprise. Did you just try it? Comment yes or no.",
             title="DID YOU TRY IT?", bg="rays", actors=[dict(c='a', x=540, pose='point', face='grin')], tension=1, min=3.5),
    ])
