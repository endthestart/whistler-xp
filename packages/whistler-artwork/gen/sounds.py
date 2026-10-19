#!/usr/bin/env python3
"""Synthesize Whistler's original sound scheme (16-bit stereo WAV files).

usage: sounds.py OUTDIR

File names follow the freedesktop sound naming spec so the "whistler" sound
theme can use them directly; desktop-login is the startup chime.
"""
import os
import sys
import wave

import numpy as np

RATE = 44100


def env(t, start, length, attack, release_frac=0.45):
    e = np.zeros_like(t)
    s, end = int(start * RATE), int(min(t[-1] + 1 / RATE, start + length) * RATE)
    seg = t[s:end] - start
    a = np.clip(seg / max(attack, 1e-4), 0, 1)
    r = np.exp(-np.maximum(seg - attack, 0) / max(length * release_frac, 1e-3))
    e[s:end] = a * a * (3 - 2 * a) * r
    return e


def tone(t, freq, start, length, amp, attack=0.01, harmonics=(1.0, 0.3, 0.12, 0.05), release=0.45):
    sig = sum(h * np.sin(2 * np.pi * freq * (i + 1) * t + i * 0.7) for i, h in enumerate(harmonics))
    return amp * env(t, start, length, attack, release) * sig


def bell(t, freq, start, length, amp):
    return tone(t, freq, start, length, amp, attack=0.004, harmonics=(1.0, 0.0, 0.32, 0.0, 0.14, 0.05),
                release=0.3)


def write(path, left, right=None, echo=0.0, delay=0.19):
    if right is None:
        right = left.copy()
    if echo:
        d = int(delay * RATE)
        left = left.copy()
        right = right.copy()
        left[d:] += echo * right[:-d]
        right[d:] += echo * left[:-d]
    n = len(left)
    fade = np.ones(n)
    tail = min(int(0.05 * RATE), n)
    fade[-tail:] = np.linspace(1, 0, tail)
    left, right = left * fade, right * fade
    peak = max(np.abs(left).max(), np.abs(right).max(), 1e-6)
    data = (np.stack([left, right], axis=1) / peak * 0.8 * 32767).astype("<i2").tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)


def timeline(seconds):
    return np.linspace(0, seconds, int(RATE * seconds), endpoint=False)


def startup(out):
    """Soft rising major-chord swell with bell-like arpeggio on top."""
    t = timeline(4.2)
    left, right = np.zeros_like(t), np.zeros_like(t)
    pads = [(155.56, 0.0, 4.0, 0.22), (233.08, 0.05, 3.9, 0.18), (311.13, 0.1, 3.8, 0.15), (392.00, 0.15, 3.6, 0.12)]
    for i, (f, s, l, a) in enumerate(pads):
        sig = tone(t, f, s, l, a, attack=0.9)
        left += sig * (0.6 + 0.1 * i)
        right += sig * (0.9 - 0.1 * i)
    for i, (f, s, l, a) in enumerate([(622.25, 0.55, 2.8, 0.10), (783.99, 0.95, 2.6, 0.09),
                                      (932.33, 1.35, 2.5, 0.085), (1244.51, 1.80, 2.3, 0.07)]):
        sig = bell(t, f, s, l, a)
        pan = 0.3 + 0.13 * i
        left += sig * (1 - pan)
        right += sig * pan
    write(os.path.join(out, "system-bootup.wav"), left, right, echo=0.25, delay=0.23)


def login(out):
    """Shorter welcome chime for later log-ons."""
    t = timeline(2.2)
    left = np.zeros_like(t)
    left += tone(t, 233.08, 0.0, 2.0, 0.14, attack=0.25)
    for f, s, a in ((622.25, 0.05, 0.10), (783.99, 0.30, 0.09), (932.33, 0.55, 0.08)):
        left += bell(t, f, s, 1.6, a)
    write(os.path.join(out, "desktop-login.wav"), left, echo=0.2)


def logout(out):
    t = timeline(2.6)
    left = np.zeros_like(t)
    for f, s, a in ((932.33, 0.0, 0.10), (783.99, 0.28, 0.10), (622.25, 0.56, 0.10)):
        left += bell(t, f, s, 2.0, a)
    left += tone(t, 155.56, 0.0, 2.4, 0.14, attack=0.3)
    left += tone(t, 233.08, 0.1, 2.3, 0.10, attack=0.3)
    write(os.path.join(out, "desktop-logout.wav"), left, echo=0.2)


def shutdown(out):
    t = timeline(3.0)
    left = np.zeros_like(t)
    for f, s in ((783.99, 0.0), (622.25, 0.3), (466.16, 0.6), (311.13, 0.9)):
        left += bell(t, f, s, 2.0, 0.1)
    left += tone(t, 116.54, 0.6, 2.4, 0.15, attack=0.4)
    write(os.path.join(out, "system-shutdown.wav"), left, echo=0.22)


def simple(out, name, notes, seconds, echo=0.1, kind="bell"):
    t = timeline(seconds)
    sig = np.zeros_like(t)
    for f, s, l, a in notes:
        sig += bell(t, f, s, l, a) if kind == "bell" else tone(t, f, s, l, a, attack=0.005)
    write(os.path.join(out, name + ".wav"), sig, echo=echo)


def crumple(out):
    t = timeline(0.6)
    rng = np.random.default_rng(42)
    noise = rng.standard_normal(len(t))
    # band-limit by smoothing, then chop into crackles
    noise = np.convolve(noise, np.ones(6) / 6, mode="same")
    crackle = (rng.random(len(t)) < 0.02).astype(float)
    crackle = np.convolve(crackle, np.exp(-np.arange(400) / 60), mode="same")
    sig = noise * (0.3 + crackle) * np.exp(-t / 0.3)
    write(os.path.join(out, "trash-empty.wav"), sig)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "sounds"
    os.makedirs(out, exist_ok=True)
    startup(out)
    login(out)
    logout(out)
    shutdown(out)
    simple(out, "dialog-information", [(1046.5, 0.0, 0.9, 0.2), (1567.98, 0.0, 0.7, 0.06)], 1.0)
    simple(out, "dialog-warning", [(659.25, 0.0, 0.8, 0.2), (987.77, 0.0, 0.6, 0.08)], 1.0)
    simple(out, "dialog-error", [(392.0, 0.0, 0.5, 0.2), (311.13, 0.16, 0.7, 0.2)], 1.0, kind="tone")
    simple(out, "dialog-question", [(880.0, 0.0, 0.5, 0.16), (1174.66, 0.14, 0.7, 0.16)], 1.0)
    simple(out, "bell", [(1318.51, 0.0, 0.5, 0.2)], 0.6)
    simple(out, "message-new-instant", [(1567.98, 0.0, 0.4, 0.14), (2093.0, 0.08, 0.5, 0.12)], 0.7)
    simple(out, "device-added", [(587.33, 0.0, 0.4, 0.18), (880.0, 0.12, 0.6, 0.18)], 0.9)
    simple(out, "device-removed", [(880.0, 0.0, 0.4, 0.18), (587.33, 0.12, 0.6, 0.18)], 0.9)
    simple(out, "battery-low", [(987.77, 0.0, 0.3, 0.2), (987.77, 0.35, 0.3, 0.2)], 0.9, kind="tone")
    crumple(out)


if __name__ == "__main__":
    main()
