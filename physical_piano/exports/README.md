# Exports — generated files for TechSpark

**These are generated.** The source of truth is `../cad/*.scad`. They are
committed anyway so that a fresh `git clone` on any machine — a laptop taken to
the consult, or TechSpark's own PC — has everything needed to quote and cut,
without needing OpenSCAD installed first.

Regenerate any of them with:

```bash
openscad -o <output> -D 'mode="<mode>"' <source>.scad
```

Do not hand-edit anything here. If a dimension changes, change it in
`../cad/piano_params.scad` and re-export.

---

## Make these FIRST

| File | Process | Stock | Why |
|------|---------|-------|-----|
| `COUPON_print_switch_holes.stl` | FDM | PLA | 7 holes, 13.8–14.4 mm |
| `COUPON_laser_switch_holes_1.5mm.dxf` | laser | **1.5 mm** | same range, same stock as the real switch plate |

The switch datasheet specifies the plate cutout as 14.00 ±0.05 mm, which
neither process holds natively — FDM undersizes holes, laser kerf oversizes
them. Clip a real switch into each hole, take the smallest one it enters
without force and cannot be pulled out of, and set `mx_cut` from it.

Nothing else should be cut in quantity until that number is known.

---

## Laser route — 3 sheets

Sheet size is **565 × 174 mm** (this is the cut part; 545 mm is the keyboard
width alone, which is *not* the number to check a bed against).

| File | Stock | Qty |
|------|-------|----:|
| `LASER_1_structure_9.0mm.dxf` | 9.0 mm | 1 |
| `LASER_2_switchplate_1.5mm.dxf` | **1.5 mm — mandatory**, this is what the MX clips grip | 1 |
| `LASER_3_stoprail_13.0mm.dxf` | 13.0 mm | 1 |
| `PRINT_hinge_bracket_x12.stl` | printed, not lasered | 12 |

The laser route also needs 6 × M3 12 mm standoffs (not yet ordered) and one
continuous 3 mm rod ≥ 581 mm.

## Printed route — 3 tiles

| File | Qty | Notes |
|------|----:|-------|
| `PRINT_base_tile_0.stl` | 1 | cells 0–4, 250 mm |
| `PRINT_base_tile_1.stl` | 1 | cells 5–8, 200 mm |
| `PRINT_base_tile_2.stl` | 1 | cells 9–10, 100 mm |

The 5 + 4 + 2 split is not arbitrary — it is the only 3-way split that keeps
both seams off a black-key boundary, where a glue joint would run through a
switch's mounting hole.

## Both routes

| File | Qty | Notes |
|------|----:|-------|
| `PRINT_key_lever_x11.stl` | 11 | **~20% infill — this is functional.** The switch guarantees only 15 gf of return force, so a key over 24 g presses its own switch and self-triggers. A solid print is ~41 g. |
| `PRINT_black_key_x7.stl` | 7 | |

---

## Not validated against hardware yet

These reflect the CAD as of the export date. `mx_cut` is still the datasheet
nominal, and two black-key dimensions (`mx_well_w`, `mx_shoulder_w`) are scaled
off a drawing rather than measured. See `../docs/BUILD.md` → "Open items".

Fine for quoting and for the coupon. **Not** to be run in quantity yet.
