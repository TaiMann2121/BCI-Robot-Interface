#! /usr/bin/env python3
"""
Arm Controller (Piano task)
---------------------------
Controls the Kinova Gen3 robotic arm for the BCI2000 piano typing task.

The piano keyboard is a 1-D layout: the arm only slides horizontally along the
row of keys to position the hand over the target key. Vertical key presses are
performed by the fingers (myAllegroHand.exe), not the arm — so unlike the older
2-D controller, this one moves along a single axis.

Data path:
    BCI2000 --5005--> bci2000_dispatcher.py --5006--> this controller

The dispatcher forwards the 8-field piano record (tab-separated, no leading
counter):
    CurrentTrial  InnerTrialCount  ArmPred_X  FingerMovePhase
    CopilotFingerPred  targetKeyIndex  pressedKeyIndex  ArmCurrentIndex

Only ArmPred_X is used here.

ArmPred_X calibration (confirmed against Piano_Application_vel.py):
    ArmPred_X = currentRoboX_px + 32767
    currentRoboX_px is the on-screen hand position in [-420, +420] px, where
    key_step = KeyWidth(95) + KeySpacing(10) = 105 px equals one key.
    Center key (index 5) is at 0; the arm's middle finger spans keys 1..9.
    Physical keys are 2 in = 0.0508 m wide, so 105 px -> 0.0508 m.

Usage:
    python arm_controller.py --ip 192.168.1.10
"""

import sys, os, socket, threading, time
import numpy as np

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.BaseCyclicClientRpc import BaseCyclicClient
from kortex_api.autogen.messages import Base_pb2

# -----------------------------------------------------------------------
# Home position of the end effector (meters / degrees)
# The home pose places the hand so the MIDDLE finger sits over the center key
# (key index 5, ArmPred_X == 32767). Jog the arm here in the Kinova web app and
# record the values if the physical setup changes.
# -----------------------------------------------------------------------
HOME_X       =  0.427   # meters
HOME_Y       = -0.447   # meters  (horizontal axis, ALONG the key row)
HOME_Z       =  0.156   # meters
HOME_THETA_X =  88.149  # degrees
HOME_THETA_Y =  -2.257  # degrees
HOME_THETA_Z =   5.636  # degrees

# -----------------------------------------------------------------------
# Piano / BCI coordinate decoding
# -----------------------------------------------------------------------
SIGNED_OFFSET = 32767          # ArmPred_X offset applied by BCI2000
PX_PER_KEY    = 105            # on-screen px per key (KeyWidth 95 + KeySpacing 10)
KEY_WIDTH_M   = 0.0508         # physical key width: 2 inches
M_PER_PX      = KEY_WIDTH_M / PX_PER_KEY   # ~4.838e-4 m per ArmPred_X unit
ARM_PX_LIMIT  = 420            # |currentRoboX_px| max -> +/- 4 keys from center

# Which physical direction is +ArmPred_X (higher key index)?
#   +1: increasing key index moves the arm in +Y (world).
#   -1: flip if the arm slides the wrong way along the keyboard.
# >>> CONFIRM against your rig by watching a small `arm key 6` vs `arm key 4`. <<<
ARM_Y_SIGN    = +1

# -----------------------------------------------------------------------
# Control parameters
# -----------------------------------------------------------------------
CONTROL_HZ  = 40             # internal servo rate (decoupled from the 8 Hz stream)
LOOP_TIME   = 1.0 / CONTROL_HZ
MAX_SPEED   = 0.4            # m/s — safety speed cap
DEADZONE    = 0.005          # meters — stop when within this of target (~0.1 key)
TIMEOUT     = 20            # seconds — home-move timeout

# UDP socket settings (receive from the dispatcher, NOT directly from BCI2000)
UDP_IP   = "127.0.0.1"
UDP_PORT = 5006

# Field index of ArmPred_X in the forwarded record
F_ARM_PRED_X = 2
NUM_FIELDS   = 8

# Shared target updated by the receive thread, read by the control loop.
_target_lock = threading.Lock()
_target_horz_m = 0.0         # horizontal offset from home, meters
_running = True


# -----------------------------------------------------------------------
# Decoding
# -----------------------------------------------------------------------
def arm_pred_to_horz_m(arm_pred_x):
    """ArmPred_X (uint) -> horizontal offset from the center key, in meters."""
    px = int(arm_pred_x) - SIGNED_OFFSET
    px = int(np.clip(px, -ARM_PX_LIMIT, ARM_PX_LIMIT))
    return px * M_PER_PX


def receive_loop(sock):
    """Drains the dispatcher stream and keeps _target_horz_m up to date."""
    global _target_horz_m
    while _running:
        try:
            data, _ = sock.recvfrom(1024)
        except socket.timeout:
            continue
        except OSError:
            break
        fields = data.decode(errors="ignore").strip().split("\t")
        if len(fields) < NUM_FIELDS:
            continue
        try:
            horz = arm_pred_to_horz_m(fields[F_ARM_PRED_X])
        except ValueError:
            continue
        with _target_lock:
            _target_horz_m = horz


# -----------------------------------------------------------------------
# Movement
# -----------------------------------------------------------------------
def on_action_end(event):
    def callback(notification, e=event):
        if notification.action_event in (Base_pb2.ACTION_END, Base_pb2.ACTION_ABORT):
            e.set()
    return callback


def move_home(base):
    """Moves the arm to the home pose (hand over center key). Blocks."""
    print("Moving to home position ({}, {}, {})...".format(HOME_X, HOME_Y, HOME_Z))
    action = Base_pb2.Action()
    action.name = "Move to home"
    pose = action.reach_pose.target_pose
    pose.x, pose.y, pose.z = HOME_X, HOME_Y, HOME_Z
    pose.theta_x, pose.theta_y, pose.theta_z = HOME_THETA_X, HOME_THETA_Y, HOME_THETA_Z

    done = threading.Event()
    handle = base.OnNotificationActionTopic(on_action_end(done), Base_pb2.NotificationOptions())
    base.ExecuteAction(action)
    success = done.wait(TIMEOUT)
    base.Unsubscribe(handle)
    print("  Reached home position." if success else "  WARNING: move_home timed out/aborted.")
    return success


def servo_toward(base, base_cyclic, target_horz_m):
    """
    One 1-D velocity step: drive the horizontal axis toward the target offset.
    The keyboard runs along the arm's Y axis; Z (height) stays at home.
    """
    feedback = base_cyclic.RefreshFeedback()
    target_y = HOME_Y + ARM_Y_SIGN * target_horz_m
    error_y  = target_y - feedback.base.tool_pose_y

    vel = 0.0 if abs(error_y) < DEADZONE else error_y / LOOP_TIME
    vel = float(np.clip(vel, -MAX_SPEED, MAX_SPEED))

    command = Base_pb2.TwistCommand()
    command.reference_frame = Base_pb2.CARTESIAN_REFERENCE_FRAME_TOOL
    command.duration = 0
    command.twist.linear_x  = vel   # tool linear_x maps to world Y in this setup
    command.twist.linear_y  = 0
    command.twist.linear_z  = 0
    command.twist.angular_x = 0
    command.twist.angular_y = 0
    command.twist.angular_z = 0
    base.SendTwistCommand(command)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
def main():
    global _running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.5)
    print("Listening for dispatcher data on {}:{}...".format(UDP_IP, UDP_PORT))

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import utilities
    args = utilities.parseConnectionArguments()

    with utilities.DeviceConnection.createTcpConnection(args) as router:
        base        = BaseClient(router)
        base_cyclic = BaseCyclicClient(router)

        move_home(base)

        recv_thread = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
        recv_thread.start()

        print("Entering control loop at {} Hz. Tracking ArmPred_X...".format(CONTROL_HZ))
        try:
            while True:
                loop_start = time.time()
                with _target_lock:
                    target = _target_horz_m
                servo_toward(base, base_cyclic, target)
                dt = time.time() - loop_start
                if dt < LOOP_TIME:
                    time.sleep(LOOP_TIME - dt)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            _running = False
            base.Stop()
            sock.close()


if __name__ == "__main__":
    main()
