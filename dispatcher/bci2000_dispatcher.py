#! /usr/bin/env python3
"""
BCI2000 Piano Dispatcher
------------------------
The piano task streams ALL control data as a single tab-separated record on one
UDP port (5005) at 8 Hz. Both the arm controller (Python) and the hand
controller (C++) need data out of that one stream, but two processes cannot
reliably share a single UDP port — a unicast localhost datagram is delivered to
only one bound socket.

This dispatcher is the fix: it is the only process that binds 5005. It parses
each BCI2000 watch packet, cleans it up, and re-broadcasts the 8-field record to
two local ports so each controller can bind its own port and pick the fields it
needs:

    BCI2000  ──5005──▶  dispatcher  ──5006──▶  arm_controller.py
                                    ──5007──▶  myAllegroHand.exe

Stream field order (from the SigGen_Piano_vel.bat ADD WATCH line):
    CurrentTrial  InnerTrialCount  ArmPred_X  FingerMovePhase
    CopilotFingerPred  targetKeyIndex  pressedKeyIndex  ArmCurrentIndex

BCI2000 prepends a frame counter and appends a trailing tab + CRLF to every
watch packet (see BCI2000 Piano/PianoStateReading.py). Rather than strip a fixed
number of bytes — which breaks the moment the counter reaches two digits — we
split on tabs, drop empty tokens, and keep the last 8 fields. That is robust to
the counter width and the trailing tab.

The forwarded record is the same 8 fields, tab-separated, with NO leading
counter and NO trailing junk, so the downstream parsers are trivial and
identical.

Usage:
    python bci2000_dispatcher.py
Run this before arm_controller.py and myAllegroHand.exe.
"""

import socket

# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
UDP_IP        = "127.0.0.1"
LISTEN_PORT   = 5005      # the real BCI2000 stream (single port, 8 Hz)
ARM_PORT      = 5006      # forwarded to arm_controller.py
HAND_PORT     = 5007      # forwarded to myAllegroHand.exe

NUM_FIELDS    = 8         # the 8 watched piano-stream variables

# Field indices within the cleaned record (shared by all downstream parsers)
F_CURRENT_TRIAL      = 0
F_INNER_TRIAL_COUNT  = 1
F_ARM_PRED_X         = 2
F_FINGER_MOVE_PHASE  = 3
F_COPILOT_FINGER_PRED = 4
F_TARGET_KEY_INDEX   = 5
F_PRESSED_KEY_INDEX  = 6
F_ARM_CURRENT_INDEX  = 7


def parse_watch_packet(raw):
    """
    Turns a raw BCI2000 watch packet into the 8-field piano record.

    Splits on tabs, drops empty tokens (handles the trailing tab), and returns
    the LAST 8 fields as a list of strings — dropping BCI2000's leading frame
    counter regardless of how many digits it has. Returns None if the packet
    doesn't contain at least 8 usable fields.
    """
    text = raw.decode(errors="ignore").strip()
    tokens = [t for t in text.split("\t") if t != ""]
    if len(tokens) < NUM_FIELDS:
        return None
    return tokens[-NUM_FIELDS:]


def main():
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((UDP_IP, LISTEN_PORT))

    out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("=" * 60)
    print("BCI2000 Piano Dispatcher")
    print("  Listening : {}:{}  (single piano stream, 8 Hz)".format(UDP_IP, LISTEN_PORT))
    print("  Arm  -> {}:{}".format(UDP_IP, ARM_PORT))
    print("  Hand -> {}:{}".format(UDP_IP, HAND_PORT))
    print("Start this before arm_controller.py and myAllegroHand.exe.")
    print("=" * 60)

    packet_count = 0
    while True:
        data, _ = listen_sock.recvfrom(1024)
        fields = parse_watch_packet(data)
        if fields is None:
            print("Bad packet, skipping: {!r}".format(data))
            continue

        record = "\t".join(fields).encode()
        out_sock.sendto(record, (UDP_IP, ARM_PORT))
        out_sock.sendto(record, (UDP_IP, HAND_PORT))

        packet_count += 1
        if packet_count % 40 == 0:   # ~ every 5 s at 8 Hz
            print("  fwd {}: ArmPred_X={} FingerMovePhase={} CopilotFingerPred={} "
                  "targetKey={} pressedKey={} armIdx={}".format(
                      packet_count,
                      fields[F_ARM_PRED_X],
                      fields[F_FINGER_MOVE_PHASE],
                      fields[F_COPILOT_FINGER_PRED],
                      fields[F_TARGET_KEY_INDEX],
                      fields[F_PRESSED_KEY_INDEX],
                      fields[F_ARM_CURRENT_INDEX]))


if __name__ == "__main__":
    main()
