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
        }
        // Clearance for the switch body and pins, which hang mx_below_plate
        // (6.4 mm) under the plate — more than fits inside the socket riser.
        // It goes right through the base so the pins hang in free air and the
        // wires are soldered from underneath; the board stands on feet.
        translate([contact_x - (mx_cut + 3)/2, -(mx_cut + 3)/2, -1])
            cube([mx_cut + 3, mx_cut + 3, base_th + 2]);
        // Black-key locating half-grooves at the cell edges. Two butted cells
        // form one full groove; the black key's web drops in and is glued.
        if (is_black(idx))      translate([0,  pitch/2, 0]) black_groove();
        if (is_black(idx - 1))  translate([0, -pitch/2, 0]) black_groove();
    }
}

// true if a black key sits between white key i and i+1
function is_black(i) = len([for (b = black_idx) if (b == i) 1]) > 0;

module black_groove() {
    translate([blk_web_x0, -(black_stem_w + clr)/2, base_th - blk_groove_d])
        cube([blk_web_x1 - blk_web_x0, black_stem_w + clr, blk_groove_d + 1]);
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
    color("white") key_lever();
    color("black") translate([0, pitch/2, 0]) black_key();
} else if (mode == "base") {
    base_cell(0);
} else if (mode == "tile") {
    for (i = [0 : tile_n - 1])
        translate([0, i*pitch, 0]) base_cell(tile_i0 + i);
} else if (mode == "full") {
    for (i = [0:10]) translate([0, i*pitch, 0]) {
        color("gray")  base_cell(i);
        color("white") key_lever();
    }
    for (i = black_idx)
        color("black") translate([0, i*pitch + pitch/2, 0]) black_key();
}
