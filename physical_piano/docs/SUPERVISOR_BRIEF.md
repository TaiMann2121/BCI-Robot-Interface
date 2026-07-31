# Physical Piano — Status & Decisions Needed

One-page summary of the physical 11-key piano that replaces the toy playmat in
the BCI arm/hand piano task. Full detail is in the accompanying Build Spec,
Parts to Purchase, and TechSpark Plan documents.

---

## Your three asks — done

| Ask | Status |
|-----|--------|
| **Add the black keys** | ✅ 7 black keys added, mirroring the simulator's exact proportions and positions. Decorative (no switches) as agreed. |
| **Links for materials to purchase** | ✅ Full list with links and prices → *Parts to Purchase* |
| **Plan for the machine shop** | ✅ Phased plan built from TechSpark's services page → *TechSpark Plan* |

## Design is complete — every dimension measured on the real rig

| Parameter | Value |
|-----------|-------|
| Keys | 11 white (4.5 × 14 cm) + 7 black, 5.0 cm pitch, 54.5 cm total |
| Switches | MX-style linear, 45 gf actuation |
| Sound | Arduino tones, tunable from a computer, saved to the board |
| Switch spec | Verified against the Kailh datasheet — travel, forces, and clearances all check out |
| Robot press force | 362 / 500 / 520 gf (index / middle / ring) |
| Finger contact point | 35 mm from key front edge — clear of the black keys ✅ |

Firmware and the computer-side tuning tool are already written. Nothing in the
design is now a guess.

---

## What I need from you

### 1. Budget approval
| Option | Cost |
|--------|-----:|
| All 3D printed | **~$450** |
| With a laser-cut base (see #2) | **~$295 + laser machine time** |

Electronics are only ~$100 of either. I'd like to order those **now** so I can
build and test the whole sound system on a breadboard while the mechanical parts
are still being made — the two halves are independent.

### 2. Laser-cut the base instead of 3D printing it?
I'd like to ask TechSpark about this. **The reason is accuracy, not cost.** The
keybed needs 11 switch holes at an exact 50 mm pitch, which is what the robot
arm is calibrated to. 3D printing means joining 3 separate tiles (the printers
are only 10″ wide), so the pitch has to survive two seams. Laser-cutting the
plate as one piece removes that risk entirely — and it's how these switches are
normally mounted.

I've drafted the layered version so both options are costed on the same basis.
On money it's a **modest** win, not a dramatic one: printed mass drops from
~490 g to ~275 g, but laser machine time is billed hourly and isn't published,
so the net saving is probably $40–90. I'll get a real number at the consult.

### 3. Funding account
TechSpark bills to a CMU oracle string. Which account should I use, and should I
place the material orders myself or send them to you?

### 4. Confirm the sound is what you pictured
You asked for electronic sound tunable on a computer, which is what I built: I
can set **each key's pitch** live over USB and save it. But the tone is always a
square-wave "beep" — the *timbre* can't be reshaped from the computer. If you
pictured adjusting the character of the sound (or wanted realistic piano
samples), that's a different setup and I'd rather find out now than after the
board is built.

---

## Two findings worth knowing

- **The arm needs to rise slightly.** The finished keyboard stands on 12 mm
  feet so the switch pins and wiring clear the desk, putting the key tops
  42.5 mm above the table. The fingers currently rest at 40 mm, so the arm
  goes up about 5–8 mm. Well within its adjustment range.
- **Keys must be printed at low infill — there's a hard limit.** The switch
  datasheet guarantees only 15 gf of return force, so a key must weigh under
  **24 g**. Ours is ~16 g at normal infill; printed near-solid it would be ~41 g
  and would sag onto its own switch and self-trigger. Cheaper too, since
  TechSpark bills by the gram.

## Next steps once approved

1. Book the TechSpark consult (Jen Hitchcock) — has lead time, so I'd start now
2. Order the electronics (~$100) and bench-test the sound
3. **Print one key and test it on the robot** before committing to all 11
4. Full print run → assemble → re-run the demo on the real keyboard
