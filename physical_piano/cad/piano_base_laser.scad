// =====================================================================
// piano_base_laser.scad — the LASER ROUTE for the keybed base
// =====================================================================
// >>> THIS FILE IS NOT ALL LASER-CUT, AND IT IS NOT THE WHOLE BOARD. <<<
//
// It is named for the ROUTE, not the process. What is in here:
//
//   mode "2d_struct"        LASER  9.0 mm sheet   x1
//   mode "2d_switch_plate"  LASER  1.5 mm sheet   x1
//   mode "2d_stop_rail"     LASER 13.0 mm sheet   x1
//   mode "hinge_block"      PRINT  small bracket  x12   <-- printed, not lasered
//
// And what is NOT in here, but is still needed to build this route:
//
//   key lever   x11   -> piano_keys.scad, mode "key"     (printed)
//   black key   x7    -> piano_keys.scad, mode "black"   (printed)
//   3 mm pin rod ~570 mm, and 6 x 12 mm standoffs        (bought)
//
// So the laser route = 3 laser parts + 30 printed parts across TWO files.
// piano_base_printed.scad is the OTHER route — do not build both.
// See ../TECHSPARK_PLAN.md for the full parts manifest.
//
// WHY: all 11 switch positions get cut in ONE operation on ONE sheet, so the
// 50 mm pitch the arm is calibrated to has no tile seams to drift across.
// (The printed base must be split into 3 tiles for a 254 mm print bed.)
//
// LAYER STACK (z measured from the board's underside):
//
//   z=23.5 ┌──────────────┐  stop rail    13.0 mm  <- key cap lands HERE
//   z=10.5 ├──────────────┤  switch plate  1.5 mm  <- MX clips into 14 mm hole
//   z=9.0  ├──────────────┤  structure     9.0 mm  <- feet, brackets, bolting
//   z=0    └──────────────┘  board underside (on 12 mm standoffs)
//
// Only TWO sheets: an earlier version had a third "spacer" layer, but once the
// structural layer was drilled through under every switch the spacer had no
// remaining job and was removed.
//
// The thicknesses are chosen so the switch plate top lands at mx_plate_z and
// the stop rail top at stop_top — both defined in piano_params.scad — so this
// route and the printed route are geometrically interchangeable.
//
// EXPORT: set mode to a "2d_*" value, press F6, then File > Export > Export as
// DXF (or SVG). Each 2D profile is a flat cut path. The 3D modes are for
// visual checking only.
// =====================================================================

include <piano_params.scad>
use     <piano_keys.scad>      // key_lever() / black_key() for previews

$fn = 48;

// Side margin so the OUTERMOST hinge brackets land on material. Without it the
// boundary positions at each end fall exactly on the board edge (or past it).
margin_side = 10;
board_w   = n_keys * pitch - key_gap + 2 * margin_side;   // 545 + 20 = 565 mm

// ---------------- Layer thicknesses (set the critical heights) ----------
// Only TWO layers below the stop rail. An earlier version had a separate
// "spacer" to clear the switch body, but once the structural layer was drilled
// through under every switch it did the same job — so the spacer was doing
// nothing and has been merged away.
t_struct  = 9.0;    // structure, feet, all bolting. Standard stock, stiff over
                    // 565 mm, and far easier to laser than 12 mm.
t_plate   = 1.5;    // MX switches CLIP into 1.5 mm — mandatory, cannot be thicker
t_stop    = 13.0;

// ---------------- Derived heights ----------
z_plate   = t_struct;
z_plate_t = z_plate + t_plate;
z_stop_t  = z_plate_t + t_stop;

echo(str("switch plate top z = ", z_plate_t, "  (shared mx_plate_z = ", mx_plate_z, ")"));
echo(str("stop rail top z    = ", z_stop_t,  "  (shared stop_top   = ", stop_top, ")"));
echo(str("below-plate clearance = ", t_struct, " mm in-board (need ", mx_below_plate,
         "), plus ", foot_h, " mm of open air under the feet"));
echo(str("KEY TOP above the TABLE = ", key_top_z + foot_h,
         " mm — the feet raise everything, so raise the arm to match"));

// These compare the laser stack against the SHARED values, so the two routes
// can never silently drift apart again.
if (z_plate_t != mx_plate_z)
    echo("*** WARNING: laser stack puts the switch plate at ", z_plate_t,
         " but piano_params.scad says ", mx_plate_z, " — adjust t_struct/t_plate ***");
if (z_stop_t != stop_top)
    echo("*** WARNING: laser stop rail top is ", z_stop_t,
         " but piano_params.scad says ", stop_top, " — adjust t_stop ***");
if (t_struct < mx_below_plate)
    echo("*** NOTE: switch pins reach past the board underside — fine, the feet ",
         "give clearance, but keep foot_h above ", mx_below_plate - t_struct, " mm ***");

// ---------------- Board footprint ----------------
margin_front = 12;        // material ahead of the key front edge
margin_rear  = 22;        // material behind the pivot, carries hinge blocks
board_l      = key_len + margin_front + margin_rear;   // 174 mm

// ---------------- Feature sizes ----------------
sw_clear   = 17.0;        // clearance hole for the switch BODY below the plate
// stop_clear MOVED to piano_params.scad. The printed route's stop shoulders
// need exactly the same number, and a second copy here is precisely how
// pivot_z drifted between the two routes once before. The hole stays square,
// not round: a round hole would have to be 22 mm across to pass the housing's
// diagonal, which would leave the rail far too thin.
bolt_d     = 3.4;         // M3 clearance

// Stop rail runs ACROSS all keys at the contact point. The key cap lands on
// its top face; the plunger passes through stop_clear to reach the stem.
//
// The rail is exactly as wide as the printed route's shoulders — the clearance
// hole plus stop_width either side — so BOTH routes bind at the same radius
// from the pivot (stop_r_lead) and give the same press. It used to run to
// contact_x +/- 15, reaching 2.5 mm further forward than the printed shoulders
// and grounding the key earlier still.
stop_x0    = contact_x - (stop_clear/2 + stop_width);
stop_x1    = contact_x + (stop_clear/2 + stop_width);

hinge_post_len = 9;             // bracket length along x
hinge_post_w   = 4;             // bracket thickness — must fit the 5 mm gap
// Both bracket bolts sit BEHIND the pivot. A forward bolt would land at
// x ~118, inside the black key web's 62-120 span, and the web shares this gap.
hinge_bolt_x1  = pivot_x + 7;
hinge_bolt_x2  = pivot_x + 17;

// Black key webs drop through slots cut at the black boundaries. The POSITIONS
// come from black_idx in piano_params.scad — this file must never keep its own
// copy of that list, or the two can drift the way pivot_z once did.

// Hinge brackets sit ON THE BOUNDARIES between keys (in the 5 mm gaps), not
// under the keys — a bracket under a key would foul the cap. One bracket per
// boundary, including the two outer edges, so 12 across the board. They all
// carry ONE continuous pin rod, which also guarantees every pivot is collinear.
n_hinge = n_keys + 1;
// Negated to match key_y above — boundary_y(b+1) stays the midpoint between
// key b and key b+1 either way.
function boundary_y(j) = -(j - n_keys / 2) * pitch;   // j = 0 .. n_keys

// Key centre y for key index i, board centred on y=0.
// NEGATED so key 0 lands at HIGH y = the viewer's LEFT, matching the simulator.
// See the orientation note at the top of piano_params.scad.
function key_y(i) = -(i - (n_keys - 1) / 2) * pitch;
// x is measured from the key's FRONT edge; board local x adds the margin
function bx(x) = x + margin_front;

// =====================================================================
// 2D LAYER PROFILES  (export these to DXF)
// =====================================================================

// Board outline with a corner notch at the KEY 0 end. Cut into every layer, so
// the assembled board carries a permanent "this end is key 0" mark. Without it
// the board is near enough symmetric that a mirrored view (or flipping it on
// the bench) silently reverses the key order.
module outline() {
    difference() {
        square([board_l, board_w], center = false);
        // Notch at the FRONT edge, KEY 0 end. Key 0 is at high y (viewer's
        // left), so the notch goes in the far-y front corner.
        polygon([[0, board_w], [mark_size, board_w], [0, board_w - mark_size]]);
    }
}

// Bolt pattern shared by every layer so the stack aligns. Bolts sit on the key
// BOUNDARIES (in the 5 mm gaps) so they never sit under a moving key. The rear
// column is behind the keys entirely, clear of the hinge bracket bolts.
module stack_bolts() {
    for (j = [0 : n_hinge - 1]) {
        y = boundary_y(j) + board_w / 2;
        // Front and stop-rail columns. The second must fall inside the stop
        // rail's x span so the rail is actually clamped. No rear column is
        // needed — the hinge bracket bolts already clamp all three layers there.
        for (x = [bx(8), bx(contact_x)])
            translate([x, y]) circle(d = bolt_d);
    }
}

// Black key switch holes, on the key boundaries. Black keys are switched now,
// so they need the same treatment as the white ones: an exact 14 mm cutout in
// the switch plate and a clearance hole everywhere else. The old web slots are
// gone — nothing is glued in any more.
module black_holes(d) {
    for (b = black_idx) {
        y = boundary_y(b + 1) + board_w / 2;
        translate([bx(blk_switch_x), y]) square([d, d], center = true);
    }
}

// Bolt holes for the hinge brackets. They pass through ALL THREE lower layers,
// so every layer subtracts them.
module hinge_bolts() {
    for (j = [0 : n_hinge - 1]) {
        y = boundary_y(j) + board_w / 2;
        for (x = [bx(hinge_bolt_x1), bx(hinge_bolt_x2)])
            translate([x, y]) circle(d = bolt_d);
    }
}

// =====================================================================
// The two laser layers are the SAME profile — identical outline, identical
// bolt patterns, identical black key slots. The only thing that differs is
// the size of the hole at each switch, so both are generated from one module.
// Keeping them in one place guarantees the stack cannot drift out of
// alignment when a bolt pattern is edited.
// =====================================================================
module layer_2d(switch_hole) {
    difference() {
        outline();
        stack_bolts();
        hinge_bolts();
        foot_bolts();
        for (i = [0 : n_keys - 1]) {
            y = key_y(i) + board_w / 2;
            translate([bx(contact_x), y])
                square([switch_hole, switch_hole], center = true);
        }
        black_holes(switch_hole);
    }
}

// --- Layer 1: structure (9 mm) ---------------------------------------
// Carries the feet, hinge brackets, stop rail and black key webs.
// Hole = sw_clear (17 mm): big enough for the switch body to pass through AND
// for the MX clips to spring outward and latch under the plate above. At 14 mm
// the clips would be pinched and could never engage.
module layer_struct_2d() { layer_2d(sw_clear); }

// Standoff bolt positions — four along each long edge, clear of the keys.
module foot_bolts() {
    for (y = [25, board_w / 2, board_w - 25])
        for (x = [bx(2), bx(key_len + 16)])
            translate([x, y]) circle(d = bolt_d);
}

// --- Layer 2: switch plate (1.5 mm) — THE accuracy-critical part -----
// Hole = mx_cut (14 mm, spec 14.00 +/- 0.05): the switch housing rests on this
// layer and its clips grip the underside. This is the ONE hole that must be
// accurate, which is why this layer is thin — a laser kerf tapers with depth.
// All 11 are cut in a single operation, so the 50 mm pitch has no seams.
module layer_switch_plate_2d() { layer_2d(mx_cut); }

// --- Layer 3: stop rail — the hard bottom stop for every key ---------
// Only spans the contact zone, not the whole key length.
module layer_stop_rail_2d() {
    difference() {
        translate([bx(stop_x0), 0]) square([stop_x1 - stop_x0, board_w]);
        for (i = [0 : n_keys - 1]) {
            y = key_y(i) + board_w / 2;
            translate([bx(contact_x), y]) square([stop_clear, stop_clear], center = true);
        }
        // the middle bolt column clamps the rail into the stack
        for (j = [0 : n_hinge - 1]) {
            y = boundary_y(j) + board_w / 2;
            translate([bx(contact_x), y]) circle(d = bolt_d);
        }
    }
}

// =====================================================================
// PRINTED PART: hinge bracket (12 off — one per key boundary)
// =====================================================================
// The only feature a laser cannot make: a pin bore cross-drilled through it.
// Small, so print mass stays low.
//
// The pin bore runs along Y — ACROSS the keys — so the key pivots up and down.
// (A bore along X would let the key roll sideways instead.)
//
// Origin is centred on the key BOUNDARY and sits on the TOP FACE OF THE STACK
// (the switch plate, z = z_plate_t). It must NOT start lower: the structural
// layer and switch plate span the whole board, so a bracket rooted at z=0
// would pass straight through them.
module hinge_block() {
    pin_z_local = pivot_z - z_plate_t;
    h = pin_z_local + hinge_post_len / 2;           // material over the bore
    flange_x = hinge_bolt_x2 - pivot_x + 4;         // reaches past the rear bolt
    difference() {
        union() {
            translate([-hinge_post_len/2, -hinge_post_w/2, 0])
                cube([hinge_post_len, hinge_post_w, h]);
            // Bolting flange runs REARWARD only — a forward flange would cross
            // the black key web, which shares this 5 mm gap.
            translate([-hinge_post_len/2, -hinge_post_w/2, 0])
                cube([flange_x + hinge_post_len/2, hinge_post_w, 3]);
        }
        translate([0, -hinge_post_w/2 - 1, pin_z_local])
            rotate([-90, 0, 0]) cylinder(h = hinge_post_w + 2, d = bolt_d);
        for (x = [hinge_bolt_x1 - pivot_x, hinge_bolt_x2 - pivot_x])
            translate([x, 0, -1]) cylinder(h = 6, d = bolt_d);
    }
}

// =====================================================================
// 3D assembly preview
// =====================================================================
module assembly_3d() {
    // standoffs — they lift the board so the switch pins and the wiring
    // harness have somewhere to live
    color("#888780")
        for (y = [25, board_w / 2, board_w - 25])
            for (x = [bx(2), bx(key_len + 16)])
                translate([x, y, -foot_h]) cylinder(h = foot_h, d = 9);
    color("#85B7EB") linear_extrude(t_struct) layer_struct_2d();
    color("#B5D4F4") translate([0, 0, z_plate])   linear_extrude(t_plate) layer_switch_plate_2d();
    color("#9FE1CB") translate([0, 0, z_plate_t]) linear_extrude(t_stop)  layer_stop_rail_2d();
    // hinge brackets, one per key boundary, standing in the 5 mm gaps.
    // They sit ON the switch plate — the top face of the laser stack.
    for (j = [0 : n_hinge - 1])
        color("#CECBF6")
            translate([bx(pivot_x), boundary_y(j) + board_w / 2, z_plate_t])
                hinge_block();
    // the single continuous pin rod every key pivots on
    color("#888780")
        translate([bx(pivot_x), -8, pivot_z])
            rotate([-90, 0, 0]) cylinder(h = board_w + 16, d = 3);
    // The printed keys from piano_keys.scad, so this preview shows the SAME
    // complete board as piano_base_printed.scad's "full" mode and the two
    // routes can be compared side by side. Set show_keys = false to see the
    // laser parts unobstructed.
    if (show_keys) {
        // Orientation check: reading left to right the black keys must go
        // single, PAIR, TRIPLET, single. Triplet before pair means the camera
        // is behind the board — move the camera, do not edit black_idx.
        for (i = [0 : n_keys - 1])
            color("white")
                translate([margin_front, key_y(i) + board_w / 2, 0]) key_lever(i);
        for (b = black_idx)
            color("black")
                translate([margin_front, boundary_y(b + 1) + board_w / 2, 0]) black_key();
    }
}

// =====================================================================
// Render selector
// =====================================================================
// "assembly_3d"      the whole board — same view as piano_base_printed's "full"
// "2d_struct" | "2d_switch_plate" | "2d_stop_rail"   -> the 3 laser cut files
// "hinge_block"      the one printed part (print 12)
mode      = "assembly_3d";
show_keys = true;   // false = laser parts only, unobstructed by the key levers

if      (mode == "assembly_3d")     assembly_3d();
else if (mode == "2d_struct")       layer_struct_2d();
else if (mode == "2d_switch_plate") layer_switch_plate_2d();
else if (mode == "2d_stop_rail")    layer_stop_rail_2d();
else if (mode == "hinge_block")     hinge_block();