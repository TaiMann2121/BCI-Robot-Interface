# BCI Robot Interface — Setup Guide

This guide covers everything needed to set up the BCI-controlled robotic arm and hand interface on a Windows PC.

---

## System Overview

The interface connects a Kinova Gen3 robotic arm and an Allegro Hand V4 to a BCI2000 brain-computer interface system running the piano typing task.

For the piano task, BCI2000 streams **all** control data as a single combined
record on **one** UDP port (5005) at **8 Hz**. Because two processes cannot
reliably share a UDP port, a dispatcher owns 5005 and forwards the record to the
two controllers on separate local ports:

```
BCI2000 (Windows)
  └── UDP 5005 → bci2000_dispatcher.py ┬── UDP 5006 → arm_controller.py → Kortex API (Ethernet) → Kinova Gen3 Arm
                                        └── UDP 5007 → myAllegroHand.exe → PCAN-USB (CAN bus)     → Allegro Hand V4
```

**Stream (confirmed from `SigGen_Piano_vel.bat` and `Piano_Application_vel.py`):**
- Single port 5005, single tab-separated record, 8 Hz (SamplingRate=1024Hz, SampleBlockSize=128).
- The arm is **1-D** (horizontal slide along the keys). The fingers handle key presses; the arm does not move vertically.

---

## Hardware Requirements

- Kinova Gen3 robotic arm
- Allegro Hand V4 (right hand configuration)
- PEAK PCAN-USB CAN adapter
- Windows 11 PC
- Ethernet cable (for arm connection)
- CAN bus cable (for hand connection, included with Allegro Hand)

---

## Network Configuration

The Kinova arm communicates over Ethernet. Configure the PC's Ethernet adapter:

- **Arm IP address:** `192.168.1.10`
- **PC Ethernet adapter IP:** `192.168.1.11`
- **Subnet mask:** `255.255.255.0`

To verify connectivity after configuring, run:
```
ping 192.168.1.10
```
You should receive replies with no packet loss.

---

## Software Requirements

### 1. Python 3.9

The arm controller requires Python 3.9 specifically due to a compatibility issue between the Kortex API and newer Python versions (`collections.MutableMapping` was removed in Python 3.10).

Download from: https://www.python.org/downloads/release/python-3913/

During installation, check **"Add python.exe to PATH"**.

Verify installation:
```
py -3.9 --version
```

### 2. Kortex API (Python)

The Kortex API is distributed as a `.whl` file — it is not available on PyPI. The file `kortex_api-2.6.0.post3-py3-none-any.whl` is included in the `arm/` folder of this repository.

Set up a dedicated virtual environment:
```
py -3.9 -m venv kortex_env39
kortex_env39\Scripts\activate
pip install arm\kortex_api-2.6.0.post3-py3-none-any.whl
pip install numpy
```

**Important:** Always activate `kortex_env39` before running the arm controller. Do not use any other Python environment for arm control, as the Kortex API will not be available.

### 3. PEAK PCAN-USB Driver

Download **Device driver setup 5.x for Windows** from:
https://www.peak-system.com/PCAN-USB.199.0.html

During installation, keep the default options — **CAN device drivers** and **PCAN-Basic API** should both be selected. You may need to reboot after installation.

After installation, verify the driver installed correctly:
- Open Device Manager (Start → search "Device Manager")
- Look for the PCAN-USB adapter under "CAN-Hardware"

### 4. Visual Studio (Community Edition)

Required to build the hand controller C++ project.

Download from: https://visualstudio.microsoft.com/downloads/

During installation, select the **"Desktop development with C++"** workload.

**Note:** Visual Studio (full IDE) is different from VS Code (lightweight editor). Both may be used — VS Code for Python scripts, Visual Studio for the C++ hand controller.

---

## Building the Hand Controller

### Step 1 — Open the project

Open Visual Studio and load:
```
hand\myAllegroHand.sln
```

A migration report may appear in your browser — this is harmless. The project was originally created in Visual Studio 2010 and will be automatically updated.

### Step 2 — Set configuration

At the top of Visual Studio, set the configuration dropdown to **Peak Debug** and platform to **Win32**.

### Step 3 — Set DLL path

Right-click **myAllegroHand** in the Solution Explorer → **Properties**.

Navigate to **Configuration Properties → Debugging** and set the **Environment** field to:
```
PATH=C:\Program Files\PEAK-System\PEAK-Drivers 5\;%PATH%
```

Click Apply then OK.

### Step 4 — Build

Go to **Build → Build Clean Solution → Build Solution**.

The output should show:
```
Build: 1 succeeded, 0 failed, 0 skipped
```

The compiled executable will be at:
```
hand\Peak Debug\myAllegroHand.exe
```

### Step 5 — Copy DLL

Copy `libBHand.dll` from `hand\lib\BHand\` to `hand\Peak Debug\`:
```
copy "hand\lib\BHand\libBHand.dll" "hand\Peak Debug\"
```

---

## Running the Interface

Run each component in a separate terminal window. All terminals running Python scripts must have `kortex_env39` activated. **Start the dispatcher first** — it owns port 5005, and the controllers listen on the ports it forwards to.

### Step 1 — Connect hardware

1. Connect the Kinova arm to the PC via Ethernet
2. Power off the Allegro Hand
3. Connect the PCAN-USB adapter to the PC
4. Connect the CAN cable from the PCAN-USB adapter to the Allegro Hand
5. Power on the Allegro Hand

### Step 2 — Start the dispatcher

In a terminal (a plain Python is fine — the dispatcher has no Kortex dependency):
```
python dispatcher\bci2000_dispatcher.py
```
It should print that it is listening on `127.0.0.1:5005` and forwarding to 5006 (arm) and 5007 (hand).

### Step 3 — Start the hand controller

Run `myAllegroHand.exe` from Visual Studio by pressing **F5**, or directly from the command line:
```
"hand\Peak Debug\myAllegroHand.exe"
```

The console should show the CAN channel opening, hardware info, and then:
```
Listening for piano finger data on UDP port 5007 (via dispatcher)...
```

The hand will move to its resting pose on startup.

### Step 4 — Start the arm controller

In a new terminal with `kortex_env39` activated:
```
cd arm
kortex_env39\Scripts\activate
python arm_controller.py --ip 192.168.1.10
```

The arm will move to its home position (hand over the center key), then track `ArmPred_X`.

### Step 5 — Run BCI2000 or the simulator

For real experiments, launch BCI2000 with `BCI2000 Piano\SigGen_Piano_vel.bat`.

For testing without BCI2000, use the simulator (see next section).

---

## Using the Simulator

The simulator replicates the real piano stream (single port 5005, 8 Hz, BCI2000 watch-packet framing) for testing without a real BCI2000 session. It talks to the **dispatcher**, so start the dispatcher (and, optionally, the controllers) first. Run it in its own terminal:

```
cd simulator
python bci_arm_hand_simulator.py
```

### Key commands

| Command | Description |
|---|---|
| `trial <key> <finger>` | Full trial: slide arm to key window (1–9), then press finger (0–2) |
| `demo [n]` | Run n random trials (default 4) |
| `key <index>` | Slide the arm so the middle finger is over key index 1–9 |
| `armx <px>` | Set raw arm position directly, −420..420 px (0 = center key 5) |
| `press <0\|1\|2>` | Fire a single finger press (0=left, 1=center, 2=right) |
| `home` | Recenter the arm over the center key, lift the finger |
| `status` | Show current stream state |

**Recommended first test:** `demo 4` with the dispatcher (and both controllers) running — this is the closest simulation of a real piano session.

**Finger vs. key:** `CopilotFingerPred` 0/1/2 presses the key to the left of / under / right of the arm's middle finger, so the pressed key = `ArmCurrentIndex + finger − 1`.

---

## Packet Formats

### Piano stream (BCI2000 → UDP port 5005, 8 Hz)

BCI2000's `ADD WATCH` sends one tab-separated record per packet, framed with a
leading frame counter and a trailing tab + CRLF:
```
<counter>  CurrentTrial  InnerTrialCount  ArmPred_X  FingerMovePhase  CopilotFingerPred  targetKeyIndex  pressedKeyIndex  ArmCurrentIndex  <CRLF>
```

| Field | Range | Meaning |
|---|---|---|
| `CurrentTrial` | 1–5 | block number |
| `InnerTrialCount` | 0+ | step within the block |
| `ArmPred_X` | 32347–33187 | arm horizontal position, = px + 32767 offset (px ∈ [−420, 420]) |
| `FingerMovePhase` | 0/1 | **edge-triggered** press pulse — press on the 0→1 transition |
| `CopilotFingerPred` | 0/1/2 | finger to press: left / center / right |
| `targetKeyIndex` | 2–8 | intended note key (C–B) |
| `pressedKeyIndex` | 0–10 | key actually pressed (= `ArmCurrentIndex + CopilotFingerPred − 1`) |
| `ArmCurrentIndex` | 1–9 | key the middle finger is currently over |

### Forwarded record (dispatcher → arm 5006 / hand 5007)

The dispatcher drops the leading counter and trailing junk (it splits on tabs,
discards empty tokens, and keeps the last 8 fields — robust to the counter's
digit count) and re-sends the same 8 fields, tab-separated, to both controllers:
```
CurrentTrial  InnerTrialCount  ArmPred_X  FingerMovePhase  CopilotFingerPred  targetKeyIndex  pressedKeyIndex  ArmCurrentIndex
```
- **Arm controller** uses `ArmPred_X` only.
- **Hand controller** uses `FingerMovePhase` (rising edge) and `CopilotFingerPred`.

> **Note on the press pulse:** `FingerMovePhase` is true only during the
> `FingerHold` phase (`ResultHoldTime`, ~100 ms in the loaded `.prm`). At 8 Hz
> (~125 ms/packet) that is captured in one packet, occasionally zero. If presses
> are ever missed on the real system, raise `ResultHoldTime` in the parameters.

---

## Key Configuration Values

### Arm controller (`arm/arm_controller.py`)
```python
HOME_X  =  0.657   # meters — hand over the CENTER key; update if setup changes
HOME_Y  =  0.001   # meters — horizontal axis, along the key row
HOME_Z  =  0.417   # meters
DEADZONE = 0.005   # meters — arm stops moving within this of target (~0.1 key)
MAX_SPEED = 0.4    # m/s — safety speed cap
ARM_Y_SIGN = +1    # flip to -1 if the arm slides the wrong way along the keys
```

Calibration (derived from `Piano_Application_vel.py`, do not change unless the
BCI2000 geometry changes): `105` px per key, key width `0.0508 m` (2 in), so
`M_PER_PX = 0.0508 / 105`. `ArmPred_X` range ±420 px = ±4 keys = ±0.2032 m.

To update the home position, jog the arm so the middle finger sits over the
center key using the Kinova web app (`192.168.1.10`), record the end effector
coordinates, and update `HOME_*`. Confirm `ARM_Y_SIGN` by sending `key 6` then
`key 4` from the simulator and checking the arm moves the correct way.

### Hand controller (`hand/RockScissorsPaper.cpp`)
```cpp
// CopilotFingerPred 0/1/2 -> which Allegro finger flexes (joint ranges).
static const int fingerJoints[3][2] = { {1,3}, {5,7}, {9,11} }; // index / middle / ring
static double press_flexion = 0.35;   // radians of flexion when pressing a key
```
```cpp
// hand/myAllegroHand.cpp
#define PRESS_HOLD_MS   400           // how long to hold a press before lifting
```
Confirm `fingerJoints` matches how the three playing fingers are physically
mounted over the keys, and tune `press_flexion` / `PRESS_HOLD_MS` so a press
depresses the key cleanly without jamming.

The `initpos` array defines the hand's resting position (fingers hovering over the keys). If the hand needs to be recalibrated, add the following print block to `MainLoop()` in `myAllegroHand.cpp` immediately after the `MotionReset()` call, rebuild, and record the printed values to update `initpos` and `position` in `RockScissorsPaper.cpp`:

```cpp
MotionReset();

// Temporary calibration block — remove after recording values
Sleep(3000);  // wait for hand to reach its resting pose
printf("Resting pose joint values:\n");
for (int i = 0; i < 16; i++)
{
    printf("q[%d] = %.4f\n", i, q[i]);
}
```

---

## Troubleshooting

**Arm aborts immediately on startup**
The arm's current position is too far from the home position defined in `arm_controller.py`. Jog the arm closer to home using the web app at `192.168.1.10`, or update the home position constants.

**Hand controller crashes with `libBHand.dll not found`**
Copy `libBHand.dll` from `hand\lib\BHand\` to `hand\Peak Debug\`.

**Kortex API import errors / yellow squiggles in VS Code**
Make sure `kortex_env39` is activated and VS Code is using the `kortex_env39` interpreter. The Kortex API requires Python 3.9 — it will not work with Python 3.10 or later.

**CAN channel fails to open**
Check that the PCAN-USB adapter is connected and the driver is installed. Verify in Device Manager that the adapter appears under "CAN-Hardware" without errors.

**Hand jitter when not moving**
Increase `DEADZONE` in `arm_controller.py`. The default 2cm should prevent jitter but may need tuning based on your setup.

**Build errors after modifying `myAllegroHand.cpp`**
Make sure `#include <winsock2.h>` appears before `#include "windows.h"` — reversing this order causes hundreds of socket redefinition errors.

---

## File Reference

```
BCI_RobotInterface/
├── arm/
│   ├── arm_controller.py          Arm control (1-D key tracking, port 5006)
│   ├── utilities.py               Kinova connection helper (unmodified)
│   └── kortex_api-2.6.0.post3-py3-none-any.whl   Kortex API installer
├── hand/
│   ├── myAllegroHand.cpp          Hand control (edge-triggered press, port 5007)
│   ├── RockScissorsPaper.cpp      Finger press / reset functions
│   ├── RockScissorsPaper.h        Header
│   └── ...                        Remaining project files (unmodified)
├── dispatcher/
│   └── bci2000_dispatcher.py      Owns port 5005, fans out to arm + hand
├── simulator/
│   └── bci_arm_hand_simulator.py  Piano-stream simulator for testing
├── BCI2000 Piano/                 Piano-task BCI2000 reference files
│   ├── SigGen_Piano_vel.bat       Launches the piano task
│   ├── BioSemi_Piano.prm          Piano parameters
│   └── Piano_Application_vel.py    App module (authoritative field definitions)
└── docs/
    └── setup_guide.md             This document
```
