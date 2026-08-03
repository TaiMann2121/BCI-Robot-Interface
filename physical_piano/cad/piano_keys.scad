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
// `idx` is the white-key index 0..10. It decides which sides get notched to
// clear the neighbouring black keys' switches. Pass -1 for an un-notched key.
module key_lever(idx = -1) {
    difference() {
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
        // Notch the rear of the key wherever a black key sits beside it, so its
        // switch has room. Real piano white keys are shaped the same way, and
        // for the same reason. The notch stops at blk_notch_x1 so the hinge
        // knuckle keeps its full width.
        if (is_black(idx))     notch( 1);
        if (is_black(idx - 1)) notch(-1);
    }
}

module notch(side) {
    y0 = (side > 0) ? (key_w/2 - blk_notch) : -(key_w/2);
    translate([blk_notch_x0, y0, under_rest - 8])
        cube([blk_notch_x1 - blk_notch_x0, blk_notch, cap_th + 10]);
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
// A SWITCHED black key: a keycap on a post that pushes straight onto an MX
// stem, exactly like a keyboard keycap. No hinge, no glue, no return spring —
// the switch supplies the travel and the spring.
//
// It travels straight down while the white keys pivot. Slightly different feel,
// but the black keys are never pressed by the robot, and a lever here would
// collide with the hinge brackets that share the same 5 mm gap.
module black_key() {
    cap_under = black_top_z - blk_cap_th;
    post_w    = mx_mount_cross + 2.4;      // socket plus wall
    difference() {
        union() {
            // cap
            translate([key_len - black_len, -black_w/2, cap_under])
                cube([black_len, black_w, blk_cap_th]);
            // post down to the switch stem, centred on blk_switch_x
            translate([blk_switch_x - post_w/2, -post_w/2, stem_top_z])
                cube([post_w, post_w, cap_under - stem_top_z + 0.1]);
        }
        // MX cross socket in the underside of the post
        translate([blk_switch_x, 0, stem_top_z - 0.1]) mx_mount();
    }
}

// The + shaped recess an MX stem plugs into.
module mx_mount() {
    for (r = [0, 90])
        rotate([0, 0, r])
            translate([-mx_mount_cross/2, -mx_mount_th/2, 0])
                cube([mx_mount_cross, mx_mount_th, mx_mount_depth + 0.1]);
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
