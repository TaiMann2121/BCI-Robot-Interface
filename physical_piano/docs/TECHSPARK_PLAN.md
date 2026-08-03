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
- 11 keys = **3 tiles** (5 + 5 + 1), joined with M3 hardware.
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
   - likely fit the laser bed in one piece (545 mm) where the 254 mm print bed
     cannot;
   - reduce printed mass from ~502 g to ~275 g (**$321 → ~$176**). Note the
     saving is *modest*, not half: laser machine time is billed hourly and
     isn't quoted on the services page, so net saving is likely **$30–80**.
     **Ask what laser time actually costs** — it decides whether the cost
     argument holds at all. The pitch accuracy above is the real reason.

   A worked layered design already exists at
   [`../cad/piano_base_laser.scad`](../cad/piano_base_laser.scad): four flat layers
   (base / spacer / switch plate / stop rail) whose thicknesses land the switch
   plate at z=12 mm and the stop at z=25 mm — identical to the printed version,
   so key height and arm height are unchanged. Only 22 small hinge blocks stay
   printed, because they need a cross-drilled pin hole a laser can't make.

   Specifics to confirm: **can the bed take 545 mm**, and can they supply
   **~1.5 mm stock** (the thickness MX switches clip into)? If 1.5 mm is too
   flimsy over that span, is a stepped two-layer plate (1.5 mm with 14 mm holes
   over a thicker backing with clearance holes) feasible?
4. **Tile joining.** The base cells now carry alignment dowel half-holes on
   every edge, so a tile seam closes onto a 3 mm rod rather than being butted
   by eye. Worth asking whether they would also glue or pin the seam, since
   the 50 mm key pitch — what the arm is calibrated to — has to survive two
   joins on this route. **This is now the likely route**, so it deserves more
   attention than the laser alternative.
5. Turnaround time and how billing works against our lab's oracle string.

### Phase 2 — Prototype ONE key
Print **1 white key + 1 base cell + 1 black key** (~$30 of material) and check:

- Does the key pivot freely and return cleanly?
- Does the switch actuate before the cap hits the bottom stops?
- Do the robot's fingers land in the **front clear zone** (see below)?
- Is the key-top height reachable by the arm's vertical adjustment?

**Do not batch 11 until this passes.** Tuning a parameter costs one reprint at
this stage and eleven reprints later.

### Phase 3 — Full run
Once the prototype is signed off, submit:
- 11 × white key lever
- 3 × base tile (5 + 5 + 1 cells, with black-key grooves at the right indices)
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
| Base tile (5 cells) | `piano_base_printed.scad` | `"tile"` | print | 3 (5+5+1) |
| Frame cheek | `piano_frame.scad` | `"cheek"` | print | 2 |
| Frame front rail segment | `piano_frame.scad` | `"front_seg"` | print | 3 |
| Frame back rail segment | `piano_frame.scad` | `"back_seg"` | print | 3 |
| Hinge pin | — | — | buy 3 mm rod, cut | — |
| Tile alignment dowels | — | — | same 3 mm rod, 4 short pieces | — |

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

*We don't have OpenSCAD on the lab PC yet — it's a free download, or TechSpark
staff can help with file prep as part of professional services.*

---

## Design status

✅ **Black-key clearance — resolved.** Black keys occupy the rear 62% of each
key, so fingers must press in the front 53.2 mm. Measured on the rig: the
fingertip lands **35 mm** from the front edge. Comfortably clear, no
repositioning needed.

⏳ **Base construction — depends on consult question 3.** If laser-cutting the
switch plate is approved, the base is redesigned from printed 50 mm cells into a
stack of flat laser-cut layers, and only the key levers and black keys stay 3D
printed. **Do not start that rework until TechSpark confirms bed size and
material** — and do not commit to the printed-tile base until question 3 is
answered either way.
