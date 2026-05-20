# BCI Robot Interface

A brain-computer interface (BCI) controlled robotic arm and hand system developed in the He Lab. BCI2000 decodes neural signals and streams control outputs to a Kinova Gen3 robotic arm and an Allegro Hand V4, enabling real-time robotic control from brain activity.

## System Overview

```
BCI2000 (Windows)
  ├── UDP port 5006 → arm_controller.py  → Kortex API → Kinova Gen3 Arm
  └── UDP port 5005 → myAllegroHand.exe  → PCAN-USB   → Allegro Hand V4
```

The arm controller moves the end effector in 2D space based on cursor position outputs from BCI2000. The hand controller curls individual fingers based on per-finger probability outputs from an EEGNet classifier running inside BCI2000.

## Repository Structure

```
BCI_RobotInterface/
├── arm/                    Kinova Gen3 arm controller (Python)
├── hand/                   Allegro Hand V4 controller (C++ Visual Studio project)
├── simulator/              BCI2000 simulator for testing without a real experiment
└── docs/
    └── setup_guide.md      Full installation and configuration guide
```

## Getting Started

See [docs/setup_guide.md](docs/setup_guide.md) for complete setup instructions including hardware requirements, network configuration, software installation, and build steps.

For testing without BCI2000, the simulator in `simulator/bci_arm_hand_simulator.py` replicates the BCI2000 data stream and supports individual arm/hand commands as well as full combined demo sequences.

For real BCI2000 experiments, use the batch files in `BCI2000/batch/`:
- `SigGen_BCI2000_arm.bat` — arm control paradigm
- `SigGen_BCI2000_finger.bat` — finger control paradigm

## Hardware

- Kinova Gen3 robotic arm (connected via Ethernet at `192.168.1.10`)
- Allegro Hand V4 — right hand configuration
- PEAK PCAN-USB CAN adapter

## Contact

He Lab — please reach out to the lab with any questions about this project.
