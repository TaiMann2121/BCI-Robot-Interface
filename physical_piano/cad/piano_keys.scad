// =====================================================================
// piano_keys.scad — the moving parts, PRINTED IN BOTH ROUTES
// =====================================================================
// Everything in this file is 3D printed and is needed whichever base you
// build. Nothing here is laser-cut.
//
//   mode "key"    key lever  x11
//   mode "black"  black key  x7
//
// The base comes from ONE of:
//   piano_base_printed.scad   all-printed route
//   piano_base_laser.scad     laser-cut route
//
// Shared dimensions live in piano_params.scad — edit them there.
// See ../TECHSPARK_PLAN.md for the full parts manifest.
//
// MECHANISM (side view, front = left):
//
//        finger presses here (contact_x)
//                |
//   ___________  v  ______________________ () <- rear pin hinge
//  |  key cap (lever, pivots at rear)      |
//  |______________________________________|
//                |plunger|
//                v
//             [MX switch] <- its own spring holds the key up and returns it
//  ============= base ====================
//
// The key RESTS on the switch stem. The finger drives the cap down; the stem
// actuates, and shortly after the cap lands on the base's stop shoulders.
// Those shoulders — not the switch — absorb the 362-520 gf overshoot.
// There is NO separate return spring and no up-stop: the MX spring does both.
//
// COORDINATES: x along the key (0 = front, +x = rear/hinge); y across the
// width (0 = centre); z up (0 = board underside).
// =====================================================================

include <piano_params.scad>

$fn = 48;

// =====================================================================
// Key lever (the moving key cap). Printing it upside-down is easiest.
// =====================================================================
module key_lever() {
    union() {
        // top plate
        translate([0, -key_w/2, under_rest]) cube([key_len, key_w, cap_th]);
        // side rails (cosmetic skirts) — INSIDE the key width so they clear
        // the hinge posts and the neighbouring key
        for (s = [-1, 1])
            translate([0, (s > 0) ? (key_w/2 - side_rail) : -key_w/2, under_rest - 6])
                cube([key_len, side_rail, 6 + 0.1]);
        // rear hinge knuckle, centred in y, pin axis along Y
        translate([pivot_x, 0, pivot_z]) knuckle();
        // plunger at contact_x: presses the MX stem (no spring — MX returns it)
        translate([contact_x, 0, 0]) plunger();
    }
}

// Hinge knuckle. Origin is the PIN CENTRE, so it is called with
// translate([pivot_x, 0, pivot_z]). A bar lying along Y with the pin bore
// through it, merging into the cap above. It does NOT reach down to the base —
// the key has to swing freely. Its width (knuckle_wid) is what stops the key
// sliding sideways along the pin.
module knuckle() {
    difference() {
        translate([0, -knuckle_wid/2, 0])
            rotate([-90, 0, 0]) cylinder(h = knuckle_wid, d = knuckle_boss_d);
        translate([0, -knuckle_wid/2 - 1, 0])
            rotate([-90, 0, 0]) cylinder(h = knuckle_wid + 2, d = pin_d);
    }
}

module plunger() {
    // Stubby post hanging from the cap underside that pushes the MX stem down.
    // It passes between the base's stop shoulders; the CAP UNDERSIDE is what
    // lands on them, so the switch never takes the overshoot.
    tip_d = 4;
    translate([0, 0, under_rest - plunger_len])
        cylinder(h = plunger_len, d = tip_d);
}

// =====================================================================
// Black key (decorative riser, no switch). Sits at a white-key boundary:
// a thin web drops into the base's slot/groove and is glued; the cap
// overhangs both neighbouring white keys, black_rise above their tops.
// White keys only travel DOWN, so the overhang never collides.
// Print flat on its side for strength along the web.
// =====================================================================
module black_key() {
    web_top = black_top_z - blk_cap_th;
    union() {
        // web / stem (also the glue tab, reaching down into the groove)
        translate([blk_web_x0, -black_stem_w/2, base_th - blk_groove_d])
            cube([blk_web_x1 - blk_web_x0, black_stem_w,
                  web_top - (base_th - blk_groove_d)]);
        // cap
        translate([key_len - black_len, -black_w/2, web_top])
            cube([black_len, black_w, blk_cap_th]);
    }
}

// =====================================================================
// Render selector
// =====================================================================
// "key"    one key lever   (print 11)
// "black"  one black key   (print 7)
// "pair"   both together, to check the black key clears the white key
mode = "pair";

if      (mode == "key")   key_lever();
else if (mode == "black") black_key();
else if (mode == "pair") {
    color("white") key_lever();
    color("black") translate([0, pitch/2, 0]) black_key();
}
