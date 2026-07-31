# Physical Piano — Start Here

Building a real 11-key piano to replace the toy playmat in the BCI arm/hand
piano task.

**Status:** design complete and verified against both the physical rig and the
switch datasheet. Nothing has been bought or fabricated yet.

## Layout

```
docs/       specifications and plans (Markdown — the source of truth)
share/      the same docs as .docx, for the shared Drive folder
cad/        OpenSCAD models
firmware/   Arduino sketch
tuner/      computer-side tone tuning tool
tools/      scripts that generate share/*.docx from docs/*.md
```

### Documents

| File | What it's for |
|------|---------------|
| [docs/SUPERVISOR_BRIEF.md](docs/SUPERVISOR_BRIEF.md) | **One page + the 4 decisions needed** — for the supervisor meeting |
| [docs/BUILD.md](docs/BUILD.md) | The spec: dimensions, sound, measured forces, mechanism |
| [docs/PURCHASING.md](docs/PURCHASING.md) | What to buy, with links and budget (~$450) |
| [docs/TECHSPARK_PLAN.md](docs/TECHSPARK_PLAN.md) | Fabrication plan + **parts manifest** |
| [docs/datasheets/](docs/datasheets/) | Kailh switch datasheet — the source for every switch dimension |

### CAD — four files, split by role

| File | Contains | Used by |
|------|----------|---------|
| [cad/piano_params.scad](cad/piano_params.scad) | **Single source of truth.** Every shared dimension and all sanity checks. Edit *here*. | everything |
| [cad/piano_keys.scad](cad/piano_keys.scad) | Key levers + black keys — **printed in both routes** | both |
| [cad/piano_base_printed.scad](cad/piano_base_printed.scad) | All-printed base (cells, 3 tiles) | route A |
| [cad/piano_base_laser.scad](cad/piano_base_laser.scad) | Laser base (2 sheets + stop rail) + 12 printed brackets | route B |

> The two `base_*` files are **alternatives — build one, not both.** Either way
> you also need `piano_keys.scad`. Full breakdown in the TechSpark plan's parts
> manifest.

### Regenerating the .docx

```bash
node tools/md2docx.js docs/BUILD.md share/Physical_Piano_Build_Spec.docx
node tools/build_bom_docx.js          # the BOM, which has a custom layout
```

---

## What to do next, in order

### ① Right now (~1 hour, unblocks everything)

1. ~~Measure where the fingertips land on a key.~~ ✅ **35 mm from the front
   edge**, well inside the 53.2 mm clear zone — no black-key collision.
2. **Email TechSpark to book the consult** — Jen Hitchcock,
   jhitchco@andrew.cmu.edu. Lead time, so start early.
3. **Order the electronics** (~$100 — Arduino, MX switches, piezo, wire). They
   get bench-tested while the mechanical side is still in progress.

### ② Verify the CAD

4. Install [OpenSCAD](https://openscad.org) (free) and open each of the four
   `cad/*.scad` files. The console prints the derived geometry and will warn if
   anything is inconsistent. **Nothing has been rendered yet** — confirm the
   shapes look right before committing to fabrication.

### ③ TechSpark

5. Attend the consult — bring the questions in the TechSpark plan. The critical
   ones are laser bed size, 1.5 mm stock availability, and what laser time costs.
6. **Fabricate ONE key + base + black key and test it on the rig.** Do not batch
   11 until that passes.

### ④ Build

7. Full run: 11 keys, 7 black keys, and the base for whichever route was chosen.
8. Wire the switches, flash the firmware, tune the tones.
9. Raise the arm ~5–8 mm so resting fingertips hover 2–5 mm above the key tops.
10. Re-run the demo sequence to validate.

---

## Two tracks run in parallel

- **Electronics** — breadboard the Arduino, switches and piezo; test the
  firmware and tuner with no mechanical parts at all.
- **Mechanical** — the slow track, gated by the TechSpark consult.

Start the electronics early so that half is proven before any key exists.
