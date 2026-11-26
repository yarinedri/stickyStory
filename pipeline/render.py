import os, sys, re, math, random, hashlib, subprocess, wave, importlib, json
import numpy as np
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E
import audio as A

SR = A.SR
CACHE = "/tmp/ss/tts_cache"; os.makedirs(CACHE, exist_ok=True)
_kok = None

def kokoro():
    global _kok
    if _kok is None:
        from kokoro_onnx import Kokoro
        _kok = Kokoro('/tmp/ss/models/kokoro.onnx', '/tmp/ss/models/voices.bin')
    return _kok

def tts(text, voice, speed):
    key = hashlib.md5(f"{voice}|{speed}|{text}".encode()).hexdigest()
    p = f"{CACHE}/{key}.npy"
    if os.path.exists(p):
        return np.load(p)
    s, sr = kokoro().create(text, voice=voice, speed=speed, lang='en-us')
    s = np.asarray(s, dtype=np.float64)
    # trim silence
    thr = 0.01 * np.max(np.abs(s))
    nz = np.where(np.abs(s) > thr)[0]
    if len(nz): s = s[max(0, nz[0] - 600): nz[-1] + 1200]
    # resample to 48k
    x = np.arange(len(s)) / sr
    xn = np.arange(int(len(s) / sr * SR)) / SR
    y = np.interp(xn, x, s)
    np.save(p, y)
    return y

def words_of(text):
    return text.split()

def build(story, out_path, preview_frames=None):
    voices = story['voices']; speed = story.get('speed', 1.08)
    chars = story.get('chars', {})
    beats = story['beats']
    # ---- audio per beat
    tl = []; t = 0.35
    narr_segments = []; caption_words = []
    for b in beats:
        lines = b.get('say', [])
        if isinstance(lines, str): lines = [('n', lines)]
        pre = b.get('pre', 0.0)
        cur = t + pre
        for vk, txt in lines:
            v = voices.get(vk, vk)
            sp = speed * (story.get('vspeed', {}).get(vk, 1.0))
            y = tts(txt.replace('“', '"').replace('”', '"'), v, sp)
            vol = story.get('vgain', {}).get(vk, 1.0)
            narr_segments.append((cur, y * vol))
            d = len(y) / SR
            ws = words_of(txt)
            wts = [len(re.sub(r'[^A-Za-z0-9$]', '', w_)) + 2.5 for w_ in ws]
            tot = sum(wts); acc = 0
            # chunking
            chunk = []; chunks = []
            for i, w_ in enumerate(ws):
                chunk.append(i)
                if len(chunk) >= b.get('chunk', 3) or re.search(r'[.,!?:;…]["\']?$', w_):
                    chunks.append(chunk); chunk = []
            if chunk: chunks.append(chunk)
            starts = []
            for i, w_ in enumerate(ws):
                starts.append(cur + 0.03 + d * 0.96 * acc / tot); acc += wts[i]
            for ch in chunks:
                cw = [ws[i].upper() for i in ch]
                for j, i in enumerate(ch):
                    end = starts[i + 1] if i + 1 < len(ws) else cur + d
                    caption_words.append(dict(t0=starts[i], t1=end, words=cw, idx=j))
            cur += d + 0.14
        dur = max(b.get('min', 1.0), cur - t + b.get('post', 0.18))
        tl.append((t, dur))
        t += dur
    total = t + story.get('tail', 0.6)
    # extend last caption gaps
    for i, cw in enumerate(caption_words):
        nxt = caption_words[i + 1]['t0'] if i + 1 < len(caption_words) else total
        cw['hold'] = min(nxt, cw['t1'] + 0.35)
    # ---- mix
    n = int(total * SR)
    narr = np.zeros(n)
    for st, y in narr_segments:
        i = int(st * SR); narr[i:i + len(y)] += y[:max(0, n - i)]
    pk = np.max(np.abs(narr)) or 1
    narr = narr / pk * 0.92
    def tension(x):
        for (st, d), b in zip(tl, beats):
            if st <= x < st + d: return b.get('tension', 0)
        return 0
    drops = [(st, st + d) for (st, d), b in zip(tl, beats) if b.get('drop')]
    mus = A.music(story['mood'], total, tension, drops)
    # duck
    envn = np.convolve(np.abs(narr), np.ones(4800) / 4800, mode='same')
    duck = 1 - 0.45 * np.clip(envn / 0.08, 0, 1)
    mus = mus * duck * story.get('music_gain', 1.0)
    fx = np.zeros(n)
    for (st, d), b in zip(tl, beats):
        for item in b.get('sfx', []):
            name, off = item[0], item[1]
            g = item[2] if len(item) > 2 else 1.0
            y = A.SFX[name]()
            i = int((st + off) * SR)
            if i < n: fx[i:i + len(y)] += y[:n - i] * g
    mix = narr + mus * 0.9 + fx * 0.8
    mix = np.tanh(mix * 1.1) * 0.92
    wav_path = out_path.replace('.mp4', '.wav')
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    # ---- video
    nf = int(total * E.FPS)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, E.W, E.H)
    c = cairo.Context(surf)
    frames = preview_frames
    proc = None
    if frames is None:
        proc = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{E.W}x{E.H}', '-r', str(E.FPS), '-i', '-',
                                 '-i', wav_path, '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k',
                                 '-movflags', '+faststart', '-shortest', out_path], stdin=subprocess.PIPE)
        frames = range(nf)
    ci = 0
    for fi in frames:
        tt = fi / E.FPS
        bi = 0
        for k, (st, d) in enumerate(tl):
            if tt >= st: bi = k
        st, d = tl[bi]; b = beats[bi]
        bt = max(0.0, tt - st)
        if tt < tl[0][0]: bt = 0
        draw_frame(c, story, b, bt, d, tt, chars)
        # captions
        cap = None
        for cw in caption_words:
            if cw['t0'] <= tt < cw['hold']: cap = cw
        if cap and not b.get('nocap'):
            E.draw_caption(c, cap['words'], cap['idx'], tt - cap['t0'], y=b.get('cap_y', 1730))
        # brand + progress
        E.rrect(c, 40, 92, 330, 56, 14); E.src(c, (0.05, 0.05, 0.07, 0.85)); c.fill()
        E.text(c, story.get('tag', 'STICKY STORY'), 205, 120, 30, "#ffffff")
        E.rect(c, 0, 0, E.W, 14, (0, 0, 0, 0.5)); E.rect(c, 0, 0, E.W * tt / total, 14, "#ffe600")
        surf.flush()
        if proc:
            proc.stdin.write(bytes(surf.get_data()))
        else:
            surf.write_to_png(f"{out_path}_{fi:05d}.png")
    if proc:
        proc.stdin.close(); proc.wait()
    return total, tl

def draw_frame(c, story, b, bt, dur, tt, chars):
    c.save()
    c.set_operator(cairo.OPERATOR_SOURCE); E.rect(c, 0, 0, E.W, E.H, "#000000"); c.set_operator(cairo.OPERATOR_OVER)
    z0, z1, fx, fy = b.get('cam', (1.1, 1.18, 540, 1150))
    u = E.ease(bt / max(dur, 0.1)) if b.get('cam_ease', True) else bt / max(dur, 0.1)
    z = z0 + (z1 - z0) * u
    if b.get('punch', True):
        z *= 1 + 0.04 * (1 - E.ease(bt / 0.3))
    sh = b.get('shake', 0)
    ox = oy = 0
    if sh:
        a = sh * math.exp(-bt * 3.5) + b.get('rumble', 0)
        r = random.Random(int(tt * 60))
        ox, oy = (r.random() - .5) * a, (r.random() - .5) * a
    c.translate(fx + ox, fy + oy); c.scale(z, z); c.translate(-fx, -fy)
    bgk = dict(b.get('bgk', {})); bgk['bt'] = bt; bgk['dur'] = dur
    E.BGS[b.get('bg', 'solid')](c, tt, **bgk)
    for pr in b.get('props', []):
        draw_prop(c, pr, tt, bt)
    for a in b.get('actors', []):
        draw_actor(c, a, tt, bt, dur, chars)
    for pr in b.get('fg', []):
        draw_prop(c, pr, tt, bt)
    if b.get('draw'):
        b['draw'](c, tt, bt, dur)
    c.restore()
    E.vignette(c, b.get('vig', 0.45))
    if b.get('dark_overlay'):
        E.rect(c, 0, 0, E.W, E.H, (0, 0, 0.05, b['dark_overlay']))
    if b.get('flash'):
        a = max(0, 1 - bt / 0.25)
        if a > 0: E.rect(c, 0, 0, E.W, E.H, (1, 1, 1, a))
    if bt < 0.12 and b.get('cut_black'):
        E.rect(c, 0, 0, E.W, E.H, (0, 0, 0, 1 - bt / 0.12))
    title = b.get('title')
    if title:
        ta = b.get('title_at', 0)
        if bt >= ta:
            E.draw_title(c, title, bt - ta, y=b.get('title_y', 330), col=b.get('title_col', '#ffe600'), box=b.get('title_box', '#111111'), size=b.get('title_size', 80))

def draw_prop(c, pr, tt, bt):
    name, x, y = pr[0], pr[1], pr[2]
    if callable(x): x = x(bt)
    if callable(y): y = y(bt)
    s = pr[3] if len(pr) > 3 else 1.0
    k = dict(pr[4]) if len(pr) > 4 else {}
    at = k.pop('at', 0)
    if bt < at: return
    if 'pop' in k:
        k.pop('pop'); p = E.ease_out_back((bt - at) / 0.3); s = s * p
        if s <= 0.01: return
    for kk, vv in list(k.items()):
        if callable(vv) and kk not in ('who', 'draw'): k[kk] = vv(bt)
    E.prop(c, name, x, y, s, tt, **k)

def draw_actor(c, a, tt, bt, dur, chars):
    ch = chars.get(a.get('c'), {})
    acc = dict(ch.get('acc', {})); acc.update(a.get('acc', {}))
    x = a.get('x', 540); y = a.get('y', E.GROUND); s = a.get('s', 1.0) * ch.get('s', 1.0)
    pose = a.get('pose', 'stand'); face = a.get('face', 'neutral'); dir_ = a.get('dir', 1)
    at = a.get('at', 0)
    if bt < at: return
    lt = bt - at
    if 'switch' in a:  # [(time, pose, face, dir?)]
        for item in a['switch']:
            if lt >= item[0]:
                pose = item[1] or pose; face = item[2] or face
                if len(item) > 3: dir_ = item[3]
    if 'walk' in a:
        x0, x1, t0, t1 = a['walk']
        if lt < t0: x = x0
        elif lt < t1:
            x = x0 + (x1 - x0) * (lt - t0) / (t1 - t0); pose = a.get('walk_pose', 'walk')
        else: x = x1
    if a.get('enter'):
        e = E.ease(lt / 0.4)
        off = (1 - e) * (700 if a['enter'] == 'r' else -700)
        x += off
        if e < 1: pose = 'walk' if a.get('walk_in', True) else pose
    if a.get('pop'):
        s *= E.ease_out_back(lt / 0.3)
        if s < 0.01: return
    E.stick(c, x, y, s, pose, tt, face, dir_, acc, outline=a.get('outline', True), look=a.get('look', 0))

if __name__ == "__main__":
    mod = importlib.import_module(sys.argv[1])
    out = sys.argv[2]
    pf = None
    if len(sys.argv) > 3:
        pf = [int(x) for x in sys.argv[3].split(',')]
    total, tl = build(mod.STORY, out, pf)
    print("total", round(total, 2), "beats", [(round(s, 2), round(d, 2)) for s, d in tl])
