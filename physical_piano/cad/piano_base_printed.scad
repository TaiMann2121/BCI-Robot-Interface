// =====================================================================
// piano_base_printed.scad — the ALL-PRINTED route for the keybed base
// =====================================================================
// One of two alternative bases. Everything here is 3D printed.
//
//   mode "base"   one 50 mm base cell
//   mode "tile"   one printable tile (set tile_i = 0/1/2)  -> print all 3
//   mode "full"   the whole 11-key board, VISUAL CHECK ONLY (too big to print)
//
// You ALSO need the key levers and black keys from piano_keys.scad — they are
// printed in both routes and are not duplicated here.
//
// BUILD VOLUME: TechSpark's printers are 10 x 10 x 10 in (254 mm) but the board
// is 545 mm wide, so the base must be split into 3 tiles (5 + 4 + 2 cells) and
// joined. The 50 mm key pitch therefore has to survive two seams — which is the
// main argument for the laser route in piano_base_laser.scad, where all 11
// switch holes are cut in one operation on one sheet.
//
// Shared dimensions live in piano_params.scad. See ../TECHSPARK_PLAN.md.
// =====================================================================

include <piano_params.scad>
use     <piano_keys.scad>      // key_lever() / black_key() for the preview modes

$fn = 48;

// =====================================================================
// Tiling — where the board is cut for the 254 mm print bed
// =====================================================================
// The 11 cells are printed as 3 tiles. WHICH cells each tile holds is not
// arbitrary: a seam must not fall on a black-key boundary, because the black
// key's switch socket straddles the boundary and would end up half on each
// tile, with the glue joint running straight through the 14 mm mounting hole
// that the MX clips grip.
//
// Black keys sit at boundaries after cells [0, 2, 3, 5, 6, 7, 9], so the only
// seam-safe boundaries are after cells 1, 4, 8 and 10. With a 5-cell (250 mm)
// tile limit, "after 4" and "after 8" is the ONLY 3-way split that works:
//
//   tile 0 -> cells 0..4   (5 cells, 250 mm)
//   tile 1 -> cells 5..8   (4 cells, 200 mm)
//   tile 2 -> cells 9..10  (2 cells, 100 mm)
//
// The previous 5 + 5 + 1 split put a seam after cell 9, which IS a black-key
// boundary.
tile_first = [0, 5, 9];              // first cell index of each tile
tile_last  = [4, 8, 10];             // last  cell index of each tile
seam_after = [4, 8];                 // a seam falls between cell s and s+1

// Feet live on the FIRST and LAST cell of each tile, so every tile stands on
// its own on the bench before the three are joined, and the finished board is
// supported at both ends of each span. Every cell used to carry a pair — 22
// feet on a 545 mm board, one every 25 mm, which is far more support than a
// plate this short needs and a lot of extra print time.
foot_cells = concat(tile_first, tile_last);   // 12 feet, was 22

function in_list(v, L) = len([for (e = L) if (e == v) 1]) > 0;

// =====================================================================
// Base cell (one 50 mm-wide slice of keybed). Tile in -y (see slot_y).
// =====================================================================
// `idx` is the white-key index (0..10) this cell holds. It decides which of the
// cell's two edges carries half of a black key's switch socket, whether the
// cell gets feet, and whether its edges are at a tile seam. Pass -1 for a plain
// cell with no black-key features.
//
// SIDE CONVENTION: slot_y() DECREASES with the index, so cell idx+1 is the -y
// neighbour of cell idx. is_black(idx) — the boundary between idx and idx+1 —
// is therefore at -pitch/2, and is_black(idx-1) is at +pitch/2. These were
// swapped, which put every black key's switch socket one boundary off.
//
// STRUCTURE: every subtraction happens in the ONE difference() below, and the
// modules in the union() are solid. mx_socket() and black_socket() used to
// carry their own nested difference(), which made the CSG tree needlessly deep
// and scattered the cuts across three places. (The reason the switch holes
// previewed as solid floors is in switch_cuts() — coincident cut faces, not
// the nesting — but keeping the cuts together is what makes that easy to see.)
module base_cell(idx = -1) {
    difference() {
        union() {
            translate([0, -pitch/2, 0]) cube([key_len, pitch, base_th]);
            hinge_post(1);
            hinge_post(-1);
            translate([contact_x, 0, base_th]) mx_boss();
            // Half of each neighbouring black key's switch boss. Clipped to
            // this cell so a tile edge stays flat: the other half is grown by
            // the neighbouring cell, and two butted cells form the whole boss.
            if (is_black(idx))      black_half_boss(-1);
            if (is_black(idx - 1))  black_half_boss( 1);
            if (in_list(idx, foot_cells)) cell_feet();
        }
        // ---- white key switch -------------------------------------------
        // The plate cutout, the clip relief under it, and a clearance hole
        // right THROUGH the base: the switch body and pins hang
        // mx_below_plate (6.4 mm) under the plate, more than fits inside the
        // riser. The pins end up in free air, the wires are soldered from
        // underneath, and the harness runs out to the Arduino in the space
        // the feet create.
        translate([contact_x, 0, base_th]) mx_cuts();
        // ---- black key switches -----------------------------------------
        // Switched, not decorative, so each needs the same cavity as a white
        // key rather than a groove to be glued into. Half falls in each
        // neighbouring cell.
        if (is_black(idx))      translate([0, -pitch/2, base_th]) black_cuts();
        if (is_black(idx - 1))  translate([0,  pitch/2, base_th]) black_cuts();
        // ---- tile registration ------------------------------------------
        if (in_list(idx,     seam_after)) translate([0, -pitch/2, 0]) dowel_holes();
        if (in_list(idx - 1, seam_after)) translate([0,  pitch/2, 0]) dowel_holes();
    }
}

// Integral feet, one pair per cell that carries them (see foot_cells). They
// lift the board by foot_h so the switch pins (which hang mx_below_plate under
// the plate) clear the desk and the wiring harness has somewhere to run.
// Printed as part of the cell — no standoffs to buy and nothing to align.
module cell_feet() {
    for (x = [15, 125])
        translate([x, 0, -foot_h]) cylinder(h = foot_h + 0.1, d = 10);
}

// Half-holes on a cell edge, cut ONLY where a tile seam falls (seam_after).
// The two halves form one bore across the joint, and a length of the same 3 mm
// rod used for the hinge pins registers the tiles to each other.
//
// This matters specifically for the printed route: the board is split into 3
// tiles for the 254 mm print bed, so the 50 mm key pitch — the thing the arm
// is calibrated to — has to survive two joins. Butting the tiles by eye would
// put that at risk; a dowel makes the joint repeatable.
//
// They used to be cut on EVERY cell edge, which put 44 blind holes through the
// base plate, 40 of them inside a tile where there is no joint to register and
// nothing to put in them.
module dowel_holes() {
    // x positions clear of the switch cavity (25-45), the black key socket
    // (87.6-105.6) and the hinge posts (122.5-131.5)
    for (x = [12, 137])
        translate([x, 0, -1]) cylinder(h = base_th + 2, d = pin_d);
}

// Physical y of key index i. Mirrored so key 0 lands at HIGH y, which is the
// viewer's LEFT when standing at the front — matching how the simulator draws
// it. See the orientation note at the top of piano_params.scad.
function slot_y(i) = (n_keys - 1 - i) * pitch;

// ---------------------------------------------------------------------
// Black key switch. SOLID and CUT are separate modules so base_cell() can do
// all of its subtraction at one level — see the note on base_cell().
// ---------------------------------------------------------------------
// blk_boss is 18 mm, not the white keys' 20 mm: it has to fit between the two
// notched white keys either side of it. A notched key edge sits
// key_w/2 - blk_notch = 15 mm from the cell centre, i.e. 10 mm from the
// boundary the boss is centred on, so a half-boss of 9 mm leaves 1 mm of
// clearance per side. At the old 19 mm that was only 0.5 mm, which print
// tolerance alone could close.
blk_boss = mx_cut + 2*2;    // 18

// Half of a black key's boss — the half lying inside THIS cell.
// side = -1 for the boss on the cell's -y edge, +1 for the +y edge.
module black_half_boss(side) {
    y0 = (side > 0) ? (pitch/2 - blk_boss/2) : -pitch/2;
    translate([blk_switch_x - blk_boss/2, y0, base_th])
        cube([blk_boss, blk_boss/2, mx_riser_h]);
}

// Everything removed at a black key switch. Same 14 mm plate cutout as the
// white keys, but NO stop shoulders: black keys are hand-pressed, so bottoming
// out on the switch is ordinary keyboard use. Origin on the key boundary at
// the TOP OF THE BASE PLATE, so it is called translated to (0, +/-pitch/2,
// base_th) — the same frame mx_cuts() uses.
module black_cuts() { switch_cuts(blk_switch_x); }

// The cut stack shared by every switch position, in TWO tiers:
//
//   mx_cut     14 mm  the plate the clips grip — the one accuracy-critical
//                     dimension, and the only place the bore is this tight
//   mx_cut + 2 16 mm  everything below it, in one cube: the relief that lets
//                     the clips spring out and latch, carried straight on
//                     through the base plate so the body and pins hang in
//                     free air, the wires are soldered from underneath, and
//                     the harness runs out to the Arduino under the board
//
// Origin at (0, 0, base_th) — z = 0 is the TOP of the base plate.
//
// This used to be three tiers, with the through-base hole widened to 17 mm.
// That extra millimetre bought nothing (16 mm already clears the 13.95 mm
// body) and left a 0.5 mm ring of wall at the bottom of the 18 mm black key
// boss, too thin to print. Two tiers leave 1 mm there and 2 mm at the white
// keys' 20 mm boss.
//
// The tiers OVERLAP in z by ov rather than meeting face to face. Two
// subtracted volumes that share a plane exactly give OpenSCAD's F5 preview
// coincident surfaces to z-fight over, and the artifact reads as a solid floor
// across the hole — which is what made these holes look like blind pockets on
// screen. F6 cut them correctly the whole time, but the preview is what
// anyone actually looks at.
module switch_cuts(x) {
    ov      = 0.5;
    plate_z = mx_riser_h - mx_plate_th;    // 3 — underside of the plate
    translate([x - mx_cut/2, -mx_cut/2, plate_z])
        cube([mx_cut, mx_cut, mx_plate_th + 1]);
    translate([x - (mx_cut + 2)/2, -(mx_cut + 2)/2, -base_th - 1])
        cube([mx_cut + 2, mx_cut + 2, base_th + 1 + plate_z + ov]);
}

// One hinge post. side = +1 / -1 puts it just outside the key cap, inside the
// 5 mm inter-key gap, so the moving key never touches it. The pin bore runs
// along Y — ACROSS the keys — so the key pivots up and down.
module hinge_post(side) {
    y0 = (side > 0) ? (key_w/2 + clr) : -(key_w/2 + clr + post_w);
    difference() {
        translate([pivot_x - post_len/2, y0, base_th])
            cube([post_len, post_w, pivot_z - base_th + post_len/2]);
        translate([pivot_x, y0 - 1, pivot_z])
            rotate([-90, 0, 0]) cylinder(h = post_w + 2, d = pin_d);
    }
}

// White key MX socket, SOLID half: a riser carrying the plate, with integral
// shoulders rising to stop_top. Those shoulders are the hard bottom stop, so
// the finger's overshoot lands on the frame rather than the switch.
// Origin at (contact_x, 0, base_th). The holes are cut by mx_cuts(), called
// with the same translate — see the note on base_cell().
//
// The shoulders stand off stop_clear/2, the SAME clearance the laser route's
// stop rail uses, so the two routes present the switch with identical
// geometry. They used to sit at mx_cut/2 + 0.5 = 7.5, a 15.0 mm gap, which is
// narrower than the 15.60 mm housing that has to pass down between them.
// They are rooted on the base plate, not on the boss, so they may overhang it.
module mx_boss() {
    boss = mx_cut + 2*3;
    translate([-boss/2, -boss/2, 0]) cube([boss, boss, mx_riser_h]);
    for (s = [-1, 1])
        translate([s > 0 ? stop_clear/2 : -(stop_clear/2 + stop_width),
                   -boss/2, 0])
            cube([stop_width, boss, stop_top - base_th]);
}

// White key MX socket, CUT half. Same frame as mx_boss().
module mx_cuts() { switch_cuts(0); }

// =====================================================================
// Render selector
// =====================================================================
// "full"      the whole 11-key board — the default, so this file and
//             piano_base_laser.scad open showing the SAME view and the two
//             routes can be compared directly. Too big to print.
// "assembly"  one cell + one key + one black key, for checking fit up close
// "base"      one bare base cell
// "tile"      one printable tile -> set tile_i and print all 3
mode   = "full";
tile_i = 0;      // which tile to render: 0, 1 or 2. Cells and seam-safety are
                 // set by tile_first / tile_last near the top of this file.

if (mode == "assembly") {
    color("gray")  base_cell(0);
    color("white") key_lever(0);
    // is_black(0) is true, so key 0's black key is its -y neighbour
    color("black") translate([0, -pitch/2, 0]) black_key();
} else if (mode == "base") {
    base_cell(0);
} else if (mode == "tile") {
    // -i*pitch so the tile reads the same way round as the assembled board
    for (i = [tile_first[tile_i] : tile_last[tile_i]])
        translate([0, -(i - tile_first[tile_i]) * pitch, 0]) base_cell(i);
} else if (mode == "full") {
    // Orientation check: reading left to right the black keys must go single,
    // PAIR, TRIPLET, single. Triplet before pair means the camera is behind the
    // board — move the camera, do not edit black_idx.
    //
    // slot_y() mirrors the index so key 0 lands at HIGH y = the viewer's left,
    // matching the simulator. See the orientation note in piano_params.scad.
    for (i = [0 : n_keys - 1]) translate([0, slot_y(i), 0]) {
        color("gray")  base_cell(i);
        color("white") key_lever(i);
    }
    // a black key sits midway between the slots of key b and key b+1
    for (b = black_idx)
        color("black")
            translate([0, (slot_y(b) + slot_y(b + 1)) / 2, 0]) black_key();
}
