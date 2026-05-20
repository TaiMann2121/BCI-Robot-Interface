#! /usr/bin/env python3
"""
Arm Controller
--------------
Controls the Kinova Gen3 robotic arm based on BCI2000 inputs.

Receives UDP packets from BCI2000 (or the simulator) on port 5006.
Packet format (tab-separated):
    trial   Arm_X   Arm_Y   ArmMove

    - trial:   incrementing counter, unused here
    - Arm_X:   uint16 horizontal position (32767 = center)
    - Arm_Y:   uint16 vertical position   (32767 = center)
    - ArmMove: 1 = move arm, 0 = stop arm

Usage:
    python arm_controller.py --ip 192.168.1.10
"""

import sys, os, socket, re, threading
import numpy as np

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.BaseCyclicClientRpc import BaseCyclicClient
from kortex_api.autogen.messages import Base_pb2, BaseCyclic_pb2, Common_pb2

# -----------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------

# Home position of the end effector (meters / degrees)
# Update these if the physical setup changes by jogging the arm to the
# desired home position in the web app and recording the values shown.
HOME_X      =  0.657   # meters
HOME_Y      =  0.001   # meters
HOME_Z      =  0.417   # meters
HOME_THETA_X =  90     # degrees
HOME_THETA_Y =   0     # degrees
HOME_THETA_Z =  90     # degrees

# BCI coordinate decoding
# Arm_X and Arm_Y are sent as uint16 with 32767 as the center offset.
# Dividing by 1050 converts to BCI space units (roughly -31 to +31).
BCI_CENTER  = 32767
BCI_SCALE   = 1050

# Arm space scaling: converts BCI space units to meters of arm movement
ARM_SCALE   = 0.48     # meters per BCI unit

# Velocity control parameters
LOOP_TIME   = 0.04     # seconds — target loop time (40ms)
MAX_SPEED   = 0.4      # m/s — safety speed cap
DEADZONE    = 0.02     # meters — stop moving when within this distance of target

# Action timeout (seconds)
TIMEOUT     = 20

# UDP socket settings
UDP_IP      = "127.0.0.1"
UDP_PORT    = 5006


# -----------------------------------------------------------------------
# Helper: action completion callback
# -----------------------------------------------------------------------

def on_action_end(event):
    """Returns a callback that sets 'event' when an action ends or aborts."""
    def callback(notification, e=event):
        status = Base_pb2.ActionEvent.Name(notification.action_event)
        print(f"  Action status: {status}")
        if notification.action_event in (Base_pb2.ACTION_END, Base_pb2.ACTION_ABORT):
            e.set()
    return callback


# -----------------------------------------------------------------------
# Movement functions
# -----------------------------------------------------------------------

def move_home(base, base_cyclic):
    """
    Moves the arm to the home position using Cartesian trajectory control.
    Blocks until the motion completes or times out.
    Returns True if successful, False if aborted or timed out.
    """
    print(f"Moving to home position ({HOME_X}, {HOME_Y}, {HOME_Z})...")

    action = Base_pb2.Action()
    action.name = "Move to home"

    pose = action.reach_pose.target_pose
    pose.x       = HOME_X
    pose.y       = HOME_Y
    pose.z       = HOME_Z
    pose.theta_x = HOME_THETA_X
    pose.theta_y = HOME_THETA_Y
    pose.theta_z = HOME_THETA_Z

    done = threading.Event()
    handle = base.OnNotificationActionTopic(on_action_end(done), Base_pb2.NotificationOptions())
    base.ExecuteAction(action)
    success = done.wait(TIMEOUT)
    base.Unsubscribe(handle)

    if success:
        print("  Reached home position.")
    else:
        print("  WARNING: move_home timed out or was aborted.")
    return success


def move_velocity(base, base_cyclic, arm_horz, arm_vert):
    """
    Moves the arm toward a target position using velocity (twist) control.
    This produces smooth, continuous motion rather than discrete jumps.

    arm_horz: horizontal offset from home in meters (maps to arm Y axis)
    arm_vert: vertical offset from home in meters   (maps to arm Z axis)

    The target position is:
        target_y = HOME_Y - arm_horz   (Y axis is negated in this setup)
        target_z = HOME_Z + arm_vert
    """
    feedback = base_cyclic.RefreshFeedback()

    # Calculate how far the arm currently is from the target
    target_y = HOME_Y - arm_horz
    target_z = HOME_Z + arm_vert
    error_y  = target_y - feedback.base.tool_pose_y
    error_z  = target_z - feedback.base.tool_pose_z

    # Stop moving if already within the deadzone
    vel_y = 0.0 if abs(error_y) < DEADZONE else error_y / LOOP_TIME
    vel_z = 0.0 if abs(error_z) < DEADZONE else error_z / LOOP_TIME

    # Cap velocity for safety
    vel_y = float(np.clip(vel_y, -MAX_SPEED, MAX_SPEED))
    vel_z = float(np.clip(vel_z, -MAX_SPEED, MAX_SPEED))

    # Send twist command
    command = Base_pb2.TwistCommand()
    command.reference_frame = Base_pb2.CARTESIAN_REFERENCE_FRAME_TOOL
    command.duration = 0
    command.twist.linear_x  = vel_y   # note: linear_x maps to Y in this setup
    command.twist.linear_y  = vel_z
    command.twist.linear_z  = 0
    command.twist.angular_x = 0
    command.twist.angular_y = 0
    command.twist.angular_z = 0
    base.SendTwistCommand(command)


# -----------------------------------------------------------------------
# UDP socket helpers
# -----------------------------------------------------------------------

def read_latest_packet(sock):
    """
    Drains the UDP buffer and returns the most recent packet as a string.
    Blocks until at least one packet is received.
    Returns None if something goes wrong.
    """
    latest = None
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            latest = data  # keep reading until buffer is empty
        except BlockingIOError:
            if latest is not None:
                return latest.decode()
            # Buffer is empty and we haven't received anything yet — keep waiting


def decode_packet(packet):
    """
    Decodes a tab-separated BCI2000 packet into arm movement values.

    Packet format: trial\tArm_X\tArm_Y\tArmMove

    Returns (arm_horz, arm_vert, arm_move) where:
        arm_horz: horizontal offset from home in meters
        arm_vert: vertical offset from home in meters
        arm_move: True if arm should move, False if it should stop
    """
    tokens   = packet.strip().split('\t')
    bci_x    = (int(tokens[1]) - BCI_CENTER) / BCI_SCALE
    bci_y    = (int(tokens[2]) - BCI_CENTER) / BCI_SCALE
    arm_move = int(tokens[3]) == 1

    arm_horz = ARM_SCALE * bci_x
    arm_vert = ARM_SCALE * bci_y
    return arm_horz, arm_vert, arm_move


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)  # non-blocking so we can drain the buffer each loop
    print(f"Listening for BCI2000 data on {UDP_IP}:{UDP_PORT}...")

    # Connect to arm
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import utilities
    args = utilities.parseConnectionArguments()

    with utilities.DeviceConnection.createTcpConnection(args) as router:
        base        = BaseClient(router)
        base_cyclic = BaseCyclicClient(router)

        # Move to home before entering the main loop
        move_home(base, base_cyclic)

        print("Entering main loop. Waiting for BCI2000 data...")
        while True:
            # Block until a packet arrives, then take the most recent one
            packet = read_latest_packet(sock)
            if packet is None:
                continue

            # Decode the packet
            try:
                arm_horz, arm_vert, arm_move = decode_packet(packet)
            except (IndexError, ValueError) as e:
                print(f"  Bad packet, skipping: {e}")
                continue

            # Act on the decoded values
            if not arm_move:
                base.Stop()
            else:
                move_velocity(base, base_cyclic, arm_horz, arm_vert)


if __name__ == "__main__":
    main()
