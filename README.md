# BCI Robot Interface

An integrated brain-computer interface (BCI) controlled robotic arm and hand system developed in the He Lab. BCI2000 decodes neural signals and streams control outputs to a Kinova Gen3 robotic arm and an Allegro Hand V4, enabling real-time robotic control from brain activity.

## System Overview

The piano task streams all control data as a single combined record on one
BCI2000 UDP port (5005) at 8 Hz. A dispatcher owns that port and fans the record
out to the two controllers:

```
BCI2000 (Windows)
  └── UDP 5005 → bci2000_dispatcher.py ┬── UDP 5006 → arm_controller.py → Kortex API → Kinova Gen3 Arm
                                        └── UDP 5007 → myAllegroHand.exe → PCAN-USB   → Allegro Hand V4
```

The keyboard is a 1-D layout of 11 keys (the middle 7 are notes C–B). The arm
slides horizontally along the keys to track `ArmPred_X`; the hand taps one of
three fingers (`CopilotFingerPred` = left/center/right) when `FingerMovePhase`
pulses. See [docs/setup_guide.md](docs/setup_guide.md) for the packet format and
calibration.

## Repository Structure

```
BCI_RobotInterface/
├── arm/                    Kinova Gen3 arm controller (Python)
├── hand/                   Allegro Hand V4 controller (C++ Visual Studio project)
├── dispatcher/            Single-port stream splitter (Python)
├── simulator/              Piano-stream simulator for testing without BCI2000
├── BCI2000 Piano/         Piano-task BCI2000 files (bat, prm, app module) for reference
└── docs/
    └── setup_guide.md      Full installation and configuration guide
```

## Getting Started

See [docs/setup_guide.md](docs/setup_guide.md) for complete setup instructions including hardware requirements, network configuration, software installation, and build steps.

For testing without BCI2000, run `dispatcher/bci2000_dispatcher.py` alongside
`simulator/bci_arm_hand_simulator.py` — the simulator replicates the real piano
stream (single port, 8 Hz, BCI2000 watch-packet framing) and lets you drive arm
positions and finger presses interactively.

For real experiments, launch BCI2000 with `BCI2000 Piano/SigGen_Piano_vel.bat`.

## Hardware

- Kinova Gen3 robotic arm (connected via Ethernet at `192.168.1.10`)
- Allegro Hand V4 — right hand configuration
- PEAK PCAN-USB CAN adapter

## Contact

He Lab — please reach out to the lab with any questions about this project.
