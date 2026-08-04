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
        //
        // WHICH SIDE: both base files lay key 0 out at HIGH y and count DOWN
        // (slot_y() and key_y() both DECREASE with the index), so key idx+1 is
        // the -y neighbour of key idx. is_black(idx) is the boundary between
        // idx and idx+1, which therefore sits at -y; is_black(idx-1) sits at
        // +y. These were swapped: the result was a notch cut at every boundary
        // WITHOUT a black key, while the real black-key boundaries got only a
        // one-sided 7.5 mm notch instead of the full 15 mm the switch needs.
        if (is_black(idx))     notch(-1);
        if (is_black(idx - 1)) notch( 1);
        // Cut LAST and at this level, so it passes through the rails and cap
        // as well as the knuckle — see pin_bore().
        pin_bore();
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
    translate([0, -knuckle_wid/2, 0])
        rotate([-90, 0, 0]) cylinder(h = knuckle_wid, d = knuckle_boss_d);
}

// The hinge pin bore. Subtracted at the KEY_LEVER level, NOT inside knuckle().
//
// The side rails run the full length of the key and stand exactly where this
// bore has to come out. Cut inside knuckle(), the bore was drilled before the
// rails were unioned on, so the rails plugged both ends: a blind 39 mm pocket
// across a 45 mm key, sealed by 3 mm of rail at each side. The pin rod could
// not be threaded through the key at all, and the lever rendered as two
// volumes — a solid plus a sealed internal cavity — instead of one.
//
// Cutting it here takes it through the rails and the cap as well. It leaves
// 2.3 mm of cap over the bore and 4.3 mm of rail under it.
module pin_bore() {
    translate([pivot_x, -key_w/2 - 1, pivot_z])
        rotate([-90, 0, 0]) cylinder(h = key_w + 2, d = pin_d);
}

module plunger() {
    // Stubby post hanging from the cap underside that pushes the MX stem down.
    // It passes between the base's stop shoulders; the CAP UNDERSIDE is what
    // lands on them, so the switch never takes the overshoot.
    //
    // The +0.1 buries it in the cap. Without it the plunger's top face and the
    // cap's underside are the same plane, and a face-to-face contact is not a
    // union: CGAL reports the lever as TWO volumes and the plunger slices as a
    // loose cylinder. The side rails above already do this; the plunger did
    // not. Only the tip position matters dimensionally, and that is unchanged.
    tip_d = 4;
    translate([0, 0, under_rest - plunger_len])
        cylinder(h = plunger_len + 0.1, d = tip_d);
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
// The post is STEPPED, and both steps are load-bearing decisions:
//
//   blk_socket_z .. blk_step_z   a slim round boss (blk_boss_w) that follows
//                                the stem down INTO the housing opening, the
//                                way a real keycap's does
//   blk_step_z   .. cap_under    the full-width post
//
// It starts at blk_socket_z — the BASE of the cross, not the top of the stem.
// This post used to start at stem_top_z with the socket cut upwards from
// there, which put the whole 3.80 mm cross below the socket: the cap sat on
// the tip of the stem with nothing gripping it. See piano_params.scad.
module black_key() {
    cap_under = black_top_z - blk_cap_th;
    post_w    = mx_mount_cross + 2.4;      // socket plus wall
    difference() {
        union() {
            // cap
            translate([key_len - black_len, -black_w/2, cap_under])
                cube([black_len, black_w, blk_cap_th]);
            // slim lower boss — round so it cannot catch on the corners of the
            // housing opening, and so it prints without a seam on the socket
            translate([blk_switch_x, 0, blk_socket_z])
                cylinder(h = blk_step_z - blk_socket_z, d = blk_boss_w);
            // full-width post, from clear of the housing up to the cap
            translate([blk_switch_x - post_w/2, -post_w/2, blk_step_z])
                cube([post_w, post_w, cap_under - blk_step_z + 0.1]);
        }
        // MX cross socket, opening at the post's bottom face. Cut deeper than
        // mx_cross_h so the cap seats on the stem SHOULDER (a 6.6 mm face)
        // rather than bottoming on the tip of the cross.
        translate([blk_switch_x, 0, blk_socket_z - 0.1]) mx_mount();
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
    // Key 0, which has a black key on its -y side (is_black(0) is true), so
    // the lever is rendered NOTCHED. It used to pair an un-notched key_lever()
    // with a black key on the +y side — the one combination that never occurs
    // on the board, and one where the black key's post drives straight through
    // the white key. F6 gave it away: the two parts fused into a single volume.
    color("white") key_lever(0);
    color("black") translate([0, -pitch/2, 0]) black_key();
}
