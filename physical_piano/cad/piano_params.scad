// =====================================================================
// piano_params.scad — SINGLE SOURCE OF TRUTH for the physical piano
// =====================================================================
// Both fabrication routes include this file:
//   piano_keys.scad         key levers + black keys (printed in BOTH routes)
//   piano_base_printed.scad all-printed base   \  pick ONE
//   piano_base_laser.scad   laser-cut base     /
//
// Every dimension the two routes must agree on lives HERE and nowhere else.
// This is not housekeeping: pivot_z was previously defined in both files and
// silently drifted to 26.5 in one and 28 in the other, which would have put
// the laser route's hinge pin 1.5 mm too high.
//
// Values marked MEASURED were taken off the physical rig. Do not change them
// without re-measuring.
// =====================================================================

// ---------------- Key layout (MEASURED) ----------------
key_w     = 45;      // key width  (mm)
key_len   = 140;     // key length (mm)
key_gap   = 5;       // gap between keys
pitch     = key_w + key_gap;    // 50 mm — what the arm is calibrated to
cap_th    = 4;       // key cap thickness
side_rail = 3;       // cosmetic side skirt

// Fingertip contact point, MEASURED at 35 mm from the key's front edge.
contact_x = 35;

// ---------------- Base / pivot ----------------
base_th   = 6;       // printed base plate thickness
// Set so stop_top lands at 23.5 (= the laser stack's 9 + 1.5 + 13 mm), giving
// the 2.7 mm press below. Adjust THIS rather than the stop rail's stock size.
hinge_h   = 20.2;    // pivot height above the base top
pin_d     = 3.4;     // hinge pin bore (3 mm rod)
pivot_x   = key_len - 13;
clr       = 0.4;     // print clearance for moving mates

// Knuckle must nearly fill the span between hinge supports or nothing stops
// the key sliding along the pin (see the note in piano_keys.scad).
knuckle_wid    = 45;
knuckle_boss_d = 9;
post_w         = 2;  // hinge post thickness — must fit the 5 mm inter-key gap
post_len       = 9;

// ---------------- MX switch ----------------
// ALL VALUES BELOW ARE FROM THE DATASHEET, not estimated:
//   Kailh CPG1511F01S04-1 "Red Shaft", doc KH-PS1706-10 rev B
//   -> ../docs/datasheets/kailh_CPG1511F01S04-1_red.pdf
// Where the datasheet gives a tolerance, the WORST CASE is used for checks.
mx_cut       = 14.0;   // plate cutout. Body through plate is 13.95 +/-0.05,
                       // so 14.0 is the correct hole — never cut it undersize.
mx_plate_th  = 1.5;    // thickness the clips grip — mandatory
mx_travel    = 3.6;    // TT total travel, +/-0.3  -> worst case MIN 3.3
mx_travel_tol = 0.3;
mx_actuate   = 1.8;    // PT actuation travel, +/-0.3 -> worst case MAX 2.1
mx_actuate_tol = 0.3;
mx_stem_h    = 11.20;  // stem top above the mounting plate (datasheet profile)
mx_housing_w = 15.60;  // top flange, sits ON the plate — stop rail must clear it
mx_riser_h   = 4.5;    // plate top height above the base plate top
mx_below_plate = 6.4;  // 5.00 lower housing + 1.40 pins, below the plate

// ---------------- Motion ----------------
rest_gap  = 0;     // key RESTS on the stem; a gap is physically impossible
// Chosen as the midpoint between the worst-case actuation depth (2.1) and the
// worst-case bottom-out depth (3.3), so it has 0.6 mm of margin either way.
mx_press  = 2.7;

// ---------------- Self-actuation figures ----------------
key_mass_g    = 16;   // printed key lever, ~20% infill
// RF (return force) is specified as a MINIMUM of 15 gf. The datasheet gives no
// preload figure, so 15 gf is the only guaranteed force holding the key up —
// design against it, not against a typical value.
mx_preload_gf = 15;
mx_act_gf     = 45;   // OF operating force, 45 +/-10 gf
com_arm       = 57;   // key centre of mass from the pivot

// ---------------- Black keys (mirrors the simulator) ----------------
black_idx    = [0, 2, 3, 5, 6, 7, 9];
black_w      = key_w   * 0.58;   // 26.1
black_len    = key_len * 0.62;   // 86.8, occupies the REAR
black_rise   = 10;
black_stem_w = 3.6;
blk_cap_th   = 5;
blk_web_x0   = 62;
blk_web_x1   = 120;   // stops short of the hinge posts
blk_groove_d = 3;
front_clear  = key_len - black_len;   // 53.2 — fingers must contact inside this

// ---------------- Derived heights — DO NOT hardcode these anywhere ----
mx_plate_z  = base_th + mx_riser_h;                 // 10.5 switch plate top
stem_top_z  = mx_plate_z + mx_stem_h;               // 21.7 stem top at rest
pivot_z     = base_th + hinge_h;                    // 26.2 hinge axis
under_rest  = pivot_z;                              //      cap underside
throw       = rest_gap + mx_press;                  //  2.7 cap travel to stop
stop_top    = pivot_z - throw;                      // 23.5 bottom stop height
plunger_len = pivot_z - (stem_top_z + rest_gap);    //  4.5
key_top_z   = pivot_z + cap_th;                     // 30.2 above the board
black_top_z = key_top_z + black_rise;               // 40.2

foot_h      = 12;    // standoff height under the board (wiring space)

// ---------------- Worst-case switch travel (datasheet tolerances) -----
travel_min   = mx_travel  - mx_travel_tol;    // 3.3 — earliest bottom-out
actuate_max  = mx_actuate + mx_actuate_tol;   // 2.1 — latest actuation

// ---------------- Lever arms and the self-actuation limit -------------
plunger_arm  = pivot_x - contact_x;                 // 92 mm
static_gf    = key_mass_g * com_arm / plunger_arm;  // key weight felt at the stem
max_key_g    = mx_preload_gf * plunger_arm / com_arm;  // heaviest safe key

// =====================================================================
// Sanity checks — these run for EVERY file that includes this one, so a
// bad edit is caught no matter which route you happen to have open.
// =====================================================================
echo(str("plate top ", mx_plate_z, " | stem top ", stem_top_z, " | pivot ", pivot_z,
         " | stop ", stop_top, " | plunger ", plunger_len, " | key top ", key_top_z));
echo(str("key top above TABLE = ", key_top_z + foot_h, " mm (on ", foot_h, " mm feet)"));
echo(str("press ", mx_press, " mm: actuates by ", actuate_max,
         " (margin ", mx_press - actuate_max, "), bottoms at ", travel_min,
         " (margin ", travel_min - mx_press, ")"));
echo(str("key ", key_mass_g, " g -> ", static_gf, " gf at stem; limit is ",
         mx_preload_gf, " gf, i.e. a key under ", max_key_g, " g"));

if (plunger_len < 2)
    echo("*** WARNING: plunger_len too short — raise hinge_h ***");
if (mx_press >= travel_min)
    echo("*** WARNING: press exceeds the worst-case travel — the SWITCH would ",
         "take the finger overshoot instead of the stops. Reduce mx_press. ***");
if (mx_press <= actuate_max)
    echo("*** WARNING: press may not reach actuation on a worst-case switch ***");
if (static_gf >= mx_preload_gf)
    echo("*** WARNING: the key outweighs the switch's guaranteed return force — ",
         "it will sag onto the stem and self-trigger. Keep the key under ",
         max_key_g, " g (print at low infill). ***");
if (contact_x >= front_clear)
    echo("*** WARNING: contact_x is inside the BLACK KEY zone — the fingertip ",
         "will collide with a black key. Keep it below ", front_clear, " mm ***");
