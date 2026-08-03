// =====================================================================
// piano_base_printed.scad — the ALL-PRINTED route for the keybed base
// =====================================================================
// One of two alternative bases. Everything here is 3D printed.
//
//   mode "base"   one 50 mm base cell
//   mode "tile"   a printable run of cells (tile_n wide)   -> print 3 tiles
//   mode "full"   the whole 11-key board, VISUAL CHECK ONLY (too big to print)
//
// You ALSO need the key levers and black keys from piano_keys.scad — they are
// printed in both routes and are not duplicated here.
//
// BUILD VOLUME: TechSpark's printers are 10 x 10 x 10 in (254 mm) but the board
// is 545 mm wide, so the base must be split into 3 tiles (5 + 5 + 1 cells) and
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
// Base cell (one 50 mm-wide slice of keybed). Tile in +y.
// =====================================================================
// `idx` is the white-key index (0..10) this cell holds. It decides which of the
// cell's two edges gets a black-key locating half-groove. Pass -1 for a plain
// cell with no grooves.
module base_cell(idx = -1) {
    difference() {
        union() {
            translate([0, -pitch/2, 0]) cube([key_len, pitch, base_th]);
            hinge_post(1);
            hinge_post(-1);
            translate([contact_x, 0, base_th]) mx_socket();
            // half of each neighbouring black key's switch socket
            if (is_black(idx))      translate([0,  pitch/2, 0]) black_socket();
            if (is_black(idx - 1))  translate([0, -pitch/2, 0]) black_socket();
            cell_feet();
        }
        // Clearance for the switch body and pins, which hang mx_below_plate
        // (6.4 mm) under the plate — more than fits inside the socket riser.
        // It goes right THROUGH the base so the pins hang in free air, the
        // wires are soldered from underneath, and the harness runs in the
        // space the feet create out to the Arduino.
        translate([contact_x - (mx_cut + 3)/2, -(mx_cut + 3)/2, -1])
            cube([mx_cut + 3, mx_cut + 3, base_th + 2]);
        // Black keys are switched now, so each needs a switch cavity through
        // the plate rather than a groove to be glued into. Half the cavity
        // falls in each neighbouring cell; two butted cells form the whole.
        if (is_black(idx))      translate([0,  pitch/2, 0]) black_switch_cut();
        if (is_black(idx - 1))  translate([0, -pitch/2, 0]) black_switch_cut();
        // Alignment dowel half-holes on both cell edges.
        for (s = [-1, 1]) translate([0, s * pitch/2, 0]) dowel_holes();
    }
}

// Integral feet, one pair per cell. They lift the board by foot_h so the
// switch pins (which hang mx_below_plate under the plate) clear the desk and
// the wiring harness has somewhere to run. Printed as part of the cell — no
// standoffs to buy and nothing to align.
module cell_feet() {
    for (x = [15, 125])
        translate([x, 0, -foot_h]) cylinder(h = foot_h + 0.1, d = 10);
}

// Half-holes on each cell edge. Inside a printed tile these are just holes;
// at a TILE SEAM the two halves form one bore, and a length of the same 3 mm
// rod used for the hinge pins registers the tiles to each other.
//
// This matters specifically for the printed route: the board is split into 3
// tiles for the 254 mm print bed, so the 50 mm key pitch — the thing the arm
// is calibrated to — has to survive two joins. Butting the tiles by eye would
// put that at risk; a dowel makes the joint repeatable.
module dowel_holes() {
    // x positions clear of the switch cavity (25-45), the black key groove
    // (62-120) and the hinge posts (122.5-131.5)
    for (x = [12, 137])
        translate([x, 0, -1]) cylinder(h = base_th + 2, d = pin_d);
}

// Physical y of key index i. Mirrored so key 0 lands at HIGH y, which is the
// viewer's LEFT when standing at the front — matching how the simulator draws
// it. See the orientation note at the top of piano_params.scad.
function slot_y(i) = (n_keys - 1 - i) * pitch;

// Clearance through the base plate for a black key's switch body and pins,
// centred on the key boundary. The socket that actually holds the switch is
// added in the union (black_socket); this is just the hole beneath it.
module black_switch_cut() {
    translate([blk_switch_x - (mx_cut + 3)/2, -(mx_cut + 3)/2, -1])
        cube([mx_cut + 3, mx_cut + 3, base_th + 2]);
}

// The black key's MX socket. Same 14 mm plate cutout as the white keys, but
// with NO stop shoulders: black keys are hand-pressed, so bottoming out on the
// switch is ordinary keyboard use. Origin on the key boundary.
module black_socket() {
    boss = mx_cut + 2*2.5;
    difference() {
        translate([blk_switch_x - boss/2, -boss/2, base_th])
            cube([boss, boss, mx_riser_h]);
        translate([blk_switch_x - mx_cut/2, -mx_cut/2, base_th + mx_riser_h - mx_plate_th])
            cube([mx_cut, mx_cut, mx_plate_th + 1]);
        translate([blk_switch_x - (mx_cut+2)/2, -(mx_cut+2)/2, base_th - 1])
            cube([mx_cut + 2, mx_cut + 2, mx_riser_h - mx_plate_th + 1]);
    }
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

// MX socket: a riser carrying the 14 x 14 mm plate cutout, with integral
// shoulders rising to stop_top. Those shoulders are the hard bottom stop, so
// the finger's overshoot lands on the frame rather than the switch.
// Origin at (contact_x, 0, base_th).
module mx_socket() {
    boss = mx_cut + 2*3;
    difference() {
        union() {
            translate([-boss/2, -boss/2, 0]) cube([boss, boss, mx_riser_h]);
            for (s = [-1, 1])
                translate([s*(mx_cut/2 + 2.5) - 4/2, -boss/2, 0])
                    cube([4, boss, stop_top - base_th]);
        }
        // the plate the clips grip
        translate([-mx_cut/2, -mx_cut/2, mx_riser_h - mx_plate_th])
            cube([mx_cut, mx_cut, mx_plate_th + 1]);
        // wider bore below it so the clips can spring out and latch
        translate([-(mx_cut + 2)/2, -(mx_cut + 2)/2, -1])
            cube([mx_cut + 2, mx_cut + 2, mx_riser_h - mx_plate_th + 1]);
    }
}

// =====================================================================
// Render selector
// =====================================================================
// "full"      the whole 11-key board — the default, so this file and
//             piano_base_laser.scad open showing the SAME view and the two
//             routes can be compared directly. Too big to print.
// "assembly"  one cell + one key + one black key, for checking fit up close
// "base"      one bare base cell
// "tile"      a printable run of tile_n cells   -> print 3 of these
mode    = "full";
tile_n  = 5;     // cells per printed tile — 5 x 50 mm = 250 mm, fits a 254 mm bed
tile_i0 = 0;     // index of the first white key in this tile

if (mode == "assembly") {
    color("gray")  base_cell(0);
    color("white") key_lever(0);
    color("black") translate([0, pitch/2, 0]) black_key();
} else if (mode == "base") {
    base_cell(0);
} else if (mode == "tile") {
    for (i = [0 : tile_n - 1])
        translate([0, i*pitch, 0]) base_cell(tile_i0 + i);
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
