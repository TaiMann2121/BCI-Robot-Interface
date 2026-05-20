"""
BCI2000 Arm Simulator
---------------------
Simulates BCI2000 UDP output for testing the arm control script
(arm_controller.py) without needing a real BCI2000 session.

Sends packets to UDP port 5006 on localhost in the format:
    trial\tArm_X\tArm_Y\tArmMove

Where:
    - trial:   incrementing trial counter (starts at 0)
    - Arm_X:   uint16 encoded x position (32767 = center/home)
    - Arm_Y:   uint16 encoded y position (32767 = center/home)
    - ArmMove: 1 = arm movement enabled, 0 = disabled

BCI space units: values are scaled by 1050 before encoding.
For example, an offset of 0.1m in arm space = 0.1/0.48*1050 = 219 units in BCI space.
"""

import socket
import time
import threading

# ---- Configuration ----
UDP_IP = "127.0.0.1"
UDP_PORT = 5006
SEND_RATE_HZ = 25  # How many packets to send per second (matches ~40ms loop in arm script)

# ---- Socket setup ----
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ---- Shared state ----
state = {
    "arm_x": 0.0,       # BCI space x offset from center (float)
    "arm_y": 0.0,       # BCI space y offset from center (float)
    "arm_move": 1,      # ArmMove flag (1 = enabled)
    "trial": 0,
    "running": True
}

def encode_bci(value):
    """Convert a BCI space float value to uint16 with 32767 center offset."""
    encoded = int(value * 1050) + 32767
    # Clamp to valid uint16 range
    encoded = max(0, min(65535, encoded))
    return encoded

def send_loop():
    """Continuously sends UDP packets at SEND_RATE_HZ."""
    interval = 1.0 / SEND_RATE_HZ
    while state["running"]:
        arm_x_enc = encode_bci(state["arm_x"])
        arm_y_enc = encode_bci(state["arm_y"])
        arm_move  = state["arm_move"]
        trial     = state["trial"]

        # Format matches what 01-move_angular_and_cartesian.py expects:
        # tokenList[0]=trial, [1]=Arm_X, [2]=Arm_Y, [3]=ArmMove
        msg = f"{trial}\t{arm_x_enc}\t{arm_y_enc}\t{arm_move}"
        sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))

        state["trial"] += 1
        
        time.sleep(interval)
        arm_move = 0

def print_help():
    print("""
Commands:
  move <x> <y>   Set target position offset from home in meters
                 e.g. 'move 0.1 0.05' moves arm 10cm in x, 5cm in y
  home           Return arm to home position (0, 0)
  stop           Disable arm movement (ArmMove = 0)
  start          Enable arm movement (ArmMove = 1)
  status         Show current state
  help           Show this message
  quit           Exit the simulator
""")

def main():
    print("=" * 50)
    print("BCI2000 Arm Simulator")
    print(f"Sending UDP packets to {UDP_IP}:{UDP_PORT} at {SEND_RATE_HZ}Hz")
    print("Make sure 01-move_angular_and_cartesian.py is running first.")
    print("=" * 50)
    print_help()

    # Start sending in background thread
    sender = threading.Thread(target=send_loop, daemon=True)
    sender.start()

    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting simulator...")
            state["running"] = False
            break

        if not cmd:
            continue

        parts = cmd.split()

        if parts[0] == "quit":
            print("Exiting simulator...")
            state["running"] = False
            break

        elif parts[0] == "move" and len(parts) == 3:
            try:
                x = float(parts[1])
                y = float(parts[2])
                state["arm_x"] = x
                state["arm_y"] = y
                state["arm_move"] = 1
                print(f"Moving to offset ({x}, {y}) from home. ArmMove = 1.")
            except ValueError:
                print("Invalid values. Usage: move <x> <y>  (e.g. move 0.1 0.05)")

        elif parts[0] == "home":
            state["arm_x"] = 0.0
            state["arm_y"] = 0.0
            state["arm_move"] = 1
            print("Returning to home position.")

        elif parts[0] == "stop":
            state["arm_move"] = 0
            print("Arm movement disabled (ArmMove = 0).")

        elif parts[0] == "start":
            state["arm_move"] = 1
            print("Arm movement enabled (ArmMove = 1).")

        elif parts[0] == "status":
            print(f"  arm_x:    {state['arm_x']} m offset")
            print(f"  arm_y:    {state['arm_y']} m offset")
            print(f"  arm_move: {state['arm_move']}")
            print(f"  trial:    {state['trial']}")
            print(f"  encoded x: {encode_bci(state['arm_x'])}")
            print(f"  encoded y: {encode_bci(state['arm_y'])}")

        elif parts[0] == "help":
            print_help()

        else:
            print(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

    sock.close()

if __name__ == "__main__":
    main()
