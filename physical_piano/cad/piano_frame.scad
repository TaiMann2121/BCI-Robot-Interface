// =====================================================================
// piano_frame.scad — cosmetic surround for the keybed
// =====================================================================
// Purely aesthetic, per the supervisor's request. It carries no load, holds
// no switch and is not needed for the piano to work — so it can be printed
// last, or skipped entirely, without touching anything else.
//
// It also usefully hides the 12 mm wiring gap under the board, which is
// otherwise the least tidy part of the build.
//
//   mode "frame"      the whole surround, for a visual check
//   mode "cheek"      one end cheek                        -> print 2
//   mode "front_seg"  one segment of the front rail        -> print front_n
//   mode "back_seg"   one segment of the back rail         -> print back_n
//   mode "preview"    frame + board + keys together
//
// The long rails are split into segments because the board is 545 mm across
// and the printers are 254 mm. Segments butt at the same 3 mm dowels used for
// the base tiles.
//
// >>> CLEARANCE RULE <<<
// The robot's fingers come down from ABOVE and land at contact_x = 35 mm,
// measured back from the key front. So nothing may sit above white-key height
// anywhere in x = 0..front_clear. The front rail therefore stands entirely
// AHEAD of the keys (negative x) and rises only to the white key tops. The
// cheeks and back rail are clear of the fingers and may stand taller.
// =====================================================================

include <piano_params.scad>
use     <piano_keys.scad>
use     <piano_base_printed.scad>

$fn = 48;

// ---------------- Frame geometry ----------------
// The rails are WALLS, not solid blocks. Solid ones came to 481 g of filament
// (~$308) — more than the keybed itself, for a part that carries no load. As
// walls the frame is about a third of that. frame_th is the single knob if it
// still needs to come down.
frame_th      = 5;                     // wall thickness
frame_gap     = 1.5;                   // clearance between frame and keys
keys_w        = n_keys * pitch - key_gap;    // 545 mm across the keys

front_rail_w  = frame_th;              // wall ahead of the keys
back_rail_w   = frame_th;              // wall behind the keys
cheek_top     = black_top_z + 4;       // cheeks rise just above the black keys
front_top     = key_top_z;             // flush with the white keys
rail_bottom   = -foot_h;               // skirts down to the desk, hiding wiring

// Board extents in y, matching piano_base_printed's slot_y():
// key i sits at (n_keys-1-i)*pitch, so the keys span -key_w/2 .. keys_w-key_w/2
y_lo = -key_w/2 - frame_gap;
y_hi = (n_keys - 1) * pitch + key_w/2 + frame_gap;

// Segment counts so nothing exceeds the 254 mm print bed
front_n = ceil((y_hi - y_lo + 2*frame_th) / 240);
back_n  = front_n;

echo(str("frame outer = ", (y_hi - y_lo) + 2*frame_th, " x ",
         key_len + front_rail_w + back_rail_w + 2*frame_gap, " mm"));
echo(str("front/back rails split into ", front_n, " segments each"));
if (front_top > key_top_z)
    echo("*** WARNING: front rail rises above the white keys — it will foul ",
         "the robot's fingers, which land at x = ", contact_x, " ***");

// ---------------- Parts ----------------

// One end cheek. Spans the full depth of the board and rises above the black
// keys, the way a piano's cheek blocks do.
module cheek() {
    depth = key_len + front_rail_w + back_rail_w + 2*frame_gap;
    difference() {
        translate([-front_rail_w - frame_gap, 0, rail_bottom])
            cube([depth, frame_th, cheek_top - rail_bottom]);
        // lighten it and give the wiring a way out at the back
        translate([key_len - 30, -1, rail_bottom + 4])
            cube([26, frame_th + 2, 10]);
    }
}

// Front rail: ahead of the keys, topping out flush with the white keys so it
// never enters the fingers' approach.
module front_rail(len) {
    translate([-front_rail_w - frame_gap, 0, rail_bottom])
        cube([front_rail_w, len, front_top - rail_bottom]);
}

// Back rail: behind the keys, free to stand as tall as the cheeks.
module back_rail(len) {
    translate([key_len + frame_gap, 0, rail_bottom])
        cube([back_rail_w, len, cheek_top - rail_bottom]);
}

// Dowel bores so rail segments register to each other, same 3 mm rod as the
// base tiles and the hinge pin.
module seg_dowels(len) {
    for (x = [-front_rail_w/2 - frame_gap, key_len + frame_gap + back_rail_w/2])
        for (y = [0, len])
            translate([x, y, rail_bottom + 8]) rotate([-90,0,0])
                cylinder(h = 12, d = pin_d, center = true);
}

// ---------------- Render selector ----------------
mode = "preview";

seg_len = (y_hi - y_lo) / front_n;

if (mode == "frame") {
    color("#B4B2A9") {
        translate([0, y_lo - frame_th, 0]) cheek();
        translate([0, y_hi, 0])            cheek();
        translate([0, y_lo, 0]) front_rail(y_hi - y_lo);
        translate([0, y_lo, 0]) back_rail(y_hi - y_lo);
    }
} else if (mode == "cheek") {
    cheek();
} else if (mode == "front_seg") {
    difference() { front_rail(seg_len); seg_dowels(seg_len); }
} else if (mode == "back_seg") {
    difference() { back_rail(seg_len); seg_dowels(seg_len); }
} else if (mode == "preview") {
    // frame
    color("#B4B2A9") {
        translate([0, y_lo - frame_th, 0]) cheek();
        translate([0, y_hi, 0])            cheek();
        translate([0, y_lo, 0]) front_rail(y_hi - y_lo);
        translate([0, y_lo, 0]) back_rail(y_hi - y_lo);
    }
    // board + keys, so the fit can be judged
    for (i = [0 : n_keys - 1]) translate([0, slot_y(i), 0]) {
        color("gray")  base_cell(i);
        color("white") key_lever(i);
    }
    for (b = black_idx)
        color("black")
            translate([0, (slot_y(b) + slot_y(b + 1)) / 2, 0]) black_key();
}
