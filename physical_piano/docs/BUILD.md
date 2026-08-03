# Physical Piano — Build Spec

Physical 11-key piano for the BCI arm/hand piano task. Replaces the toy
mockup already validated on the physical arm/hand interface (11 keys,
4.5 cm wide with 0.5 cm gaps, one key-step = 5.0 cm, confirmed working).

The layout, key count, and note mapping intentionally match the BCI2000
simulator so the physical instrument behaves and sounds like
[`Piano_Application_vel.py`](../../BCI2000%20Piano/Piano_Application_vel.py).

## Geometry (confirmed against hardware)

| Property            | Value                              |
|---------------------|------------------------------------|
| Keys                | 11, white, in a row                |
| Key width           | 4.5 cm (1.77″)                     |
| Gap between keys    | 0.5 cm (0.20″)                     |
| Key length (depth)  | 14 cm (5.5″)                       |
| Key pitch (center→center) | **5.0 cm (1.97″)** — equals the arm's one key-step |
| Total keyboard width | 11 × 4.5 cm + 10 × 0.5 cm = **54.5 cm (21.5″)** (+ frame margin) |

The 5.0 cm pitch is the load-bearing number: each physical key center must sit
exactly 5.0 cm from the next (4.5 cm key + 0.5 cm gap) so the arm's key-step
lines up. This pitch is ~1.97″, which is why the earlier "2-inch key-step"
calibration still worked — only the key-width/gap split was mis-specified.

### Black keys (decorative)

Per supervisor: include the black keys **and make them pressable**, even though
the task never uses them. Geometry mirrors the simulator exactly
(`Piano_Application_vel.py:775`) so the physical board matches the screen:

| Property | Value |
|----------|-------|
| Count / positions | **7**, between white keys at indices `[0, 2, 3, 5, 6, 7, 9]` |
| Width | 0.58 × key width = **26.1 mm** |
| Length | 0.62 × key length = **86.8 mm**, occupying the **rear** |
| Rise above white key tops | 10 mm (parametric) |
| Function | **switched** — one MX switch each, wired like the white keys |

Indices `2,3,5,6,7` are the real C♯/D♯/F♯/G♯/A♯ of the C–B octave; `0` and `9`
continue the visual pattern across the padding keys, exactly as the sim draws it.

> ✅ **Clearance confirmed.** Black keys fill the rear 86.8 mm, so the fingers
> must contact the white keys within the **front 53.2 mm** (`front_clear`).
> Measured on the rig: the fingertip lands **35 mm** from the front edge — well
> inside the clear zone, so no black key is in the finger's path and no
> repositioning is needed. This sets `contact_x = 35` in the CAD, which also
> fixes where the switch and stop shoulders sit. (The CAD still warns if
> `contact_x` is ever moved into the black-key zone.)


### Black keys are switched, and that reshapes the white keys

Making the black keys pressable forced a change to a part that was otherwise
settled. An **MX switch housing is 15.6 mm across and the gap between white
keys is 5 mm** — the switch is three times too wide to fit, and even a bare
pushrod carrying a keycap mount needs about 6 mm. There is no arrangement that
puts a switch under a black key without widening that gap.

So each white key is **notched by 7.5 mm on the side where a black key sits**,
opening the gap to 20 mm. This is exactly what a real piano does and for the
same reason, so the board also ends up looking more authentic:

| White key | Rear width |
|---|---|
| no black neighbour | 45.0 mm |
| one black neighbour | 37.5 mm |
| two black neighbours | 30.0 mm |

The notch runs from the start of the black key zone to x = 122 mm, stopping
short of the hinge knuckle, which needs its full 45 mm to locate the key on the
pin.

**The black key itself** is a keycap pushed straight onto an MX stem, the way
any keyboard keycap mounts — no hinge, no glue, no separate spring. It travels
straight down while the white keys pivot. That difference is deliberate: a
lever here would collide with the hinge brackets sharing the same gap, and
black keys are never touched by the robot.

**They also need no stop shoulders.** The white keys have them because the
robot presses with 362–520 gf and would otherwise hammer the switch. Black keys
are hand-pressed, so bottoming out at 3.6 mm is ordinary keyboard use, well
inside the switch's 80 M cycle rating.

> ⚠️ **Three clearances are tight and should be checked on the prototype:** the
> socket boss leaves 0.5 mm each side in the widened gap; a fully pressed black
> key clears the hinge posts by 0.9 mm; and the notch ends 0.5 mm before the
> knuckle. All positive, none generous.

## Key → note → pin mapping

**18 keys: 11 white + 7 black.** Key ids run **left → right**, id 0 being the
leftmost key — the end carrying the orientation notch on the board.

White keys use the simulator's own frequencies unchanged
(`Piano_Application_vel.py:753`), so the physical piano and the on-screen one
sound identical.

| id | Key | Note | Hz | Pin |
|---:|:---|:---:|---:|:---:|
| 0  | white 0 (pad) | Bb3 | 233.08 | D2 |
| 1  | white 1 (pad) | B3  | 246.94 | D3 |
| 2  | white 2 | **C4** | 261.63 | D4 |
| 3  | white 3 | **D4** | 293.66 | D5 |
| 4  | white 4 | **E4** | 329.63 | D6 |
| 5  | white 5 | **F4** | 349.23 | D7 |
| 6  | white 6 | **G4** | 392.00 | D8 |
| 7  | white 7 | **A4** | 440.00 | D9 |
| 8  | white 8 | **B4** | 493.88 | D10 |
| 9  | white 9 (pad) | C5 | 523.25 | D11 |
| 10 | white 10 (pad) | Db5 | 554.36 | D12 |
| 11 | black in gap 0/1 | A3 † | 220.00 | A5 |
| 12 | black in gap 2/3 | C♯4 | 277.18 | A0 |
| 13 | black in gap 3/4 | D♯4 | 311.13 | A1 |
| 14 | black in gap 5/6 | F♯4 | 369.99 | A2 |
| 15 | black in gap 6/7 | G♯4 | 415.30 | A3 |
| 16 | black in gap 7/8 | A♯4 | 466.16 | A4 |
| 17 | black in gap 9/10 | D5 † | 587.33 | **D13** |

† Five black keys land on a real sharp. The outer two cannot: the simulator's
padding keys are already a semitone apart (Bb3–B3 and C5–Db5), so no note
exists between them. Those two continue the scale outwards instead. They are
decorative keys the task never presses — change the values freely in
`pc/piano_listener.py`, or set one to `0` to make that key silent.

> **Why D13 carries a padding black key.** On many Uno clones pin 13 drives the
> onboard LED directly, which can load `INPUT_PULLUP` enough to read
> unreliably. It is therefore assigned the least important key, so a flaky pin
> costs nothing that matters. If D13 misbehaves, that one decorative key stops
> working and nothing else changes.

## Wiring

Every switch uses the Arduino's internal pull-up (`INPUT_PULLUP`), so **no
external resistors** and no polarity to get right. Each switch goes between its
pin and GND:

```
   D2 ─────[ white key 0 ]───── GND
   D3 ─────[ white key 1 ]───── GND
    ⋮             ⋮               ⋮
  D12 ─────[ white key 10 ]──── GND
   A5 ─────[ black gap 0/1 ]─── GND
   A0 ─────[ black gap 2/3 ]─── GND
    ⋮             ⋮               ⋮
  D13 ─────[ black gap 9/10 ]── GND     (all commons tie to one GND bus)
```

18 signal wires plus one common ground. A pressed key reads LOW; the firmware
debounces for 15 ms, which clears the switch's 10 ms end-of-life bounce spec.

**There is no speaker on the board.** D13 was the only free pin and it is now a
key — see below.

## Sound: played by the computer

The Arduino is a **pure key scanner**. It reports `P <id>` / `R <id>` over USB
serial and makes no sound; `pc/piano_listener.py` receives those events and
plays the notes.

This is not a workaround. The BCI2000 simulator already plays its notes through
`psychopy.sound`, so PC audio is the existing architecture rather than a
departure from it — and it satisfies "electronic sound, tunable on a computer"
more literally than square waves ever did.

**What it buys us**

- The pin budget closes exactly. 18 switches need all 18 usable pins on an Uno
  (D2–D13 plus A0–A5, with D0/D1 reserved for the serial link). A speaker would
  have needed a 19th.
- Real timbre, polyphony, and any tuning — all in software, no reflashing.
- Simpler firmware: no `tone()`, no frequency table, no EEPROM.

**What it costs**

- The piano cannot make a sound standalone; the PC must be running the
  listener. Since BCI2000 is running during any real use, this is not a
  practical restriction.
- Latency is roughly 15–40 ms end to end (USB serial plus audio buffer). For
  scale, a real piano action takes ~30 ms from key to hammer.

### Running it

```bash
pip install pyserial numpy pygame
python pc/piano_listener.py --test          # play every note, no hardware
python pc/piano_listener.py --port COM5     # normal use
```

`--test` is the quickest way to confirm audio works before any switch is wired.
Add `--echo` to print each key event as it arrives.

The board also answers `ping` (replies `PONG`) and `keys` (lists every id with
its pin) on the same serial port, which is handy for checking wiring one key at
a time with the Arduino IDE's Serial Monitor.

## Bill of materials (buy)

| Qty | Item | Notes |
|----:|------|-------|
| 1   | Arduino Uno or Nano | Uno is easiest to prototype; Nano if space-tight |
| 18 (+spares) | **MX-style linear keyboard switches** (~45 gf, 3.6 mm travel) — *chosen* | 11 white + 7 black. Kailh/Cherry linear red. Supplies contact + return spring + travel in one part, so there is **no separate return spring**. 45 gf actuation is far below the weakest finger (362 gf). Standard 14 × 14 mm plate mount. Wire the two switch pins to the Arduino pin/GND |
| ~   | Hookup wire, breadboard or proto-PCB | 18 signal + common GND |
| 1   | USB cable | Power, serial link, and the sound path |

*No speaker, buzzer or amplifier is needed — the computer plays the notes. See
**Sound** above. A piezo is still useful for bench-testing switches before the
PC listener is set up, but it is not part of the finished instrument.*

## Make (3D print / machine shop)

- **Key caps + hinge mechanism (11×, print):** 4.5 cm × 14 cm tops with a
  consistent, repeatable press throw so the robot's fixed flex always closes
  the switch. Printing gives identical keys and lets you tune the throw.
  **Important — protect the switch from overshoot:** the finger drives ~3 cm
  but the switch actuates in ≤ a few mm, so give each key a **hard bottom stop**
  (key cap bottoming against the frame) positioned so the switch actuates *just
  before* the stop. The frame — not the switch internals — then absorbs the
  finger's 362–520 gf overshoot, which is what makes the mechanism durable.
  Parametric CAD implementing all of this (rear pin hinge, plunger, switch
  cradle, stop pads, return spring, up-stop hook) is in
  [`../cad/piano_keys.scad`](../cad/piano_keys.scad) — defaults are self-consistent
  with the measured numbers. **Set `contact_x` and the switch dimensions, then
  print ONE key + base cell to tune before batching 11.**
- **Base / frame (print or machine shop):** holds keys on 5.0 cm centers
  (4.5 cm key + 0.5 cm gap), mounts the switches under each key, and sits at
  the arm's working height. Total ~54.5 cm (21.5″) wide; confirm it fits inside
  the arm's reachable travel before cutting.
  **Must be tiled:** TechSpark's printers have a 254 mm build volume, so the
  545 mm keybed prints as 3 tiles (5 + 5 + 1 cells) and is joined — the CAD's
  `"tile"` mode generates these.
- **Black keys (7×, print):** decorative risers that drop into locating grooves
  at the white-key boundaries and are glued. No switches, no wiring.

## Purchasing & fabrication

- **Parts to buy, with links and budget:** [`PURCHASING.md`](PURCHASING.md)
- **Machine-shop / 3D-print plan (CMU TechSpark):**
  [`TECHSPARK_PLAN.md`](TECHSPARK_PLAN.md)

## Firmware

[`../firmware/piano_firmware.ino`](../firmware/piano_firmware.ino).
Flash with the Arduino IDE. Pitches default to the simulator's frequencies and
are tuned live over serial (see **Sound** above); the serial monitor at 115200
also prints `press N` / `release N` for bring-up testing.

## Press characterization (for switch selection)

The press is **position (PD) control**, not force control (`PressFinger`,
[RockScissorsPaper.cpp:127](../../hand/RockScissorsPaper.cpp)): the knuckle drives
`press_flexion = 0.80` rad and holds for `PRESS_HOLD_MS = 400` ms
([myAllegroHand.cpp:228](../../hand/myAllegroHand.cpp)). Contact force is therefore
emergent (Kp ≈ 800–900 × position error into the surface, up to the torque cap),
so it must be measured, not read from code.

| Spec | Value |
|------|-------|
| Fingertip vertical stroke (resting → full press) | **~3 cm (measured, press-and-hold)** |
| Resting fingertip height above table | **~4 cm (measured)** |
| Pressed fingertip height above table | **< 1 cm (measured)** |
| Press force — index (left) finger | **362 g ≈ 3.55 N (measured)** |
| Press force — middle (center) finger | **500 g ≈ 4.90 N (measured)** |
| Press force — ring (right) finger | **520 g ≈ 5.10 N (measured)** |
| **Weakest finger (sets switch spec)** | **index, 362 g ≈ 3.55 N** |

**How measured:** with a zeroed digital scale centered under one fingertip at
key height, each finger was pressed and held using the bench hold mode in the
hand controller (`1`/`2`/`3` = press-and-hold left/center/right, `L` = lift; see
[myAllegroHand.cpp](../../hand/myAllegroHand.cpp) MainLoop), reading the settled
value. `N ≈ g × 0.0098`.

The stroke/height numbers were read off the rig with the finger held in resting
vs. pressed pose (press-and-hold bench mode, not the 400 ms flash). The stroke is
the fingertip's *own* vertical descent, not the depth a key gets depressed.

**Design implications:**
- **Pre-travel is not a constraint.** With ~3 cm of fingertip stroke, any
  switch's actuation travel (sub-mm) fits with room to spare, and the keys can
  have a real, piano-like key-cap travel (~0.5–1 cm) with the switch underneath.
- **Force sets the switch choice.** The switch must fully actuate under the
  *weakest* finger, 362 gf. The chosen MX linear switch actuates at ~45 gf —
  an ~8× margin, so every finger triggers it reliably.
- **The switch must not absorb the overshoot.** MX switches bottom out
  internally at 4 mm, but the finger keeps pushing with 362–520 gf (several
  times a human keystroke). The design therefore drives the stem only 3 mm and
  lands the key cap on **integral stop shoulders** in the socket, leaving 0.6 mm
  of unused switch travel even on a worst-case switch. The frame takes the load, not the
  switch. The CAD warns if these values are ever set inconsistently.

## How the key mechanism works

Each white key is a **rear-hinged lever**, like a real piano key. A small post
(the *plunger*) on its underside rests directly on an MX switch stem:

```
              finger presses here (35 mm from front)
                       ↓
   FRONT ┌─────────────────────────────────────┐ REAR
         │              key lever              │
         └──┬────────┬─────────────────────────┴──○ ← pivot (hinge pin)
            │        │ plunger
          hook     ┌─┴──┐
                   │stem│  ← MX switch: the spring inside pushes UP
                   │▓▓▓▓│    and is what holds the key up
   ════════════════╧════╧════════════════════════  base plate
```

Inside the switch, a spring-loaded stem slides down; a contact closes at ~2 mm
of travel and the spring returns it. **There is no separate return spring** —
the MX spring both holds the key up and returns it.

The hinge pin runs **across** the keyboard so the key pivots up and down. Nothing
else locates the key: the pin holds the rear, and the stem's own top-of-travel
limit sets the resting height (via the plunger length). There is no up-stop
catch — it isn't needed.

### Why the key doesn't press its own switch

The MX spring's guaranteed return force is **15 gf minimum** (datasheet RF), so
nothing moves until something pushes harder than that. The lever geometry then divides the key's weight down:

| | |
|---|---|
| Key mass | 16 g, centre of mass 57 mm from the pivot |
| Plunger position | 92 mm from the pivot |
| Force at the stem | 16 × 57/92 = **9.9 gf** |
| Guaranteed return force (datasheet RF, min) | **15 gf** |
| Maximum safe key mass | **24 g** — ours is 16 g |

By contrast the finger presses at the same 35 mm point, so its full **362 gf**
reaches the stem against a 45 gf requirement — a huge margin the right way.

> ⚠️ **Print the keys at low infill (~20%) — this is now a hard limit.** The
> datasheet guarantees only **15 gf** of return force (RF, minimum), not the
> 30 gf preload previously assumed, so the maximum safe key mass is **24 g**. A
> near-solid key at ~41 g would push 25.4 gf and **would** sag onto its switch
> and self-trigger. At ~20% infill (16 g → 9.9 gf) there is a 1.5× margin. The
> CAD warns if `key_mass_g` exceeds the limit.

## Keyboard height & arm integration

The toy mat modeled key **width and length** well, but as a flat mat (~1 cm above
the table) it does **not** model a real key's **thickness/travel**. A real keyed
instrument will be taller. This is not a problem because the **hand+arm height is
adjustable** — the current mounting height is not fixed. So treat keyboard
thickness as a free design parameter and match the arm height to it:

1. The key/switch/hinge/stop stack is now fixed: key tops sit **42.5 mm**
   above the table (30.5 mm of board on 12 mm feet). Call this **K**.
2. Raise the arm so the **resting fingertip hovers ~2–5 mm above the key tops**
   (small positive clearance so a resting finger never holds a key down).
3. The **~3 cm stroke** then presses the key: only ~0.5–1 cm of key throw is
   needed to actuate + bottom out, so `3 cm ≫ clearance + throw` (≈2 cm margin).
   The hard bottom stop absorbs the remaining overshoot.

**To verify before finalizing:** the arm's vertical adjustment range can reach
`K + clearance`. Measured reference points on the current rig: resting fingertip
~4 cm above table, pressed fingertip < 1 cm above table (on the ~1 cm mat).

## Open items

- *(none blocking)* — geometry, sound, and press force are all measured and the
  switch spec is set. Next physical steps: order the BOM, 3D-print the keys/hinge
  mechanism, bench-test firmware + tuner, then integrate under the arm.
