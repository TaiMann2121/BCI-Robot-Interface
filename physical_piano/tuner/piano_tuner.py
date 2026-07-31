#!/usr/bin/env python3
"""
piano_tuner.py - tune the physical piano's electronic tones from a computer.

Talks to piano_firmware.ino over USB serial. You can set each key's pitch,
audition it, load/save presets as JSON, and push a whole preset to the board
(which can then `save` it to EEPROM so it persists without a computer attached).

Requires: pyserial  ->  pip install pyserial

Examples
--------
  # interactive session on Windows COM5 (see Device Manager for the port)
  python piano_tuner.py --port COM5

  # push a saved preset then persist it to the Arduino's EEPROM
  python piano_tuner.py --port COM5 --load deep.json --push --save

Interactive commands (type `help`):
  list                 show current key -> Hz from the board
  set <i> <hz>         set key i (0..10); 0 = silent
  play <i>             audition key i
  push                 send every key in the local preset to the board
  save                 tell the board to store its current tuning to EEPROM
  load-board           reload the board's tuning from EEPROM
  reset                restore the board's built-in defaults
  savefile <path>      write the local preset to a JSON file
  loadfile <path>      read a JSON preset into the local table (then `push`)
  quit
"""

import argparse
import json
import sys
import time

try:
    import serial  # pyserial
except ImportError:
    sys.exit("pyserial is required: pip install pyserial")

NUM_KEYS = 11
# Same defaults as the firmware / simulator (Piano_Application_vel.py:753).
DEFAULT_FREQ = [233, 247, 262, 294, 330, 349, 392, 440, 494, 523, 554]
LABELS = ["", "", "C", "D", "E", "F", "G", "A", "B", "", ""]


def send(ser, line, wait=0.15):
    """Send one command line and echo whatever the board replies."""
    ser.write((line + "\n").encode())
    time.sleep(wait)
    out = ser.read(ser.in_waiting or 1).decode(errors="replace")
    if out.strip():
        print(out.strip())
    return out


def push_preset(ser, preset):
    for i, hz in enumerate(preset):
        send(ser, f"set {i} {int(hz)}", wait=0.05)
    print("pushed preset to board")


def load_json(path):
    with open(path) as f:
        data = json.load(f)
    freqs = data["freq"] if isinstance(data, dict) else data
    if len(freqs) != NUM_KEYS:
        raise ValueError(f"preset must have {NUM_KEYS} frequencies, got {len(freqs)}")
    return [int(x) for x in freqs]


def save_json(path, preset):
    labeled = {LABELS[i] or f"key{i}": preset[i] for i in range(NUM_KEYS)}
    with open(path, "w") as f:
        json.dump({"freq": preset, "labeled": labeled}, f, indent=2)
    print(f"wrote {path}")


def interactive(ser, preset):
    print("connected. type `help` for commands, `quit` to exit.")
    send(ser, "list")
    while True:
        try:
            raw = input("tuner> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit"):
            break
        elif cmd == "help":
            print(__doc__)
        elif cmd == "push":
            push_preset(ser, preset)
        elif cmd == "savefile" and len(parts) == 2:
            save_json(parts[1], preset)
        elif cmd == "loadfile" and len(parts) == 2:
            try:
                preset[:] = load_json(parts[1])
                print("loaded into local preset (use `push` to send to board)")
            except (OSError, ValueError, KeyError) as e:
                print(f"error: {e}")
        elif cmd == "load-board":
            send(ser, "load")
        elif cmd == "set" and len(parts) == 3:
            try:
                i, hz = int(parts[1]), int(parts[2])
                preset[i] = hz          # keep local copy in sync
            except (ValueError, IndexError):
                print("usage: set <i> <hz>")
                continue
            send(ser, f"set {i} {hz}")
        else:
            # Pass list / play / stop / save / reset straight through.
            send(ser, raw)
    print("bye")


def main():
    ap = argparse.ArgumentParser(description="Tune the physical piano's electronic tones.")
    ap.add_argument("--port", required=True, help="serial port, e.g. COM5 or /dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--load", metavar="JSON", help="load a preset file into the local table on start")
    ap.add_argument("--push", action="store_true", help="push the loaded preset to the board, then exit unless interactive")
    ap.add_argument("--save", action="store_true", help="after --push, tell the board to persist to EEPROM")
    ap.add_argument("--no-interactive", action="store_true", help="run --load/--push/--save then exit")
    args = ap.parse_args()

    preset = load_json(args.load) if args.load else list(DEFAULT_FREQ)

    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        time.sleep(2)                 # let the board reset after opening the port
        ser.read(ser.in_waiting or 1)  # flush startup banner

        if args.push:
            push_preset(ser, preset)
        if args.save:
            send(ser, "save")

        if not args.no_interactive:
            interactive(ser, preset)


if __name__ == "__main__":
    main()
