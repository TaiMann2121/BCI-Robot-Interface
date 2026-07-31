# Physical Piano — Parts to Purchase

Shopping list for the 11-key physical piano. Quantities assume **11 white keys
+ 7 decorative black keys**, one switch per white key, spares included.

Prices are approximate and are there for budgeting — confirm
at checkout. Links point to reputable distributors; equivalents are fine.

---

## 1. Key switches

### ✅ CHOSEN: mechanical keyboard switches (MX-style linear)

*Decided. The CAD has been converted to a 14 × 14 mm MX plate mount, and the
separate return springs have been removed from the design.*

An MX-style linear switch bundles **switch + return spring + 4 mm travel +
keycap mount** into one part. That removes the separate return spring, the
spring seats, and most of the travel-tuning from the build. Actuation ~45–60 gf
is far below our weakest finger (362 gf), so every finger triggers it reliably.

| Qty | Item | ~Price | Link |
|----:|------|-------:|------|
| 2 packs (20 pcs, 9 spare) | Kailh linear red switches, 10-pack (MX-compatible) | ~$6/pack | [Adafruit #4952](https://www.adafruit.com/product/4952) |
| — | *or* Cherry MX Red 45 g linear, 10-pack | ~$12/pack | [Amazon MX1A-L1NN](https://www.amazon.com/Original-Cherry-Switches-Mechanical-Keyboard/dp/B09J3GSY6Y) · [MechanicalKeyboards.com](https://mechanicalkeyboards.com/products/cherry-mx-red-45g-linear) |

### ~~Option B: snap-action micro switches~~ (not chosen — kept for reference)

Would need a separate return spring per key.

| Qty | Item | ~Price | Link |
|----:|------|-------:|------|
| 14 (11 + 3 spare) | Omron **D2F-01F** ultra-subminiature, low operating force (~0.98 N), 0.1 A — plenty for logic-level switching | ~$2 ea | [DigiKey D2F-01F](https://www.digikey.com/en/products/detail/omron-electronics-inc-emc-div/D2F-01F/83266) |
| — | *alt* Omron D2F-01 (standard force) | ~$1.50 ea | [DigiKey D2F-01](https://www.digikey.com/en/products/detail/omron-electronics-inc-emc-div/D2F-01/83260) |
| 1 assortment | Small compression springs (~8 mm OD, light force) for key return | ~$20 | [McMaster compression spring assortments](https://www.mcmaster.com/products/compression-spring-assortments/) |

Datasheet (confirm operating force before ordering):
[Omron D2F series PDF](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf)

---

## 2. Microcontroller & sound

| Qty | Item | ~Price | Link |
|----:|------|-------:|------|
| 1 | Arduino Uno R3 (official) | ~$28 | [Arduino Store](https://store-usa.arduino.cc/products/arduino-uno-rev3) · [SparkFun](https://www.sparkfun.com/arduino-uno-r3.html) |
| — | *or* budget-compatible Uno R3 clone (works identically) | ~$13 | [ELEGOO UNO R3](https://us.elegoo.com/products/elegoo-uno-r3-board) |
| 1 | Piezo buzzer (drives straight off `tone()`, no amp needed) | ~$2 | [Adafruit PS1240 #160](https://www.adafruit.com/product/160) |
| 1 *(optional, louder)* | Large enclosed piezo element w/ wires | ~$3 | [Adafruit #1739](https://www.adafruit.com/product/1739) |

Reference for wiring/driving the piezo:
[Adafruit — Using Piezo Buzzers with Arduino](https://learn.adafruit.com/using-piezo-buzzers-with-circuitpython-arduino)

---

## 3. Wiring & assembly

Wire the 11 switches in two stages: a **breadboard** to bring up and test the
firmware/tuner before any key exists (no soldering, fully reversible), then a
**soldered perfboard** for the permanent build. Solder is worth the extra step
here — the keys get struck repeatedly at 362–520 gf, and a breadboard's
friction-fit connections can work loose under that kind of repeated shock,
which is not a failure mode you want mid-session. *If you'd rather not solder*,
the no-solder screw-terminal option below is a durable middle ground.

| Qty | Item | ~Price | Link |
|----:|------|-------:|------|
| 1 | Full-size solderless breadboard | ~$5 | [Adafruit #239](https://www.adafruit.com/product/239) — bring-up/testing only |
| 1 | USB A–B cable (Uno) | ~$6 | [Adafruit #62](https://www.adafruit.com/product/62) · [Arduino Store](https://store-usa.arduino.cc/products/usb-2-0-cable-type-a-b) — likely already in lab stock |
| 1 | Hookup wire, 22 AWG stranded, 6 colors | ~$15 | [Adafruit #3111](https://www.adafruit.com/product/3111) · [SparkFun](https://www.sparkfun.com/hook-up-wire-assortment-stranded-22-awg.html) |
| 1 | Perfboard / prototyping board | ~$11 | [Adafruit #1606](https://www.adafruit.com/product/1606) — final build |
| 1 | Beginner soldering iron kit (iron, stand, solder, sucker, wick) | ~$20 | [Amazon — LCDalternatives kit](https://www.amazon.com/Beginner-Soldering-LCDalternatives-v3-solder/dp/B00SH2MOB6) |
| 1 pack | K&S 3 mm brass rod, 3-pack (300 mm each) — hinge pin | ~$8 | [Amazon](https://www.amazon.com/Round-Brass-Rod-Diameter-Engineering/dp/B013Y2EACO) — the laser route uses one continuous ~570 mm pin, so butt two rods at a bracket |
| 1 | M3 nut/bolt/washer assortment kit | ~$12 | [Amazon](https://www.amazon.com/Assortment-Stainless-Washers-Assorted-Machine/dp/B0BC24J6SS) |
| 6 | M3 standoffs, 12 mm — lift the board so switch pins and wiring clear the desk | ~$9 | [Amazon](https://www.amazon.com/Hilitchi-Female-Standoff-Assortment-Motherboard/dp/B01LZ6PXCY) |
| 1 | Gorilla super glue (cyanoacrylate) | ~$7 | [Amazon](https://www.amazon.com/Gorilla-Super-Glue-Gram-Clear/dp/B00KPYB05A) — gluing black keys into locating grooves |

**No-solder alternative** — skip the perfboard + soldering kit above and use
this instead:

| Qty | Item | ~Price | Link |
|----:|------|-------:|------|
| 1 | Screw-terminal shield for Arduino Uno | ~$15 | [Amazon](https://www.amazon.com/Screw-Terminal-Shield-Arduino-Uno/dp/B0F5NVVY1Q) |

Each wire clamps under a screw instead of being soldered — less permanent than
solder, but far more robust than a bare breadboard, with no tools to learn.

---

## 4. 3D printing (via CMU TechSpark — not a purchase, a billed service)

See [TECHSPARK_PLAN.md](TECHSPARK_PLAN.md) for the full process.

**Rough material estimate** (PLA, from part volumes — the slicer at TechSpark
gives the real number):

| Part | Qty | ~Mass each | ~Total |
|------|----:|-----------:|-------:|
| White key lever | 11 | ~16 g | ~175 g |
| Base cell | 11 | ~23 g | ~255 g |
| Black key | 7 | ~9 g | ~65 g |
| | | **Total** | **~490 g** |

At PLA **$0.64/g** → **~$315**.

On the laser route the printed base cells are replaced by **12 small hinge
brackets** (~3 g each), so printing drops to ~275 g → **~$176**, plus the laser
sheets and machine time.

> 💡 **Laser-cut base — worth discussing, mainly for accuracy.** TechSpark also
> offers **laser cutting**. Re-authoring the base as flat layers (see
> [`../cad/piano_base_laser.scad`](../cad/piano_base_laser.scad)) cuts all 11 switch
> holes in **one operation on one sheet**, so the 50 mm pitch the arm is
> calibrated to has no tile seams to drift across. The printed base has to be
> split into 3 tiles for a 254 mm bed.
>
> On cost, be realistic: printed mass drops from ~490 g to ~275 g (**$315 →
> ~$176**), but laser time is billed hourly and is not quoted on the services
> page, so the net saving is more like **$40–90, not half**. Treat the pitch
> accuracy as the reason and the cost as a bonus.

---

## Budget summary

| Category | Estimate |
|----------|---------:|
| Switches | ~$12 |
| Arduino + sound | ~$30 |
| Wiring & assembly — solder path (breadboard + perfboard + soldering kit) | ~$93 |
| *or* wiring & assembly — no-solder path (breadboard + screw-terminal shield) | *~$77* |
| **Parts subtotal — solder path** | **~$135** |
| *Parts subtotal — no-solder path* | *~$119* |
| Fabrication — all 3D printed | ~$315 |
| Fabrication — laser-cut base + printed keys | ~$176 print + laser time |
| **Grand total — solder path + all-printed** | **~$450** |
| *Grand total — no-solder path + laser-cut* | *~$295 + laser time* |

The soldering kit (~$20) is a one-time purchase — skip it on the no-solder path,
or keep it if the lab wants one on hand for future builds.

**Suggested first purchase:** buy the electronics now (~$100) so the firmware and
tuner can be bench-tested on a breadboard while the mechanical parts are still
being printed. The two tracks are independent.
