# BCI Robot Interface — Setup Guide

This guide covers everything needed to set up the BCI-controlled robotic arm and hand interface on a new Windows PC.

---

## System Overview

The interface connects a Kinova Gen3 robotic arm and an Allegro Hand V4 to a BCI2000 brain-computer interface system. BCI2000 sends control signals over UDP, which are received by two separate controller programs running simultaneously on the same Windows PC.

```
BCI2000 (Windows)
  ├── UDP port 5006 → arm_controller.py   → Kortex API (Ethernet) → Kinova Gen3 Arm
  └── UDP port 5005 → myAllegroHand.exe   → PCAN-USB (CAN bus)   → Allegro Hand V4
```

**BCI2000 update rates (confirmed from parameter files):**
- Arm data: 25 Hz (SamplingRate=1000Hz, SampleBlockSize=40)
- Hand data: 8 Hz (SamplingRate=1024Hz, SampleBlockSize=128)

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
- Look for the PCAN-USB adapter under "PEAK-System PCAN Adapters"

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

Press `Ctrl + Shift + B` or go to **Build → Build Solution**.

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

Run each component in a separate terminal window. All terminals running Python scripts must have `kortex_env39` activated.

### Step 1 — Connect hardware

1. Connect the Kinova arm to the PC via Ethernet
2. Power off the Allegro Hand
3. Connect the PCAN-USB adapter to the PC
4. Connect the CAN cable from the PCAN-USB adapter to the Allegro Hand
5. Power on the Allegro Hand

### Step 2 — Start the hand controller

Run `myAllegroHand.exe` from Visual Studio by pressing **F5**, or directly from the command line:
```
"hand\Peak Debug\myAllegroHand.exe"
```

The console should show the CAN channel opening, hardware info, and then:
```
Listening for BCI2000 finger data on UDP port 5005...
```

The hand will move to its home position on startup.

### Step 3 — Start the arm controller

In a new terminal with `kortex_env39` activated:
```
cd arm
kortex_env39\Scripts\activate
python arm_controller.py --ip 192.168.1.10
```

The arm will move to its home position, then wait for BCI2000 data.

### Step 4 — Run BCI2000 or the simulator

For real BCI2000 experiments, use the batch files in `BCI2000\batch\`:
- `SigGen_BCI2000_arm.bat` — arm control paradigm
- `SigGen_BCI2000_finger.bat` — finger control paradigm

For testing without BCI2000, use the simulator (see next section).

---

## Using the Simulator

The simulator replicates BCI2000 UDP output for testing without a real BCI2000 session. Run it in a third terminal with `kortex_env39` activated:

```
cd simulator
python bci_arm_hand_simulator.py
```

### Key commands

| Command | Description |
|---|---|
| `demo sequence` | Runs a preset 4-trial block mimicking a real experiment |
| `demo random <n>` | Runs n randomized trials |
| `demo trial <x> <y> <finger>` | One trial: arm moves to (x,y)m while finger ramps |
| `arm square <size>` | Arm traces a square, e.g. `arm square 0.1` |
| `arm circle <radius>` | Arm traces a circle, e.g. `arm circle 0.08` |
| `hand trial <finger>` | Full 5s hand trial: pre-feedback → ramp → reset |
| `hand sequence index middle thumb pinky` | Series of hand trials |
| `move <x> <y> <finger>` | Move arm and curl one finger simultaneously |
| `home` | Return arm and hand to home position |
| `stop` | Disable all movement |
| `status` | Show current state |

**Recommended first test:** `demo sequence` with both controllers running — this is the closest simulation of a real BCI2000 experiment.

**Safe arm movement ranges:** Keep x and y offsets under 0.1m when testing. Start with small values like `arm square 0.05`.

---

## Packet Formats

### Arm (UDP port 5006, 25 Hz)
```
trial   Arm_X   Arm_Y   ArmMove
```
- `Arm_X`, `Arm_Y`: uint16, center offset = 32767, scale = 1050
- `ArmMove`: 1 = movement enabled, 0 = stopped

### Hand (UDP port 5005, 8 Hz)
```
CurrentTrial   FeedbackApp   prob_thumb   prob_index   prob_middle   prob_pinky
```
- `FeedbackApp`: 1 = feedback period active, 0 = pre-feedback or inter-trial
- `prob_*`: smoothed finger probabilities (0–100 integer)

**Hand behavior:**
- `FeedbackApp=1`, max prob > threshold → `MoveFinger()` called for highest probability finger
- `FeedbackApp=0`, all probs = 0 → `MotionReset()` called, hand returns to home
- `FeedbackApp=0`, probs present (25 each) → pre-feedback period, hand stays still

---

## Key Configuration Values

### Arm controller (`arm/arm_controller.py`)
```python
HOME_X  =  0.657   # meters — update if physical setup changes
HOME_Y  =  0.001   # meters
HOME_Z  =  0.417   # meters
DEADZONE = 0.02    # meters — arm stops moving within this distance of target
MAX_SPEED = 0.4    # m/s — safety speed cap
```

To update the home position, jog the arm to the desired position using the Kinova web app (`192.168.1.10`), record the end effector coordinates, and update the constants above.

### Hand controller (`hand/RockScissorsPaper.cpp`)
```cpp
static double speed       = 0.1;    // finger flexion speed (radians per call)
static double speed_thumb = 0.12;   // thumb moves slightly faster
#define MIN_PROB_THRESHOLD  0       // minimum probability to trigger movement
```

The `initpos` array defines the hand's resting position. If the hand needs to be recalibrated, press H in the hand controller console to move to the BHand home position, then add a print statement to record `q_des` values and update `initpos` and `position` accordingly.

---

## Troubleshooting

**Arm aborts immediately on startup**
The arm's current position is too far from the home position defined in `arm_controller.py`. Jog the arm closer to home using the web app at `192.168.1.10`, or update the home position constants.

**Hand controller crashes with `libBHand.dll not found`**
Copy `libBHand.dll` from `hand\lib\BHand\` to `hand\Peak Debug\`.

**Kortex API import errors / yellow squiggles in VS Code**
Make sure `kortex_env39` is activated and VS Code is using the `kortex_env39` interpreter. The Kortex API requires Python 3.9 — it will not work with Python 3.10 or later.

**CAN channel fails to open**
Check that the PCAN-USB adapter is connected and the driver is installed. Verify in Device Manager that the adapter appears under "PEAK-System PCAN Adapters" without errors.

**Hand jitter when not moving**
Increase `DEADZONE` in `arm_controller.py`. The default 2cm should prevent jitter but may need tuning based on your setup.

**Build errors after modifying `myAllegroHand.cpp`**
Make sure `#include <winsock2.h>` appears before `#include "windows.h"` — reversing this order causes hundreds of socket redefinition errors.

---

## File Reference

```
BCI_RobotInterface/
├── arm/
│   ├── arm_controller.py          Main arm control script
│   ├── utilities.py               Kinova connection helper (unmodified)
│   └── kortex_api-2.6.0.post3-py3-none-any.whl   Kortex API installer
├── hand/
│   ├── myAllegroHand.cpp          Main hand control program (modified MainLoop)
│   ├── RockScissorsPaper.cpp      Finger motion functions (modified)
│   ├── RockScissorsPaper.h        Header (modified)
│   └── ...                        Remaining project files (unmodified)
├── simulator/
│   └── bci_arm_hand_simulator.py  BCI2000 simulator for testing
└── docs/
    └── setup_guide.md             This document
```
