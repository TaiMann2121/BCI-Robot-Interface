#!/usr/bin/env python3
"""
piano_listener.py — plays the physical piano's notes on the computer.

The Arduino is only a key scanner: it reports `P <id>` / `R <id>` over USB
serial and makes no sound of its own. This script turns those events into
audio. That split exists because 18 switches use every usable pin on an Uno,
leaving none for a speaker — and it matches the BCI2000 simulator, which
already plays its notes through psychopy.sound.

Requires: pyserial, numpy, and pygame  ->  pip install pyserial numpy pygame

Examples
--------
  python piano_listener.py --port COM5        # normal use
  python piano_listener.py --test             # play every note, no hardware
  python piano_listener.py --port COM5 --echo # also print each event
"""

import argparse
import sys
import time

try:
    import numpy as np
except ImportError:
    sys.exit("numpy is required:  pip install numpy")

N_WHITE, N_BLACK = 11, 7
N_KEYS = N_WHITE + N_BLACK

# ---------------------------------------------------------------- notes ----
# White keys are the simulator's own table, unchanged
# (Piano_Application_vel.py:753) so the physical piano and the on-screen one
# sound identical.
WHITE_HZ = [233.08, 246.94, 261.63, 293.66, 329.63,
            349.23, 392.00, 440.00, 493.88, 523.25, 554.36]
WHITE_NAME = ["Bb3", "B3", "C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5", "Db5"]

# Black keys sit in the white-key gaps [0,2,3,5,6,7,9]. Five of them land on a
# real sharp. The outer two do not: the simulator's padding keys are already a
# semitone apart (Bb3-B3 and C5-Db5), so there is no note between them. Those
# two continue the scale outwards instead — they are decorative keys the task
# never presses, so change these freely if the supervisor prefers other values
# (setting one to 0 makes that key silent).
BLACK_GAP  = [0, 2, 3, 5, 6, 7, 9]
BLACK_HZ   = [220.00, 277.18, 311.13, 369.99, 415.30, 466.16, 587.33]
BLACK_NAME = ["A3*", "C#4", "D#4", "F#4", "G#4", "A#4", "D5*"]

NOTE_HZ   = WHITE_HZ + BLACK_HZ
NOTE_NAME = WHITE_NAME + BLACK_NAME


def label(key_id):
    if key_id < N_WHITE:
        return f"white {key_id} ({NOTE_NAME[key_id]})"
    k = key_id - N_WHITE
    return f"black {BLACK_GAP[k]}/{BLACK_GAP[k]+1} ({NOTE_NAME[key_id]})"


# ---------------------------------------------------------------- audio ----
SAMPLE_RATE = 44100


def render(freq, seconds=2.5):
    """One note as a stereo int16 buffer.

    A plain sine sounds thin and clicks on release, so this adds a couple of
    quiet harmonics and an attack/decay envelope — closer to a struck string
    and, more practically, free of clicks at note boundaries.
    """
    if freq <= 0:
        return np.zeros((int(SAMPLE_RATE * 0.05), 2), dtype=np.int16)
    t = np.linspace(0, seconds, int(SAMPLE_RATE * seconds), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t)
            + 0.25 * np.sin(2 * np.pi * 2 * freq * t)
            + 0.12 * np.sin(2 * np.pi * 3 * freq * t))
    attack = np.clip(t / 0.006, 0, 1)          # ~6 ms, avoids a click
    decay = np.exp(-t * 1.6)
    wave *= attack * decay
    wave /= np.max(np.abs(wave)) or 1.0
    mono = (wave * 0.28 * 32767).astype(np.int16)
    return np.column_stack([mono, mono])


class Audio:
    """pygame.mixer wrapper. It gives polyphony for free, which the Arduino's
    tone() never could — overlapping notes just work."""

    def __init__(self):
        import pygame
        self.pygame = pygame
        # 512-frame buffer keeps output latency near 12 ms; the whole chain
        # then lands in the same range as a real piano action (~30 ms).
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(N_KEYS + 4)
        self.sounds = [pygame.sndarray.make_sound(render(f)) for f in NOTE_HZ]
        self.channels = {}

    def press(self, key_id):
        ch = self.sounds[key_id].play()
        if ch:
            self.channels[key_id] = ch

    def release(self, key_id):
        ch = self.channels.pop(key_id, None)
        if ch:
            ch.fadeout(140)        # stands in for a piano damper

    def close(self):
        self.pygame.mixer.quit()


# ---------------------------------------------------------------- main -----
def run_test(audio):
    print("Playing every note. White keys first, then black.\n")
    for i in range(N_KEYS):
        print(f"  {i:2d}  {label(i)}")
        audio.press(i)
        time.sleep(0.45)
        audio.release(i)
        time.sleep(0.05)
    time.sleep(0.5)


def run_serial(audio, port, baud, echo):
    try:
        import serial
    except ImportError:
        sys.exit("pyserial is required:  pip install pyserial")

    with serial.Serial(port, baud, timeout=0.05) as ser:
        time.sleep(2)                     # the board resets when the port opens
        ser.reset_input_buffer()
        print(f"Listening on {port}. Ctrl-C to stop.\n")
        buf = ""
        while True:
            data = ser.read(256).decode("ascii", errors="replace")
            if data:
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    handle(line.strip(), audio, echo)
            else:
                time.sleep(0.001)


def handle(line, audio, echo):
    if not line:
        return
    parts = line.split()
    if len(parts) == 2 and parts[0] in ("P", "R"):
        try:
            key_id = int(parts[1])
        except ValueError:
            return
        if not 0 <= key_id < N_KEYS:
            print(f"  ignoring out-of-range key id {key_id}")
            return
        if parts[0] == "P":
            audio.press(key_id)
            if echo:
                print(f"  press   {label(key_id)}")
        else:
            audio.release(key_id)
            if echo:
                print(f"  release {label(key_id)}")
    else:
        print(f"  [board] {line}")       # READY, PONG, key listings


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="serial port, e.g. COM5 or /dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--test", action="store_true",
                    help="play every note once and exit — no board needed")
    ap.add_argument("--echo", action="store_true", help="print each key event")
    args = ap.parse_args()

    if not args.test and not args.port:
        ap.error("give --port, or --test to check audio without the board")

    try:
        audio = Audio()
    except ImportError:
        sys.exit("pygame is required:  pip install pygame")

    try:
        if args.test:
            run_test(audio)
        else:
            run_serial(audio, args.port, args.baud, args.echo)
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        audio.close()


if __name__ == "__main__":
    main()
