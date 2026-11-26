import numpy as np, math
SR = 48000
rng = np.random.default_rng(7)

def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(d, 1e-4))
    return e

def lp(x, k=0.1):
    # one-pole lowpass
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += k * (x[i] - acc); y[i] = acc
    return y

def lp_fast(x, win=8):
    if win <= 1: return x
    k = np.ones(win) / win
    return np.convolve(x, k, mode='same')

def noise(n): return rng.standard_normal(n)

def tone(f, dur, harm=(1,), decay=0.5, a=0.005):
    n = int(dur * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * (i + 1) * t) * h for i, h in enumerate(harm))
    return y * env(n, a, decay)

# ---------------- SFX
def sfx_knock():
    out = np.zeros(int(1.2 * SR))
    for k, st in enumerate([0, 0.28, 0.52]):
        n = int(0.18 * SR); t = np.arange(n) / SR
        th = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.05) + lp_fast(noise(n), 12) * np.exp(-t / 0.02) * 0.8
        i = int(st * SR); out[i:i + n] += th
    return out * 0.9

def sfx_creak():
    n = int(1.0 * SR); t = np.arange(n) / SR
    f = 240 + 60 * np.sin(2 * np.pi * 1.3 * t) + 20 * np.sin(2 * np.pi * 23 * t)
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    am = (np.sin(2 * np.pi * 31 * t) > 0.2).astype(float) * 0.6 + 0.4
    e = np.sin(np.pi * t / t[-1]) ** 2
    return lp_fast(saw * am * e, 6) * 0.35

def sfx_whoosh(d=0.5):
    n = int(d * SR); t = np.arange(n) / SR
    x = noise(n); e = np.sin(np.pi * t / t[-1]) ** 2
    y = lp_fast(x, 10) * 0.6 + (x - lp_fast(x, 4)) * 0.2
    return y * e * 0.7

def sfx_boom():
    n = int(2.2 * SR); t = np.arange(n) / SR
    f = 70 * np.exp(-t / 0.4) + 32
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    y += lp_fast(noise(n), 30) * np.exp(-t / 0.15) * 1.5
    return np.tanh(y * 1.6) * 0.9

def sfx_riser(d=1.5):
    n = int(d * SR); t = np.arange(n) / SR
    f = 200 + 1200 * (t / d) ** 2
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15 + lp_fast(noise(n), 3) * 0.25
    return y * (t / d) ** 2

def sfx_click():
    out = np.zeros(int(0.3 * SR))
    for st in (0, 0.09):
        n = int(0.03 * SR); i = int(st * SR); t = np.arange(n) / SR
        out[i:i + n] += noise(n) * np.exp(-t / 0.004) + np.sin(2 * np.pi * 2200 * t) * np.exp(-t / 0.01)
    return out * 0.6

def sfx_buzz():
    out = np.zeros(int(1.0 * SR))
    for st in (0, 0.45):
        n = int(0.32 * SR); t = np.arange(n) / SR; i = int(st * SR)
        out[i:i + n] += np.sign(np.sin(2 * np.pi * 160 * t)) * 0.25 * (1 - np.exp(-t / 0.01))
    return lp_fast(out, 10)

def sfx_ding():
    return (tone(1318, 1.2, (1, .3), 0.35) + tone(1760, 1.2, (1,), 0.3) * 0.6) * 0.35

def sfx_pop():
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = 900 * np.exp(-t / 0.03) + 200
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.04) * 0.5

def sfx_siren(d=3.0):
    n = int(d * SR); t = np.arange(n) / SR
    f = 950 + 350 * np.sin(2 * np.pi * 0.7 * t)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    e = np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.5)
    return y * e * 0.18

def sfx_heartbeat(n_beats=4, bpm=80):
    per = 60 / bpm; out = np.zeros(int((n_beats * per + 0.5) * SR))
    for b in range(n_beats):
        for off, amp in ((0, 1), (0.18, 0.7)):
            m = int(0.15 * SR); t = np.arange(m) / SR; i = int((b * per + off) * SR)
            out[i:i + m] += np.sin(2 * np.pi * 48 * t) * np.exp(-t / 0.05) * amp
    return np.tanh(out * 2) * 0.7

def sfx_boing():
    n = int(0.7 * SR); t = np.arange(n) / SR
    f = 500 * np.exp(-t / 0.25) + 120 + 30 * np.sin(2 * np.pi * 14 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35) * 0.45

def sfx_horn():
    n = int(0.8 * SR); t = np.arange(n) / SR
    f = 420 + 25 * np.sin(2 * np.pi * 7 * t)
    ph = np.cumsum(f) / SR
    y = (2 * (ph % 1) - 1) * np.minimum(1, t / 0.03) * np.minimum(1, (t[-1] - t) / 0.1)
    return lp_fast(y, 4) * 0.25

def sfx_cash():
    d = sfx_ding(); m = int(0.4 * SR); i = int(0.05 * SR)
    d[i:i + m] += lp_fast(noise(m), 2) * env(m, 0.001, 0.1) * 0.2
    return d

def sfx_door():
    n = int(0.6 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.12) + lp_fast(noise(n), 20) * np.exp(-t / 0.06)
    return np.tanh(y * 1.5) * 0.7

def sfx_tick(n=4, per=0.5):
    out = np.zeros(int((n * per + 0.1) * SR))
    for k in range(n):
        m = int(0.02 * SR); t = np.arange(m) / SR; i = int(k * per * SR)
        out[i:i + m] += np.sin(2 * np.pi * (3000 if k % 2 else 2400) * t) * np.exp(-t / 0.004)
    return out * 0.4

def sfx_engine(d=3.0):
    n = int(d * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 45 * t + 2 * np.sin(2 * np.pi * 9 * t)) * 0.5 + lp_fast(noise(n), 40) * 0.4
    e = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.8)
    return y * e * 0.35

def sfx_hiss():
    n = int(0.7 * SR); t = np.arange(n) / SR
    return (noise(n) - lp_fast(noise(n), 3)) * np.exp(-t / 0.25) * 0.25

def sfx_type(d=1.5):
    out = np.zeros(int(d * SR)); k = 0.0
    while k < d - 0.05:
        m = int(0.015 * SR); i = int(k * SR); t = np.arange(m) / SR
        out[i:i + m] += noise(m) * np.exp(-t / 0.003) * 0.4; k += 0.07 + rng.random() * 0.08
    return out

def sfx_scratch():
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 600 * (1 - t / t[-1]) + 80
    y = (2 * ((np.cumsum(f) / SR) % 1) - 1) * np.exp(-t / 0.3)
    return lp_fast(y, 6) * 0.35

SFX = dict(knock=sfx_knock, creak=sfx_creak, whoosh=sfx_whoosh, boom=sfx_boom, riser=sfx_riser, click=sfx_click,
           buzz=sfx_buzz, ding=sfx_ding, pop=sfx_pop, siren=sfx_siren, heartbeat=sfx_heartbeat, boing=sfx_boing,
           horn=sfx_horn, cash=sfx_cash, door=sfx_door, tick=sfx_tick, engine=sfx_engine, hiss=sfx_hiss, type=sfx_type,
           scratch=sfx_scratch)

# ---------------- music
def music(mood, total, tension_fn, drops):
    """tension_fn(t)->0..3, drops: list of (t0,t1) muted."""
    n = int(total * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    tens = np.array([tension_fn(x) for x in np.arange(0, total, 0.05)])
    tens = np.interp(t, np.arange(len(tens)) * 0.05, tens)
    if mood == "thriller":
        # drone
        base = 55.0
        dr = (np.sin(2 * np.pi * base * t) + 0.6 * np.sin(2 * np.pi * base * 1.5 * t + 0.3) + 0.4 * np.sin(2 * np.pi * base * 2.003 * t)
              + 0.25 * np.sin(2 * np.pi * base * 2.38 * t))  # minor-ish cluster
        dr *= 0.5 + 0.3 * np.sin(2 * np.pi * 0.12 * t)
        out += dr * (0.10 + 0.06 * tens)
        # high eerie tone at tension>=2
        hi = np.sin(2 * np.pi * 880 * t + 3 * np.sin(2 * np.pi * 0.3 * t)) * 0.025
        out += hi * np.clip(tens - 1.5, 0, 1)
        # pulse / heartbeat
        bpm = 70 + 25 * tens
        ph = np.cumsum(bpm / 60 / SR)
        frac = ph % 1
        hb = np.sin(2 * np.pi * 50 * frac / (bpm / 60)) * np.exp(-frac * 14) + 0.7 * np.sin(2 * np.pi * 50 * ((frac - 0.22) % 1) / (bpm / 60)) * np.exp(-((frac - 0.22) % 1) * 14)
        out += hb * 0.35 * np.clip(tens - 1, 0, 1.5)
        # ticks
        tk = np.exp(-((ph * 2) % 1) * 200) * np.sin(2 * np.pi * 3000 * t)
        out += tk * 0.05 * np.clip(tens, 0, 1)
        wind = lp_fast(noise(n), 60) * 0.12
        out += wind
    elif mood == "comedy":
        bpm = 116; beat = 60 / bpm
        prog = [(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]
        nb = int(total / beat) + 1
        for b in range(nb):
            chord = prog[(b // 4) % 4]
            st = int(b * beat * SR)
            # bass on beats
            bn = tone(chord[0] / 2, beat * 0.9, (1, .5, .25), 0.12)
            out[st:st + len(bn)] += bn[:max(0, n - st)] * 0.22
            # pluck offbeat
            for sub in (0.5,):
                s2 = int((b + sub) * beat * SR)
                note = chord[(b + int(sub * 2)) % 3] * 2
                pk = tone(note, 0.25, (1, .4, .2), 0.06)
                out[s2:s2 + len(pk)] += pk[:max(0, n - s2)] * 0.12
            # hat
            hh = (noise(int(0.03 * SR)) * env(int(0.03 * SR), 0.0005, 0.008))
            for sub in (0.0, 0.5):
                s3 = int((b + sub) * beat * SR); out[s3:s3 + len(hh)] += hh[:max(0, n - s3)] * 0.05
        # tension makes it sparse; add low drone when tension>=2
        out *= (1 - 0.45 * np.clip(tens - 1, 0, 1))
        out += np.sin(2 * np.pi * 65.4 * t) * 0.08 * np.clip(tens - 1, 0, 1)
        out += np.exp(-((np.cumsum((90 + 30 * tens) / 60 / SR)) % 1) * 14) * np.sin(2 * np.pi * 50 * t) * 0.25 * np.clip(tens - 1.5, 0, 1)
    elif mood == "warm":
        bpm = 76; beat = 60 / bpm
        prog = [(174.6, 220.0, 261.6, 349.2), (220.0, 261.6, 329.6, 440.0), (233.1, 293.7, 349.2, 466.2), (261.6, 329.6, 392.0, 523.3)]
        nb = int(total / (beat / 2)) + 1
        for b in range(nb):
            chord = prog[(b // 8) % 4]
            st = int(b * beat / 2 * SR)
            note = chord[[0, 1, 2, 3, 2, 1, 2, 3][b % 8]]
            pk = tone(note * 2, 1.6, (1, .35, .12, .05), 0.7)
            out[st:st + len(pk)] += pk[:max(0, n - st)] * 0.07
            if b % 8 == 0:
                bs = tone(chord[0] / 2, 3.2, (1, .3), 1.5)
                out[st:st + len(bs)] += bs[:max(0, n - st)] * 0.12
        # simple echo
        d = int(0.32 * SR); e = out.copy(); e[d:] += out[:-d] * 0.35; out = e
        out *= (1 - 0.4 * np.clip(tens - 1, 0, 1))
        out += np.sin(2 * np.pi * 87.3 * t) * 0.07 * np.clip(tens - 0.8, 0, 1)
    # drops
    gain = np.ones(n)
    for a, b in drops:
        i0, i1 = int(a * SR), int(b * SR)
        fade = int(0.08 * SR)
        gain[i0:i1] = 0.0
        gain[max(0, i0 - fade):i0] *= np.linspace(1, 0, min(fade, i0))
    out *= gain
    # fade in/out
    fi = int(0.3 * SR); out[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.2 * SR); out[-fo:] *= np.linspace(1, 0, fo)
    return out
