# Plan for Working with CMU TechSpark

How we get the physical piano's mechanical parts made. Based on the TechSpark
services page: <https://engineering.cmu.edu/techspark/facilities/services.html>

---

## What TechSpark offers us

**3D printers**

| Printer | Process / material | Build volume | Min feature |
|---------|--------------------|--------------|-------------|
| Bambu X1C | FDM, PLA | 10 × 10 × 10″ (254 mm) | 0.4 mm |
| Stratasys F170 | FDM, ABS + **soluble support** | 10 × 10 × 10″ | 0.4 mm |
| Formlabs Form 3 | SLA resin (listed as coming soon) | 14.5 × 14.5 × 19.3 cm | 85 µm |

**Materials & pricing:** PLA **$0.64/g** · ABS **$1.03/g** · resin **$1.08/g**

**Also available:** machining, fabrication, welding, CNC, **laser cutting**, and
CAD/file-prep help from staff.
Professional services $65/hr + machining $72/hr or fabrication $74/hr.

**File formats accepted:** `.stl` `.obj` `.3mf` `.zip`

**How jobs are submitted:** through the **FBS system** at <https://cmu.fbs.io/>,
after an in-person consult at **Hamerschlag Hall C124**. Billing is via a CMU
oracle string / Andrew HUB account.

**Contacts**
- 3D printing & fabrication — **Jen Hitchcock**, jhitchco@andrew.cmu.edu
- Machining — **Ed Wojciechowski**, wojo@andrew.cmu.edu

---

## The one hard constraint this creates

**The keyboard is 545 mm wide; the build volume is 254 mm.** The keybed cannot
be printed as one piece. The CAD is already designed around this: the base is
built from **tileable 50 mm cells**, so we print it in runs and join them.

- 5 cells per tile = 250 mm → fits the 254 mm bed with 4 mm to spare.
- 11 keys = **3 tiles** (5 + 4 + 2 = cells 0-4, 5-8, 9-10), joined with M3
  hardware. The split is **not** free: the black keys' switch sockets straddle
  the white-key boundaries, so a seam must not land on one or the glue joint
  would run through the 14 mm hole the MX clips grip. Black keys sit after
  cells 0, 2, 3, 5, 6, 7 and 9, so only "after 4" and "after 8" are seam-safe,
  and with a 5-cell tile limit that is the only 3-way split that works.
  (5 + 5 + 1 put a seam after cell 9, which *is* a black-key boundary.)
- Individual white keys (140 × 45 mm) and black keys (87 × 26 mm) fit easily and
  can be batched many-per-plate.

---

## Proposed plan

### Phase 1 — Consult (before printing anything)
Go to **HH C124** and talk to Jen Hitchcock. Bring the CAD and these questions:

1. **Tolerances for moving parts.** Our design has a pin hinge and a sliding
   plunger with **0.4 mm** clearances. Is that achievable on the X1C in PLA, or
   should we open it up? *(This is the single most important question — the
   whole mechanism depends on the key pivoting freely without slop.)*
2. **PLA vs. ABS.** PLA is cheapest. The F170's **soluble support** could print
   the hinge better. Is ABS worth the 1.6× material cost here?
3. **Laser-cut the switch plate instead of printing tiles.** ⭐ *Highest-value
   question.* MX switches are plate-mount: they clip into a flat plate with
   14 × 14 mm square holes. Cutting that as **one piece** would:
   - hold all 11 switches at an exact **50 mm pitch with no tile seams** — the
     arm's calibration depends on that pitch, so this removes a real risk, not
     just a cost;
   - likely fit the laser bed in one piece where the 254 mm print bed cannot —
     but note the SHEET is **565 x 174 mm**, not 545. 545 is the keyboard width;
     the cut part adds a 10 mm side margin so the outermost hinge brackets land
     on material. Ask about 565, or a yes here becomes a no later;
   - reduce printed mass from ~502 g to ~275 g (**$321 → ~$176**). Note the
     saving is *modest*, not half: laser machine time is billed hourly and
     isn't quoted on the services page, so net saving is likely **$30–80**.
     **Ask what laser time actually costs** — it decides whether the cost
     argument holds at all. The pitch accuracy above is the real reason.

   A worked layered design already exists at
   [`../cad/piano_base_laser.scad`](../cad/piano_base_laser.scad): **three** flat
   layers — structure **9.0 mm**, switch plate **1.5 mm**, stop rail
   **13.0 mm** — whose thicknesses land the switch plate top at **z = 10.5 mm**
   and the stop top at **z = 23.5 mm**, identical to the printed route, so key
   height and arm height are unchanged either way. Only **12** small hinge
   brackets stay printed, because they need a cross-drilled pin hole a laser
   cannot make. (An earlier version had a fourth "spacer" layer and 22
   brackets; the spacer had no remaining job once the structural layer was
   drilled through under every switch, and there is one bracket per key
   boundary, which is 12.)

   Specifics to confirm: **can the bed take 565 x 174 mm**, and can they supply
   **1.5 mm stock** (the thickness MX switches clip into — this one is
   mandatory, not a preference) plus 9.0 mm and 13.0 mm? If 1.5 mm is too
   flimsy over that span, is a stepped two-layer plate (1.5 mm with 14 mm holes
   over a thicker backing with clearance holes) feasible?

   Also ask about **kerf compensation**: the switch cutout is specified
   14.00 ±0.05 mm and an uncompensated cut comes out ~0.2 mm oversize, which is
   the difference between a switch that clips and one that rattles. See the
   test-coupon step in BUILD.md.
4. **Tile joining.** The base cells carry alignment dowel half-holes at the
   two tile seams, so a seam closes onto a 3 mm rod rather than being butted
   by eye. Worth asking whether they would also glue or pin the seam, since
   the 50 mm key pitch — what the arm is calibrated to — has to survive two
   joins on this route. **This is now the likely route**, so it deserves more
   attention than the laser alternative.
5. Turnaround time and how billing works against our lab's oracle string.

### Phase 2 — Prototype ONE key

**Before this:** cut a hole-size coupon and set `mx_cut` from it, and put
calipers on a real switch for `mx_well_w` / `mx_shoulder_w`. Both are in
BUILD.md → "Open items". A switch that will not clip in makes every other
question on this list unanswerable.

Print **1 white key + 1 base cell + 1 black key** (~$30 of material) —
`mode = "assembly"` in `piano_base_printed.scad` is exactly that trio — and
check:

- Does the switch clip into the plate and stay there when pulled by hand?
- Does the key pivot freely and return cleanly?
- Does the switch actuate before the cap hits the bottom stops?
- Does the cap land on the **stop shoulders**, not on the switch? (Press hard —
  the whole point is that the frame takes the robot's overshoot.)
- Does the black keycap grip its cross, and travel its full 3.6 mm without
  fouling the switch housing?
- Do the robot's fingers land in the **front clear zone** (see below)?
- Is the key-top height reachable by the arm's vertical adjustment?

**Do not batch 11 until this passes.** Tuning a parameter costs one reprint at
this stage and eleven reprints later.

### Phase 3 — Full run
Once the prototype is signed off, submit:
- 11 × white key lever
- 3 × base tile (5 + 4 + 2 cells, with black-key switch sockets at the right
  boundaries)
  *— or the laser-cut plate stack, if consult question 3 is a yes*
- 7 × black key

> ⚠️ **Specify low infill (~20%) on the key levers.** This is a functional
> requirement with a hard number: the switch datasheet guarantees only **15 gf**
> of return force, so the **maximum safe key mass is 24 g**. A near-solid key at
> ~41 g would press its own switch and self-trigger. At ~20% infill (~16 g) there
> is a 1.5× margin. It is also cheaper, since TechSpark bills by the gram.

### Phase 4 — Assembly & integration
Wire the switches to the Arduino, flash the firmware, tune the tones, then set
the arm height so the resting fingertips hover 2–5 mm above the key tops, and
re-run the demo sequence.

---

## Parts manifest — what is made how

> ⚠️ **The CAD files are split by ROUTE, not by process.** `piano_base_laser.scad`
> is the laser *route* — it still contains one 3D-printed part. And **either route
> needs `piano_keys.scad`**, because the key levers and black keys are printed in
> both. Do not hand over a single file and assume it covers everything.

**Route A — all 3D printed**

| Part | File | `mode` | Process | Qty |
|------|------|--------|---------|----:|
| Key lever (notched for the black keys) | `piano_keys.scad` | `"key"` | print, PLA ~20% infill | 11 |
| Black key (switched keycap) | `piano_keys.scad` | `"black"` | print | 7 |
| Base tile | `piano_base_printed.scad` | `"tile"`, `tile_i` = 0/1/2 | print | 3 (5+4+2) |
| Frame cheek | `piano_frame.scad` | `"cheek"` | print | 2 |
| Frame front rail segment | `piano_frame.scad` | `"front_seg"` | print | 3 |
| Frame back rail segment | `piano_frame.scad` | `"back_seg"` | print | 3 |
| Hinge pin | — | — | buy 3 mm rod, cut | — |
| Tile alignment dowels | — | — | same 3 mm rod, 4 short pieces | — |

`mx_switch.scad` is **not a part**. It is a to-scale model of the Kailh switch
plus fit checks that place it in the board, so switch clearances can be looked
at instead of argued from numbers. Run its `"white"`, `"black"` and
`"fit_slice"` modes after any change to the socket, stop or keycap geometry.

Feet are printed into every base cell, so this route needs **no standoffs**.

**Route B — laser-cut base** *(the one we're asking about)*

| Part | File | `mode` | Process | Qty |
|------|------|--------|---------|----:|
| Key lever | `piano_keys.scad` | `"key"` | **print** | 11 |
| Black key | `piano_keys.scad` | `"black"` | **print** | 7 |
| Structure sheet | `piano_base_laser.scad` | `"2d_struct"` | **laser, 9 mm** | 1 |
| Switch plate | `piano_base_laser.scad` | `"2d_switch_plate"` | **laser, 1.5 mm** | 1 |
| Stop rail | `piano_base_laser.scad` | `"2d_stop_rail"` | **laser, 13 mm** | 1 |
| Hinge bracket | `piano_base_laser.scad` | `"hinge_block"` | **print** | 12 |
| Hinge pin | — | — | buy 3 mm rod, ~570 mm | 1 |
| Standoffs | — | — | buy, 12 mm M3 | 6 |

So Route B is **3 laser parts + 30 printed parts**, drawn from **two** files.

## What to send them

- **Laser:** `../cad/piano_base_laser.scad` exported to **DXF** — one file per `2d_*`
  mode (3 files), each tagged with its stock thickness.
- **Print:** STL per part — key lever and black key (`piano_keys.scad`), plus
  either the base tiles (`piano_base_printed.scad`)
  or the hinge bracket (`piano_base_laser.scad`).
- This document, for the manifest, build volumes, and material context.

*OpenSCAD is installed on the lab PC. Open any `cad/*.scad` file, set `mode`,
press F6, then File > Export. TechSpark staff can help with file prep as part of
professional services if needed.*

---

## Design status

✅ **Black-key clearance — resolved.** Black keys occupy the rear 62% of each
key, so fingers must press in the front 53.2 mm. Measured on the rig: the
fingertip lands **35 mm** from the front edge. Comfortably clear, no
repositioning needed.

⏳ **Base construction — still a choice, no longer a rework.** BOTH routes are
now fully modelled: `piano_base_printed.scad` (3 tiles, 5 + 4 + 2 cells) and
`piano_base_laser.scad` (3 flat layers + 12 printed brackets). Picking one is a
decision, not a redesign. The laser route cuts all 11 switch positions in ONE
operation, so the 50 mm pitch the arm is calibrated to has no glued seams to
drift across, and it is far cheaper in material; the printed route needs no
laser. **Confirm laser access and 9.0 / 1.5 / 13.0 mm stock before committing.**
They are alternatives — do not build both.

⏳ **Switch fit — not yet verified against hardware.** Every dimension the CAD
takes from the switch datasheet has been checked line by line, but three things
cannot be settled on paper: whether the switch actually purchased matches the
datasheet, the two stem dimensions the datasheet draws without dimensioning, and
whether the fabrication process holds the 14.00 ±0.05 plate cutout. See
BUILD.md → "Open items". **Nothing should be fabricated in quantity until these
close.**
