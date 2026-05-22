"""
BCI2000 Arm+Hand Simulator
--------------------------
Simulates BCI2000 UDP output for testing the arm controller (arm_controller.py)
and hand controller (myAllegroHand.exe) without needing a real BCI2000 session.

Arm packets  → UDP port 5006 @ 25Hz,  format: trial\tArm_X\tArm_Y\tArmMove
Hand packets → UDP port 5005 @ 8Hz,   format: trial\tFeedbackApp\tprob_thumb\tprob_index\tprob_middle\tprob_pinky

Frequencies confirmed from BCI2000 parameter files:
  Arm:  SamplingRate=1000Hz, SampleBlockSize=40  -> 25Hz update rate
  Hand: SamplingRate=1024Hz, SampleBlockSize=128 -> 8Hz update rate

Trial structure (from finger .prm file):
  PreFeedback = 1s  (FeedbackApp=0, arm moving toward target)
  Feedback    = 2s  (FeedbackApp=1, finger probability ramping up)
  InterTrial  = 2s  (FeedbackApp=0, arm returns home, hand resets)

Usage:
    Run arm_controller.py and myAllegroHand.exe first, then run this script.
"""

import socket
import time
import threading
import math
import random

# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
UDP_IP       = "127.0.0.1"
ARM_PORT     = 5006
HAND_PORT    = 5005
ARM_RATE_HZ  = 25   # confirmed from arm .prm: 1000Hz / 40 samples = 25Hz
HAND_RATE_HZ = 8     # confirmed from finger .prm: 1024Hz / 128 samples = 8Hz

# Trial timing (seconds) from finger .prm file
PRE_FEEDBACK_DURATION = 1.0
FEEDBACK_DURATION     = 2.0
INTERTRIAL_DURATION   = 2.0

# Arm step timing: 1 packet interval = most accurate BCI2000 replication
ARM_STEP_DURATION = 1.0 / ARM_RATE_HZ   # 0.04s per waypoint

# Preset arm targets for demo trials (x, y offsets from home in meters)
DEMO_ARM_TARGETS = [
    ( 0.05,  0.05),
    (-0.05,  0.05),
    ( 0.05, -0.05),
    (-0.05, -0.05),
]

# -----------------------------------------------------------------------
# Shared state
# -----------------------------------------------------------------------
state = {
    "arm_x":       0.0,
    "arm_y":       0.0,
    "arm_move":    1,
    "arm_trial":   0,
    "prob_thumb":  0,
    "prob_index":  0,
    "prob_middle": 0,
    "prob_pinky":  0,
    "hand_move":   0,
    "hand_trial":  0,
    "arm_running":  True,
    "hand_running": True,
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
FINGER_NAMES = ["thumb", "index", "middle", "pinky"]

# -----------------------------------------------------------------------
# Encoding
# -----------------------------------------------------------------------
def encode_arm_pos(value):
    encoded = int(value * 1050) + 32767
    return max(0, min(65535, encoded))

# -----------------------------------------------------------------------
# Send loops
# -----------------------------------------------------------------------
def send_loop_arm():
    interval = 1.0 / ARM_RATE_HZ
    while state["arm_running"]:
        msg = "{}\t{}\t{}\t{}".format(
            state["arm_trial"],
            encode_arm_pos(state["arm_x"]),
            encode_arm_pos(state["arm_y"]),
            state["arm_move"]
        )
        sock.sendto(msg.encode(), (UDP_IP, ARM_PORT))
        state["arm_trial"] += 1
        time.sleep(interval)

def send_loop_hand():
    interval = 1.0 / HAND_RATE_HZ
    while state["hand_running"]:
        msg = "{}\t{}\t{}\t{}\t{}\t{}".format(
            state["hand_trial"],
            state["hand_move"],
            state["prob_thumb"],
            state["prob_index"],
            state["prob_middle"],
            state["prob_pinky"]
        )
        sock.sendto(msg.encode(), (UDP_IP, HAND_PORT))
        state["hand_trial"] += 1
        time.sleep(interval)

# -----------------------------------------------------------------------
# Arm helpers
# -----------------------------------------------------------------------
def run_arm_sequence(waypoints, step_duration=ARM_STEP_DURATION):
    def _run():
        state["arm_move"] = 1
        for x, y in waypoints:
            state["arm_x"] = x
            state["arm_y"] = y
            time.sleep(step_duration)
    threading.Thread(target=_run, daemon=True).start()

def make_square(size, steps_per_side=10, step_duration=ARM_STEP_DURATION):
    s = size
    wpts = []
    for i in range(steps_per_side):
        wpts.append((s * i / steps_per_side, 0))
    for i in range(steps_per_side):
        wpts.append((s, s * i / steps_per_side))
    for i in range(steps_per_side):
        wpts.append((s - s * i / steps_per_side, s))
    for i in range(steps_per_side):
        wpts.append((0, s - s * i / steps_per_side))
    wpts.append((0, 0))
    run_arm_sequence(wpts, step_duration)

def make_circle(radius, num_steps=36, step_duration=ARM_STEP_DURATION):
    wpts = []
    for i in range(num_steps + 1):
        a = 2 * math.pi * i / num_steps
        wpts.append((radius * math.cos(a), radius * math.sin(a)))
    run_arm_sequence(wpts, step_duration)

# -----------------------------------------------------------------------
# Finger helpers
# -----------------------------------------------------------------------
def set_finger(finger_name):
    for f in FINGER_NAMES:
        state["prob_" + f] = 0
    if finger_name in FINGER_NAMES:
        state["prob_" + finger_name] = 100
        return True
    return False

def set_finger_probs(thumb, index, middle, pinky):
    state["prob_thumb"]  = max(0, min(100, thumb))
    state["prob_index"]  = max(0, min(100, index))
    state["prob_middle"] = max(0, min(100, middle))
    state["prob_pinky"]  = max(0, min(100, pinky))

# -----------------------------------------------------------------------
# Hand trial patterns
# -----------------------------------------------------------------------
def run_hand_trial(finger_name):
    """
    Single realistic BCI2000 finger trial:
      Pre-feedback (1s):  FeedbackApp=0, equal probs (25 each)
      Feedback (2s):      FeedbackApp=1, target finger ramps 25->90 over 16 packets at 8Hz
      Inter-trial (2s):   FeedbackApp=0, all probs reset to 0
    Total: 5 seconds. Runs in background thread.
    """
    if finger_name not in FINGER_NAMES:
        print("Unknown finger '{}'.".format(finger_name))
        return

    def _run():
        hand_interval  = 1.0 / HAND_RATE_HZ
        feedback_steps = int(FEEDBACK_DURATION * HAND_RATE_HZ)  # 16 steps

        print("  [Hand] Pre-feedback ({}s)...".format(PRE_FEEDBACK_DURATION))
        state["hand_move"] = 0
        set_finger_probs(25, 25, 25, 25)
        time.sleep(PRE_FEEDBACK_DURATION)

        print("  [Hand] Feedback ({}s) -- ramping {}...".format(FEEDBACK_DURATION, finger_name))
        state["hand_move"] = 1
        for step in range(feedback_steps):
            t           = step / max(feedback_steps - 1, 1)
            target_prob = int(25 + t * 65)
            other_prob  = int((100 - target_prob) / 3)
            probs = {f: other_prob for f in FINGER_NAMES}
            probs[finger_name] = target_prob
            set_finger_probs(probs["thumb"], probs["index"],
                             probs["middle"], probs["pinky"])
            time.sleep(hand_interval)

        print("  [Hand] Inter-trial ({}s)...".format(INTERTRIAL_DURATION))
        state["hand_move"] = 0
        set_finger_probs(0, 0, 0, 0)
        time.sleep(INTERTRIAL_DURATION)
        print("  [Hand] Trial complete.")

    threading.Thread(target=_run, daemon=True).start()

def run_hand_sequence(finger_list):
    total_per_trial = PRE_FEEDBACK_DURATION + FEEDBACK_DURATION + INTERTRIAL_DURATION

    def _run():
        print("[Hand sequence] {} trials: {}".format(
            len(finger_list), " -> ".join(finger_list)))
        for i, finger in enumerate(finger_list):
            print("\n[Hand sequence] Trial {}/{}: {}".format(i+1, len(finger_list), finger))
            run_hand_trial(finger)
            time.sleep(total_per_trial + 0.2)
        print("[Hand sequence] Complete.")

    threading.Thread(target=_run, daemon=True).start()

# -----------------------------------------------------------------------
# Combined demo sequences
# -----------------------------------------------------------------------
def run_demo_trial(arm_x, arm_y, finger_name):
    """
    Full combined BCI2000 trial:
      - Arm moves toward target during pre-feedback + feedback, returns during inter-trial
      - Hand runs a full trial simultaneously
    Both start at the same time. Total ~5 seconds.
    """
    print("\n[Demo trial] Arm -> ({}, {})m  |  Hand -> {}".format(arm_x, arm_y, finger_name))

    def _run():
        phase1_steps = int((PRE_FEEDBACK_DURATION + FEEDBACK_DURATION) * ARM_RATE_HZ)
        phase1 = [(arm_x * (i+1) / phase1_steps,
                   arm_y * (i+1) / phase1_steps) for i in range(phase1_steps)]

        phase2_steps = int(INTERTRIAL_DURATION * ARM_RATE_HZ)
        phase2 = [(arm_x * (1 - (i+1) / phase2_steps),
                   arm_y * (1 - (i+1) / phase2_steps)) for i in range(phase2_steps)]

        run_arm_sequence(phase1 + phase2, ARM_STEP_DURATION)
        run_hand_trial(finger_name)

        total = PRE_FEEDBACK_DURATION + FEEDBACK_DURATION + INTERTRIAL_DURATION
        time.sleep(total + 0.5)
        print("[Demo trial] Complete.")

    threading.Thread(target=_run, daemon=True).start()

def run_demo_sequence():
    trials          = list(zip(DEMO_ARM_TARGETS, FINGER_NAMES))
    total_per_trial = PRE_FEEDBACK_DURATION + FEEDBACK_DURATION + INTERTRIAL_DURATION + 0.5

    def _run():
        print("\n[Demo sequence] Starting {}-trial block...".format(len(trials)))
        for i, ((ax, ay), finger) in enumerate(trials):
            print("\n[Demo sequence] Trial {}/{}".format(i+1, len(trials)))
            run_demo_trial(ax, ay, finger)
            time.sleep(total_per_trial)
        print("\n[Demo sequence] Block complete.")

    threading.Thread(target=_run, daemon=True).start()

def run_demo_random(n):
    total_per_trial = PRE_FEEDBACK_DURATION + FEEDBACK_DURATION + INTERTRIAL_DURATION + 0.5

    def _run():
        print("\n[Demo random] Starting {} randomized trials...".format(n))
        for i in range(n):
            ax     = round(random.uniform(-0.06, 0.06), 3)
            ay     = round(random.uniform(-0.06, 0.06), 3)
            finger = random.choice(FINGER_NAMES)
            print("\n[Demo random] Trial {}/{}".format(i+1, n))
            run_demo_trial(ax, ay, finger)
            time.sleep(total_per_trial)
        print("\n[Demo random] Complete.")

    threading.Thread(target=_run, daemon=True).start()

# -----------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------
def print_help():
    print("""
Commands:
  Combined arm + hand:
    move <x> <y> <finger>                            Move arm and curl one finger
    move <x> <y> <p_thumb> <p_idx> <p_mid> <p_pnk>  Move arm and set finger probabilities
    home                                             Return arm and hand to home
    start / stop                                     Enable / disable both

  Arm only:
    arm move <x> <y>
    arm home / arm start / arm stop
    arm square <size> [steps] [dwell]    e.g. arm square 0.1 25 0.04
    arm circle <radius> [steps] [dwell]  e.g. arm circle 0.08 100 0.04

  Hand only:
    hand move <finger>
    hand move <p_thumb> <p_idx> <p_mid> <p_pnk>
    hand home / hand start / hand stop
    hand trial <finger|random>           Full 5s BCI2000 trial (pre-feedback, ramp, inter-trial)
    hand sequence <f1> <f2> ...          Series of trials  e.g. hand sequence index middle thumb

  Combined demo:
    demo trial <x> <y> <finger>          One full trial with arm + hand  e.g. demo trial 0.05 0.05 index
    demo sequence                        Preset 4-trial block (one per finger, varied arm targets)
    demo random <n>                      n randomized trials  e.g. demo random 8

  General:
    status / help / quit
""")

# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
def main():
    print("=" * 55)
    print("BCI2000 Arm+Hand Simulator")
    print("Arm  -> UDP {}:{}  @ {}Hz".format(UDP_IP, ARM_PORT, ARM_RATE_HZ))
    print("Hand -> UDP {}:{} @ {}Hz".format(UDP_IP, HAND_PORT, HAND_RATE_HZ))
    print("Make sure arm_controller.py and myAllegroHand.exe are running first.")
    print("=" * 55)
    print_help()

    threading.Thread(target=send_loop_arm,  daemon=True).start()
    threading.Thread(target=send_loop_hand, daemon=True).start()

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
            print("  Arm:  x={}m  y={}m  move={}  trial={}".format(
                state["arm_x"], state["arm_y"], state["arm_move"], state["arm_trial"]))
            print("  Hand: thumb={}  index={}  middle={}  pinky={}  move={}  trial={}".format(
                state["prob_thumb"], state["prob_index"], state["prob_middle"],
                state["prob_pinky"], state["hand_move"], state["hand_trial"]))
        elif parts[0] == "home":
            state["arm_x"] = state["arm_y"] = 0.0
            state["arm_move"] = 1
            set_finger_probs(0, 0, 0, 0)
            state["hand_move"] = 0
            print("Returning arm and hand to home.")
        elif parts[0] == "stop":
            state["arm_move"] = 0
            state["hand_move"] = 0
            print("Arm and hand movement disabled.")
        elif parts[0] == "start":
            state["arm_move"] = 1
            state["hand_move"] = 1
            print("Arm and hand movement enabled.")
        elif parts[0] == "move" and len(parts) == 4:
            try:
                x, y = float(parts[1]), float(parts[2])
                finger = parts[3]
                if finger not in FINGER_NAMES:
                    print("Unknown finger '{}'. Use: thumb, index, middle, pinky.".format(finger))
                    continue
                state["arm_x"] = x
                state["arm_y"] = y
                state["arm_move"] = 1
                set_finger(finger)
                state["hand_move"] = 1
                print("Arm -> ({}, {})m  |  Hand -> {}".format(x, y, finger))
            except ValueError:
                print("Usage: move <x> <y> <finger>")
        elif parts[0] == "move" and len(parts) == 7:
            try:
                x, y = float(parts[1]), float(parts[2])
                pt, pi, pm, pp = int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6])
                state["arm_x"] = x
                state["arm_y"] = y
                state["arm_move"] = 1
                set_finger_probs(pt, pi, pm, pp)
                state["hand_move"] = 1
                print("Arm -> ({}, {})m  |  probs: thumb={} index={} middle={} pinky={}".format(
                    x, y, pt, pi, pm, pp))
            except ValueError:
                print("Usage: move <x> <y> <p_thumb> <p_idx> <p_mid> <p_pnk>")
        elif parts[0] == "arm":
            if len(parts) < 2:
                print("Usage: arm <move|home|start|stop|square|circle>")
            elif parts[1] == "home":
                state["arm_x"] = state["arm_y"] = 0.0
                state["arm_move"] = 1
                print("Arm returning to home.")
            elif parts[1] == "stop":
                state["arm_move"] = 0
                print("Arm movement disabled.")
            elif parts[1] == "start":
                state["arm_move"] = 1
                print("Arm movement enabled.")
            elif parts[1] == "move" and len(parts) == 4:
                try:
                    x, y = float(parts[2]), float(parts[3])
                    state["arm_x"] = x
                    state["arm_y"] = y
                    state["arm_move"] = 1
                    print("Arm -> ({}, {})m".format(x, y))
                except ValueError:
                    print("Usage: arm move <x> <y>")
            elif parts[1] == "square":
                try:
                    size  = float(parts[2]) if len(parts) > 2 else 0.1
                    steps = int(parts[3])   if len(parts) > 3 else 10
                    dwell = float(parts[4]) if len(parts) > 4 else ARM_STEP_DURATION
                    print("Running square: size={}m  steps/side={}  dwell={}s".format(size, steps, dwell))
                    make_square(size, steps, dwell)
                except ValueError:
                    print("Usage: arm square <size> [steps] [dwell]")
            elif parts[1] == "circle":
                try:
                    radius = float(parts[2]) if len(parts) > 2 else 0.08
                    steps  = int(parts[3])   if len(parts) > 3 else 36
                    dwell  = float(parts[4]) if len(parts) > 4 else ARM_STEP_DURATION
                    print("Running circle: radius={}m  steps={}  dwell={}s".format(radius, steps, dwell))
                    make_circle(radius, steps, dwell)
                except ValueError:
                    print("Usage: arm circle <radius> [steps] [dwell]")
            else:
                print("Unknown arm command. Type 'help' for usage.")
        elif parts[0] == "hand":
            if len(parts) < 2:
                print("Usage: hand <move|home|start|stop|trial|sequence>")
            elif parts[1] == "home":
                set_finger_probs(0, 0, 0, 0)
                state["hand_move"] = 0
                print("Hand returning to home.")
            elif parts[1] == "stop":
                state["hand_move"] = 0
                print("Hand movement disabled.")
            elif parts[1] == "start":
                state["hand_move"] = 1
                print("Hand movement enabled.")
            elif parts[1] == "move" and len(parts) == 3:
                finger = parts[2]
                if finger not in FINGER_NAMES:
                    print("Unknown finger '{}'. Use: thumb, index, middle, pinky.".format(finger))
                else:
                    set_finger(finger)
                    state["hand_move"] = 1
                    print("Hand -> moving {}".format(finger))
            elif parts[1] == "move" and len(parts) == 6:
                try:
                    pt, pi, pm, pp = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
                    set_finger_probs(pt, pi, pm, pp)
                    state["hand_move"] = 1
                    print("Hand probs: thumb={} index={} middle={} pinky={}".format(pt, pi, pm, pp))
                except ValueError:
                    print("Usage: hand move <p_thumb> <p_idx> <p_mid> <p_pnk>")
            elif parts[1] == "trial":
                if len(parts) < 3:
                    print("Usage: hand trial <finger|random>")
                else:
                    finger = random.choice(FINGER_NAMES) if parts[2] == "random" else parts[2]
                    if finger not in FINGER_NAMES:
                        print("Unknown finger '{}'. Use: thumb, index, middle, pinky, or random.".format(finger))
                    else:
                        print("Running hand trial: {}".format(finger))
                        run_hand_trial(finger)
            elif parts[1] == "sequence":
                if len(parts) < 3:
                    print("Usage: hand sequence <finger1> <finger2> ...")
                else:
                    fingers = parts[2:]
                    invalid = [f for f in fingers if f not in FINGER_NAMES]
                    if invalid:
                        print("Unknown finger(s): {}. Use: thumb, index, middle, pinky.".format(invalid))
                    else:
                        print("Running hand sequence: {}".format(" -> ".join(fingers)))
                        run_hand_sequence(fingers)
            else:
                print("Unknown hand command. Type 'help' for usage.")
        elif parts[0] == "demo":
            if len(parts) < 2:
                print("Usage: demo <trial|sequence|random>")
            elif parts[1] == "trial" and len(parts) == 5:
                try:
                    ax     = float(parts[2])
                    ay     = float(parts[3])
                    finger = parts[4]
                    if finger not in FINGER_NAMES:
                        print("Unknown finger '{}'. Use: thumb, index, middle, pinky.".format(finger))
                    else:
                        run_demo_trial(ax, ay, finger)
                except ValueError:
                    print("Usage: demo trial <x> <y> <finger>")
            elif parts[1] == "sequence":
                print("Running preset 4-trial demo block...")
                run_demo_sequence()
            elif parts[1] == "random":
                try:
                    n = int(parts[2]) if len(parts) > 2 else 4
                    run_demo_random(n)
                except ValueError:
                    print("Usage: demo random <n>")
            else:
                print("Unknown demo command. Type 'help' for usage.")
        else:
            print("Unknown command '{}'. Type 'help' for available commands.".format(cmd))

    state["arm_running"]  = False
    state["hand_running"] = False
    sock.close()
    print("Simulator stopped.")

if __name__ == "__main__":
    main()
