// =====================================================================
// mx_switch.scad — a to-scale MX switch, and the fit checks that use it
// =====================================================================
// NOTHING HERE IS FABRICATED. This file exists so the switch can be put in
// the board and looked at, instead of the fit being argued from numbers.
//
// It earns its place: the black keycap's cross socket was modelled 3.8 mm
// ABOVE the stem's cross for several revisions. Every dimension involved was
// individually correct and the sanity checks all passed, because nothing in
// the project drew the switch. Dropping this model in makes it obvious in one
// render.
//
//   mode "switch"      the switch on its own
//   mode "white"       section through a white key position   <- the stop fit
//   mode "black"       section through a black key position   <- the socket fit
//   mode "fit_slice"   plan cut at the housing, both rotations side by side
//
// For a section, set mode then look at it from the front (Ctrl+5 / View >
// Front). `press` drives the stem down so travel can be checked, not just
// the rest position.
//
// SOURCE: Kailh CPG1511F01S04-1 "Red Shaft", doc KH-PS1706-10 rev B, section 5
// "Profile Dimensions" -> ../docs/datasheets/kailh_CPG1511F01S04-1_red.pdf
// Every figure below is read off that drawing EXCEPT the two marked MEASURED
// OFF THE DRAWING, which the datasheet does not dimension.
// =====================================================================

include <piano_params.scad>
use     <piano_keys.scad>
use     <piano_base_printed.scad>

$fn = 32;

// ---------------------------------------------------------------------
// The switch
// ---------------------------------------------------------------------
// Origin at the CENTRE OF THE PLATE HOLE, z = 0 at the PLATE TOP — the same
// datum the datasheet dimensions from. So it is placed with
//   translate([x, y, mx_plate_z]) mx_switch();
//
// rot = 0 puts the wide (mx_housing_w) axis along x; rot = 90 puts the narrow
// (mx_housing_d) axis along x. With stop_clear at 17.0 both now fit — at the
// old 15.0 only rot = 90 did, which is what this model was written to catch.
module mx_switch(press = 0, rot = 0) {
    shaft_h = mx_stem_h - mx_cross_h - mx_housing_h;   // 1.70 of bare stem
    rotate([0, 0, rot]) {
        // ---- fixed: housing, clips, pins ----
        color("#3F4756") {
            translate([0, 0, mx_housing_h/2])
                cube([mx_housing_w, mx_housing_d, mx_housing_h], center = true);
            translate([0, 0, -mx_lower_h/2])
                cube([mx_cut - 0.05, mx_cut - 0.05, mx_lower_h], center = true);
            // clips, at their widest — this is what the relief below the plate
            // has to clear, not the 13.95 body
            translate([0, 0, -mx_lower_h + 0.6])
                cube([mx_clip_w, mx_cut - 0.05, 1.2], center = true);
        }
        color("#8A8F98") for (s = [-1, 1])
            translate([s*3, 2, -mx_lower_h - mx_pin_h/2])
                cube([1, 0.4, mx_pin_h], center = true);
        // ---- moving: stem shoulder + cross ----
        color("#B4553F") translate([0, 0, -press]) {
            translate([0, 0, mx_housing_h + shaft_h/2])
                cube([mx_shoulder_w, mx_shoulder_w, shaft_h], center = true);
            for (r = [0, 90]) rotate([0, 0, r])
                translate([0, 0, mx_stem_h - mx_cross_h/2])
                    cube([mx_mount_cross - 0.2, mx_mount_th - 0.15, mx_cross_h],
                         center = true);
        }
    }
}

// ---------------------------------------------------------------------
// Checks
// ---------------------------------------------------------------------
mode    = "white";
press   = 0;      // 0 = at rest. Try mx_press for a white key at its stop,
                  // or blk_travel for a black key bottomed out.
sw_rot  = 0;
section = true;   // Cut away the NEAR half (y < 0). Leave this ON for the front
                  // view: the key lever's side skirts hang 6 mm below the cap
                  // and sit between the camera and everything worth looking at.
                  // Uncut, a pressed key shows a skirt crossing the stop
                  // shoulder, which reads as contact when the two are 12 mm
                  // apart in y and never touch.

// `plane` is the y the section is taken on — it has to follow the part being
// checked. A white key sits at y = 0, a black key at y = -pitch/2, and a cut
// fixed at 0 simply deletes the black key instead of sectioning it.
module cut(plane = 0) {
    if (section)
        difference() {
            children();
            translate([-60, plane - 90, -40]) cube([320, 90, 140]);
        }
    else children();
}

// A white key position: switch between the stop shoulders, plunger on the
// stem. What to look for: the housing clear of both shoulders, and the cap
// underside reaching the shoulder tops exactly as the plunger reaches mx_press.
//
// The key ROTATES about the pin, it does not drop — which is the whole reason
// the stops ground it early. `press` is the travel at the PLUNGER, so the
// angle comes from plunger_arm and every other point on the cap moves by its
// own radius. Set press = mx_press to see it land.
module check_white() {
    ang = asin(press / plunger_arm);
    base_cell(-1);
    color("#E8E8E8")
        translate([pivot_x, 0, pivot_z])
            rotate([0, -ang, 0])
                translate([-pivot_x, 0, -pivot_z]) key_lever(-1);
    translate([contact_x, 0, mx_plate_z]) mx_switch(press, sw_rot);
}

// A black key position. This one DOES travel straight down — no lever — so the
// cap moves with the stem. What to look for: the keycap's socket SWALLOWING
// the cross rather than perching on top of it, and the slim boss — not the
// full-width post — being the only thing near the housing at full travel.
// Set press = blk_travel for the bottomed-out case.
module check_black() {
    base_cell(0);
    color("#E8E8E8") key_lever(0);
    color("#111111") translate([0, -pitch/2, -press]) black_key();
    translate([blk_switch_x, -pitch/2, mx_plate_z]) mx_switch(press, sw_rot);
}

// Plan cut level with the housing, showing both rotations. Separate islands
// mean the switch drops in; one merged blob means it fouls the shoulders.
module check_fit_slice() {
    z_cut = (mx_plate_z + housing_top_z) / 2;
    for (i = [0, 1])
        translate([0, i * 60, 0])
            projection(cut = true) translate([0, 0, -z_cut]) {
                base_cell(-1);
                translate([contact_x, 0, mx_plate_z]) mx_switch(0, i * 90);
            }
}

if      (mode == "switch")    mx_switch(press, sw_rot);
else if (mode == "white")     cut(0)         check_white();
else if (mode == "black")     cut(-pitch/2)  check_black();
else if (mode == "fit_slice") check_fit_slice();
