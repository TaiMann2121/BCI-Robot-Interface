"""
BCI2000 Piano Simulator
-----------------------
Simulates the BCI2000 piano-task UDP output so the dispatcher, arm controller,
and hand controller can be tested without a real BCI2000 session.

Unlike the old two-stream simulator, the piano task sends ONE combined stream:

    UDP 127.0.0.1:5005 @ 8 Hz, tab-separated, one record per packet:
        CurrentTrial  InnerTrialCount  ArmPred_X  FingerMovePhase
        CopilotFingerPred  targetKeyIndex  pressedKeyIndex  ArmCurrentIndex

Each packet is framed exactly like a BCI2000 "ADD WATCH" packet — a leading
frame counter + tab, and a trailing tab + CRLF — so it exercises the dispatcher's
real parsing path. Run bci2000_dispatcher.py to fan this out to the controllers.

Key geometry (matches Piano_Application_vel.py):
    11 keys, index 0..10. Keys 2..8 are the 7 notes (C D E F G A B);
    keys 0,1,9,10 are non-note edge keys. The hand's middle finger spans key
    windows 1..9 (ArmCurrentIndex). ArmPred_X = currentRoboX_px + 32767, with
    105 px per key and the center key (5) at 0, so ArmPred_X is in [32347, 33187].
    CopilotFingerPred 0/1/2 = left/center/right finger; the pressed key is
    ArmCurrentIndex + CopilotFingerPred - 1.

Usage:
    python bci_arm_hand_simulator.py
"""

import socket
import time
import threading
import random

# -----------------------------------------------------------------------
# Configuration / geometry
# -----------------------------------------------------------------------
UDP_IP        = "127.0.0.1"
STREAM_PORT   = 5005
RATE_HZ       = 8

SIGNED_OFFSET = 32767
PX_PER_KEY    = 105
CENTER_KEY    = 5            # key index at ArmPred_X == offset (px 0)
MIN_ARM_INDEX = 1           # middle finger can cover key windows 1..9
MAX_ARM_INDEX = 9
MIN_NOTE_KEY  = 2           # note keys are 2..8
MAX_NOTE_KEY  = 8

# Trial timing (seconds), loosely matching the paradigm (MoveTime/PressTime = 2 s)
MOVE_TIME     = 2.0
HOLD_TIME     = 0.5
PRESS_PULSE   = 0.125       # FingerMovePhase held true ~1 packet (rising edge)
INTERTRIAL    = 1.0

# -----------------------------------------------------------------------
# Shared stream state
# -----------------------------------------------------------------------
state = {
    "CurrentTrial":       1,
    "InnerTrialCount":    0,
    "ArmPred_X":          SIGNED_OFFSET,   # start over center key
    "FingerMovePhase":    0,
    "CopilotFingerPred":  1,
    "targetKeyIndex":     CENTER_KEY,
    "pressedKeyIndex":    CENTER_KEY,
    "ArmCurrentIndex":    CENTER_KEY,
    "running":            True,
}
_lock = threading.Lock()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------
def key_to_arm_pred(key_index):
    """Key index -> ArmPred_X (middle finger centered over that key)."""
    px = (key_index - CENTER_KEY) * PX_PER_KEY
    return SIGNED_OFFSET + px

def arm_pred_to_index(arm_pred_x):
    """ArmPred_X -> nearest arm window index (which key the middle finger is on)."""
    px = arm_pred_x - SIGNED_OFFSET
    idx = round(px / PX_PER_KEY) + CENTER_KEY
    return int(max(MIN_ARM_INDEX, min(MAX_ARM_INDEX, idx)))

def set_arm_pred(arm_pred_x):
    lo = key_to_arm_pred(MIN_ARM_INDEX)
    hi = key_to_arm_pred(MAX_ARM_INDEX)
    arm_pred_x = int(max(lo, min(hi, arm_pred_x)))
    with _lock:
        state["ArmPred_X"] = arm_pred_x
        state["ArmCurrentIndex"] = arm_pred_to_index(arm_pred_x)


# -----------------------------------------------------------------------
# Send loop — BCI2000 watch-packet framing
# -----------------------------------------------------------------------
def send_loop():
    interval = 1.0 / RATE_HZ
    counter = 0
    while state["running"]:
        with _lock:
            fields = [
                state["CurrentTrial"], state["InnerTrialCount"], state["ArmPred_X"],
                state["FingerMovePhase"], state["CopilotFingerPred"],
                state["targetKeyIndex"], state["pressedKeyIndex"], state["ArmCurrentIndex"],
            ]
        # leading counter + tab, then the 8 fields, then trailing tab + CRLF
        body = "\t".join(str(v) for v in fields)
        packet = "{}\t{}\t\r\n".format(counter, body)
        sock.sendto(packet.encode(), (UDP_IP, STREAM_PORT))
        counter += 1
        time.sleep(interval)


# -----------------------------------------------------------------------
# Arm motion
# -----------------------------------------------------------------------
def ramp_arm_to_key(key_index, move_time=MOVE_TIME):
    """Smoothly slide the arm so the middle finger reaches key_index."""
    key_index = int(max(MIN_ARM_INDEX, min(MAX_ARM_INDEX, key_index)))
    with _lock:
        start_px = state["ArmPred_X"] - SIGNED_OFFSET
    end_px = (key_index - CENTER_KEY) * PX_PER_KEY
    steps = max(1, int(move_time * RATE_HZ))
    for i in range(1, steps + 1):
        px = start_px + (end_px - start_px) * i / steps
        set_arm_pred(SIGNED_OFFSET + px)
        time.sleep(1.0 / RATE_HZ)


def press_finger(finger, hold=PRESS_PULSE):
    """Fire one finger press: set CopilotFingerPred, pulse FingerMovePhase true."""
    finger = int(max(0, min(2, finger)))
    with _lock:
        arm_idx = state["ArmCurrentIndex"]
        pressed = int(max(0, min(10, arm_idx + finger - 1)))
        state["CopilotFingerPred"] = finger
        state["pressedKeyIndex"] = pressed
        state["FingerMovePhase"] = 1
    time.sleep(hold)
    with _lock:
        state["FingerMovePhase"] = 0
    print("  [press] finger={} (arm key {}) -> pressed key {}".format(finger, arm_idx, pressed))


# -----------------------------------------------------------------------
# Trials
# -----------------------------------------------------------------------
def run_trial(arm_key, finger):
    """One trial: slide arm to arm_key, hold, then press finger."""
    def _run():
        with _lock:
            state["InnerTrialCount"] += 1
            target = int(max(MIN_NOTE_KEY, min(MAX_NOTE_KEY, arm_key + finger - 1)))
            state["targetKeyIndex"] = target
        print("\n[Trial {}] arm -> key {}, finger {} (target note key {})".format(
            state["InnerTrialCount"], arm_key, finger, target))
        ramp_arm_to_key(arm_key)
        time.sleep(HOLD_TIME)
        press_finger(finger)
        time.sleep(INTERTRIAL)
        print("[Trial] complete.")
    threading.Thread(target=_run, daemon=True).start()


def run_demo(n):
    def _run():
        print("\n[Demo] {} random trials...".format(n))
        for i in range(n):
            arm_key = random.randint(MIN_NOTE_KEY, MAX_NOTE_KEY)
            finger  = random.randint(0, 2)
            run_trial(arm_key, finger)
            time.sleep(MOVE_TIME + HOLD_TIME + PRESS_PULSE + INTERTRIAL + 0.3)
        print("\n[Demo] complete.")
    threading.Thread(target=_run, daemon=True).start()


# -----------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------
def print_help():
    print("""
Commands:
  key <index>        Slide arm so middle finger is over key index (1-9)
  armx <px>          Set raw arm position directly in px (-420..420, 0 = center)
  press <0|1|2>      Fire a finger press (0=left, 1=center, 2=right finger)
  trial <key> <fgr>  Full trial: arm to key (1-9), then press finger (0-2)
  demo [n]           Run n random trials (default 4)
  home               Recenter arm over the center key, lift finger
  status             Show current stream state
  help / quit
""")


def main():
    print("=" * 60)
    print("BCI2000 Piano Simulator")
    print("Stream -> UDP {}:{} @ {} Hz (single combined piano stream)".format(
        UDP_IP, STREAM_PORT, RATE_HZ))
    print("Start bci2000_dispatcher.py to fan this out to the controllers.")
    print("=" * 60)
    print_help()

    threading.Thread(target=send_loop, daemon=True).start()

    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
        if not cmd:
            continue
        parts = cmd.split()

        if parts[0] == "quit":
            break
        elif parts[0] == "help":
            print_help()
        elif parts[0] == "status":
            with _lock:
                print("  ArmPred_X={} (px {}, key {})  FingerMovePhase={}  "
                      "CopilotFingerPred={}  targetKey={}  pressedKey={}".format(
                          state["ArmPred_X"], state["ArmPred_X"] - SIGNED_OFFSET,
                          state["ArmCurrentIndex"], state["FingerMovePhase"],
                          state["CopilotFingerPred"], state["targetKeyIndex"],
                          state["pressedKeyIndex"]))
        elif parts[0] == "home":
            set_arm_pred(SIGNED_OFFSET)
            with _lock:
                state["FingerMovePhase"] = 0
                state["CopilotFingerPred"] = 1
            print("Arm recentered over key {}.".format(CENTER_KEY))
        elif parts[0] == "key" and len(parts) == 2:
            try:
                threading.Thread(target=ramp_arm_to_key, args=(int(parts[1]),), daemon=True).start()
            except ValueError:
                print("Usage: key <index 1-9>")
        elif parts[0] == "armx" and len(parts) == 2:
            try:
                set_arm_pred(SIGNED_OFFSET + int(parts[1]))
            except ValueError:
                print("Usage: armx <px -420..420>")
        elif parts[0] == "press" and len(parts) == 2:
            try:
                threading.Thread(target=press_finger, args=(int(parts[1]),), daemon=True).start()
            except ValueError:
                print("Usage: press <0|1|2>")
        elif parts[0] == "trial" and len(parts) == 3:
            try:
                run_trial(int(parts[1]), int(parts[2]))
            except ValueError:
                print("Usage: trial <key 1-9> <finger 0-2>")
        elif parts[0] == "demo":
            try:
                run_demo(int(parts[1]) if len(parts) > 1 else 4)
            except ValueError:
                print("Usage: demo [n]")
        else:
            print("Unknown command '{}'. Type 'help'.".format(cmd))

    state["running"] = False
    sock.close()
    print("Simulator stopped.")


if __name__ == "__main__":
    main()
