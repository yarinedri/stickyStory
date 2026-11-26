from engine import *

DAN = {'acc': {'headset': 1, 'hair': '#5a3a22'}}
LENA = {'acc': {'hair_long': '#3a2418', 'dress': '#3aa0a0'}}

def split_kitchen(show_man=True):
    def d(c, t, bt, dur):
        pass
    return d

STORY = dict(
    slug="pizza", mood="thriller", speed=1.06,
    voices={'n': 'bm_george', 'dan': 'am_eric', 'lena': 'af_nicole'},
    chars={'dan': DAN, 'lena': LENA},
    beats=[
        dict(say=[('n', "A 911 operator picked up a call. And a woman said..."), ('lena', "Hi. I'd like to order a pizza.")],
             title="SHE CALLED 911 TO ORDER PIZZA", bg="dispatch", props=[("desk_monitors", 540, 1540)],
             actors=[dict(c='dan', x=540, y=1600, pose='sit_talk', face='neutral')], sfx=[("ding", 0.1, 0.5)], tension=1),
        dict(say=[('dan', "Ma'am, this is 911. Not a pizza place.")], bg="dispatch", props=[("desk_monitors", 540, 1540)],
             actors=[dict(c='dan', x=540, y=1600, pose='sit_talk', face='grumpy')], tension=1, cam=(1.2, 1.3, 540, 1000)),
        dict(say=[('lena', "Yes. Large. Pepperoni. Half cheese.")], title="\"LARGE. PEPPERONI.\"", bg="call",
             bgk=dict(name="Unknown caller", sub="911 · 00:19"), tension=1),
        dict(say="He almost hung up. Prank calls happen every single day.", bg="dispatch", props=[("desk_monitors", 540, 1540)],
             actors=[dict(c='dan', x=540, y=1600, pose='type', face='grumpy')], tension=1),
        dict(say="But something in her voice was wrong. Too calm. Too careful.", bg="dispatch",
             actors=[dict(c='dan', x=540, s=1.5, y=1950, pose='think', face='worried')], tension=2, cam=(1.2, 1.32, 540, 950)),
        dict(say=[('dan', "Ma'am... are you in danger right now?")], title="IS SHE IN DANGER?", bg="dispatch",
             actors=[dict(c='dan', x=540, s=1.5, y=1950, pose='phone', face='worried')], tension=2, cam=(1.25, 1.4, 540, 950)),
        dict(say=[('lena', "Yes.")], bg="call", bgk=dict(name="Unknown caller", sub="911 · 00:41"), tension=3, drop=False, min=1.6, post=0.5,
             sfx=[("heartbeat", 0.0, 0.8)]),
        dict(say=[('dan', "Is someone there with you?"), ('lena', "Yes. Can you make it extra large?")], bg="kitchen_night",
             actors=[dict(c='lena', x=700, pose='phone', face='scared', dir=-1, acc={'hold': 'phone'})],
             fg=[("shadowman", 230, 1540, 1.05, dict(alpha=lambda bt: min(1, bt * 0.5)))], tension=3, cam=(1.05, 1.2, 500, 1050)),
        dict(say="He understood. She couldn't talk. Someone was listening.", title="SOMEONE WAS LISTENING", title_col="#ff3b3b",
             bg="kitchen_night", fg=[("shadowman", 380, 1540, 1.2)], actors=[dict(c='lena', x=820, pose='phone', face='terrified', dir=-1, acc={'hold': 'phone'})],
             tension=3, sfx=[("boom", 0.2, 0.7)], shake=12, cam=(1.2, 1.3, 450, 1000)),
        dict(say="He typed her address, sent the nearest patrol car, and kept her on the line. Only yes or no questions.",
             bg="map", bgk=dict(), tension=2, sfx=[("type", 0.0), ("siren", 2.4, 0.5)]),
        dict(say=[('dan', "Is he armed?"), ('lena', "No. No mushrooms.")], title="\"NO MUSHROOMS\"", bg="call",
             bgk=dict(name="Unknown caller", sub="911 · 03:12"), tension=2),
        dict(say="Eight minutes later, her pizza arrived. In a police car.", title="THE PIZZA ARRIVED", bg="street_day",
             dark_overlay=0.55, props=[("police_car", 540, 1600, 1.1)], tension=0, sfx=[("siren", 0.0, 0.8)], flash=True),
        dict(say="The man was arrested. She was safe.", bg="kitchen_night",
             actors=[dict(c='lena', x=640, pose='cry_happy', face='cry', dir=-1), dict(x=360, pose='stand', face='happy', acc={'police': 1})],
             drop=True, tension=0),
        dict(say="Calls like this really happen. That operator didn't hang up. Share this. It could save someone's life.",
             title="SHARE THIS. IT SAVES LIVES.", bg="rays", bgk=dict(col="#0e1626", col2="#16233a"),
             actors=[dict(c='dan', x=540, pose='stand', face='happy', s=1.1)], post=1.2),
    ])
