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

Per supervisor: **include the black keys even though the task never presses
them.** Geometry mirrors the simulator exactly
(`Piano_Application_vel.py:775`) so the physical board matches the screen:

| Property | Value |
|----------|-------|
| Count / positions | **7**, between white keys at indices `[0, 2, 3, 5, 6, 7, 9]` |
| Width | 0.58 × key width = **26.1 mm** |
| Length | 0.62 × key length = **86.8 mm**, occupying the **rear** |
| Rise above white key tops | 10 mm (parametric) |
| Function | **none** — fixed risers, no switch, no wiring |

Indices `2,3,5,6,7` are the real C♯/D♯/F♯/G♯/A♯ of the C–B octave; `0` and `9`
continue the visual pattern across the padding keys, exactly as the sim draws it.

> ✅ **Clearance confirmed.** Black keys fill the rear 86.8 mm, so the fingers
> must contact the white keys within the **front 53.2 mm** (`front_clear`).
> Measured on the rig: the fingertip lands **35 mm** from the front edge — well
> inside the clear zone, so no black key is in the finger's path and no
> repositioning is needed. This sets `contact_x = 35` in the CAD, which also
> fixes where the switch and stop shoulders sit. (The CAD still warns if
> `contact_x` is ever moved into the black-key zone.)

## Key → note → pin mapping

Key index runs **left → right**. Indices 2–8 are the named white keys; 0,1
and 9,10 are padding keys (they still sound, matching the sim). Sim
frequencies are from `Piano_Application_vel.py:753`. "Deep" = one octave down
(the placeholder sound), toggled by `OCTAVE_DOWN` in the firmware.

| Idx | Sim label | Sim note | Sim freq (Hz) | Deep freq (Hz) | Arduino pin |
|----:|:---------:|:--------:|--------------:|---------------:|:-----------:|
| 0   | (pad)     | Bb3      | 233           | 116            | D2          |
| 1   | (pad)     | B3       | 247           | 123            | D3          |
| 2   | **C**     | C4       | 262           | 131            | D4          |
| 3   | **D**     | D4       | 294           | 147            | D5          |
| 4   | **E**     | E4       | 330           | 165            | D6          |
| 5   | **F**     | F4       | 349           | 175            | D7          |
| 6   | **G**     | G4       | 392           | 196            | D8          |
| 7   | **A**     | A4       | 440           | 220            | D9          |
| 8   | **B**     | B4       | 494           | 247            | D10         |
| 9   | (pad)     | C5       | 523           | 262            | D11         |
| 10  | (pad)     | Db5      | 554           | 277            | D12         |

Speaker/piezo output: **D13**.

## Wiring

Every switch uses the Arduino's internal pull-up (`INPUT_PULLUP`), so **no
external resistors**. Wire each switch between its pin and GND:

```
  D2 ─────[ key 0 switch ]───── GND
  D3 ─────[ key 1 switch ]───── GND
   ⋮            ⋮                 ⋮
 D12 ─────[ key 10 switch ]──── GND     (all switch commons tie to GND)

 D13 ──[ 100Ω ]──╢ piezo ╟──── GND      (passive buzzer / piezo)
        or D13 ── amp IN, amp OUT ── speaker, for louder sampled/tone audio
```

Pressed key reads LOW. Firmware debounces (15 ms) and plays the tone while the
key is held, silencing on release. tone() is **monophonic** — only one key
sounds at a time, which is fine because the robot presses one finger per phase.

## Sound (decided: electronic, computer-tunable)

Per supervisor: **electronic tones, tunable from a computer.** Implemented as
Arduino `tone()` square-wave notes whose **pitch is set live over USB serial**
and stored in EEPROM, so a tuned instrument keeps its sound with no computer
attached and no re-flashing.

- **What's tunable:** each key's frequency (Hz), 0 or 20–8000. `tone()` fixes
  the *timbre* to a square wave — pitch and note length are adjustable, the
  waveform shape is not. (Shaping the waveform itself would need a synthesis
  library such as Mozzi, or the sampled-audio/DFPlayer path — out of scope for
  the chosen "electronic" sound.)
- **Defaults:** the simulator's 11 frequencies (matches BCI2000 out of the box).
- **How to tune:** either open the Arduino IDE Serial Monitor (115200 baud) and
  type commands, or use the helper below.

### Tuning workflow

[`tuner/piano_tuner.py`](../tuner/piano_tuner.py) (needs `pip install pyserial`):

```bash
python tuner/piano_tuner.py --port COM5
```

Then, at the `tuner>` prompt: `set 4 300` to change a key, `play 4` to hear it,
`save` to persist the whole set to the Arduino's EEPROM. Presets can be written
to / read from JSON (`savefile deep.json` / `loadfile deep.json` then `push`)
so you can keep e.g. a "deep" tuning and a "sim-matched" tuning side by side.

Firmware serial commands: `list | set <i> <hz> | play <i> | stop | save | load | reset | help`.

## Bill of materials (buy)

| Qty | Item | Notes |
|----:|------|-------|
| 1   | Arduino Uno or Nano | Uno is easiest to prototype; Nano if space-tight |
| 11 (+spares) | **MX-style linear keyboard switches** (~45 gf, 4 mm travel) — *chosen* | Kailh/Cherry linear red. Supplies contact + return spring + travel in one part, so there is **no separate return spring**. 45 gf actuation is far below the weakest finger (362 gf). Standard 14 × 14 mm plate mount. Wire the two switch pins to the Arduino pin/GND |
| 1   | Passive piezo buzzer *(fast path)* | Direct `tone()` output |
| —   | *or* small Class-D amp + 8Ω speaker | Louder; needed if you later switch to sampled audio |
| ~   | Hookup wire, breadboard or proto-PCB | 11 signal + common GND |
| 1   | USB cable | Power + serial monitor |

*Optional upgrade for real piano timbre (if supervisor wants samples, not
beeps): DFPlayer Mini + microSD with 11 note WAV/MP3 files + 8Ω speaker. This
also enables polyphony. Firmware would change from `tone()` to serial DFPlayer
commands.*

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
