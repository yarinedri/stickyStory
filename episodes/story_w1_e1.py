# Weekly story "Room 13" - Episode 1 (A/B ending, top comment decides Ep2)
from engine import *
SAM = {'acc': {'hair': '#3a2a1a'}}
STORY = dict(
    slug="room13_e1", mood="thriller", tag="ROOM 13 · EP 1", speed=1.05,
    voices={'n': 'bm_george', 'sam': 'am_adam', 'land': 'am_michael'},
    chars={'sam': SAM},
    beats=[
        dict(say="Sam moved into the cheapest apartment in the city. Two hundred dollars a month.", title="$200 A MONTH?!",
             bg="hall_out", props=[("door", 760, 1540, 1.0)],
             actors=[dict(c='sam', x=420, pose='hold', face='happy')], sfx=[("ding", 0.2, 0.5)], tension=1),
        dict(say=[('land', "Just one rule. Never open the door at the end of the hall.")], title="ONE RULE.",
             bg="hall_dark", actors=[dict(c='sam', x=380, pose='stand', face='worried'), dict(x=720, pose='point', face='grumpy', dir=-1, acc={'hair': '#888888'})],
             tension=2, cam=(1.1, 1.2, 540, 1000)),
        dict(say="The door had no handle. Just a number. Thirteen.", title="ROOM 13", title_col="#ff3b3b",
             bg="hall_dark", props=[("door", 540, 1540, 1.1, dict(dark=True))], tension=2, cam=(1.0, 1.25, 540, 1050), sfx=[("riser", 0.2, 0.5)]),
        dict(say="The first night, at exactly three AM, Sam heard it.", bg="bedroom_night",
             props=[("bed", 540, 1540), ("clock", 880, 1350, 0.8, dict(txt="3:00"))],
             actors=[dict(c='sam', x=420, y=1520, pose='lie_up', face='sleepy', switch=[(1.2, None, 'shock')])],
             fg=[("blanket", 540, 1540)], tension=2, dark_overlay=0.15),
        dict(say="Knocking. From inside room thirteen.", title="KNOCK. KNOCK.", bg="hall_dark",
             props=[("door", 540, 1540, 1.1, dict(dark=True))], sfx=[("knock", 0.3), ("knock", 1.5, 0.7)], shake=8, tension=3),
        dict(say="Then something slid under the door. A key. And a note.", bg="hall_dark",
             props=[("door", 540, 1540, 1.1, dict(dark=True)), ("key", 540, 1500, 1.4, dict(pop=1, at=0.6))],
             actors=[dict(c='sam', x=250, pose='scared', face='terrified')], tension=3),
        dict(say="It said: Don't trust the landlord. Open the door.", bg="note",
             bgk=dict(lines=["Don't trust the", "landlord.", "", "OPEN THE DOOR."]), tension=3, sfx=[("heartbeat", 0.0, 0.8)]),
        dict(say="Sam's phone buzzed. A text from the landlord. Did you touch the key?", bg="phone",
             bgk=dict(header="Landlord", msgs=[("them", "Did you touch the key?")]), sfx=[("buzz", 0.4)], tension=3, drop=False),
        dict(say="What should Sam do? A, open room thirteen. Or B, call the landlord. Top comment decides tomorrow's episode.",
             title="A: OPEN IT  ·  B: CALL HIM", bg="hall_dark", props=[("door", 540, 1540, 1.1, dict(dark=True))],
             actors=[dict(c='sam', x=300, pose='think', face='worried', acc={'hold': 'key'})], tension=2, min=4.5),
    ])
