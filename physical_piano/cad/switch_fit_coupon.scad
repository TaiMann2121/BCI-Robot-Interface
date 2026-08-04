// =====================================================================
// switch_fit_coupon.scad — settle the switch hole size before committing
// =====================================================================
// The switch datasheet specifies the plate cutout as 14.00 +/-0.05 mm square
// in 1.50 +/-0.1 mm material (Kailh KH-PS1706-10 rev B, s.10). Neither of our
// processes holds +/-0.05 on a 14 mm feature, and they miss it in OPPOSITE
// directions:
//
//   FDM   undersizes holes by ~0.1-0.4 mm -> switch will not enter, or enters
//         so tightly the clips cannot spring out and latch
//   LASER kerf removes ~0.15-0.25 mm     -> hole comes out oversize and the
//         switch rattles instead of clipping
//
// So there is no single number that suits both routes, and no amount of CAD
// fixes it. Make this coupon in the REAL process, on the REAL material, at the
// REAL settings, clip a real switch into each hole, and read the answer off it.
//
//   mode "printed"  a slab carrying 7 sockets   -> print, 15 min, a few grams
//   mode "2d_laser" a flat profile for 1.5 mm   -> laser, one small offcut
//
// WHAT TO DO WITH IT
//   1. Try a switch in every hole, smallest first.
//   2. Take the SMALLEST hole the switch enters without force AND cannot be
//      pulled back out of by hand. Too loose is as wrong as too tight — the
//      clips have to grip, and a rattling switch moves under a 520 gf press.
//   3. Set mx_cut in piano_params.scad to that number and re-render.
//
// If two adjacent sizes both work, take the smaller.
//
// NOTE: this file deliberately repeats the socket stack from
// piano_base_printed.scad instead of importing it. The whole purpose is to
// vary mx_cut, which is a global there — one shared module cannot do both
// jobs. Keep the two in step if the stack ever changes.
// =====================================================================

include <piano_params.scad>

$fn = 48;

// The sizes to try, in mm. Centred on the datasheet's 14.00 so the nominal is
// always one of the options and you can see which way your process drifts.
sizes    = [13.8, 13.9, 14.0, 14.1, 14.2, 14.3, 14.4];

site     = 26;    // spacing between test holes
coupon_w = 30;    // across the strip
relief_h = 5.0;   // depth of clip relief below the plate. The clips sit ~5 mm
                  // under the plate, so this has to be deep enough for them to
                  // spring out — a blind 1.5 mm plate would test nothing.
label_d  = 0.6;   // engraving depth

coupon_l = len(sizes) * site;

// One test site. Origin at the hole centre, on the TOP face.
module socket_cuts(d) {
    // the plate hole itself — the dimension under test
    translate([-d/2, -d/2, -mx_plate_th])
        cube([d, d, mx_plate_th + 1]);
    // relief below, so the clips can open and latch exactly as they will in
    // the real part
    translate([-(d + 2)/2, -(d + 2)/2, -mx_plate_th - relief_h])
        cube([d + 2, d + 2, relief_h + 0.1]);
}

// str(14.0) renders as "14", which hides the one size that matters — the
// datasheet nominal. Force one decimal place so every label reads alike.
function fmt1(v) = str(floor(v), ".", round((v - floor(v)) * 10));

// Size engraved beside each hole. Positional order is ascending as well, so
// the coupon is still readable if the text does not come out.
module label(d, x) {
    translate([x, -coupon_w/2 + 4.5, -label_d])
        linear_extrude(label_d + 0.1)
            text(fmt1(d), size = 4.2, halign = "center", valign = "baseline");
}

module coupon_3d() {
    difference() {
        // slab, top face at z = 0
        translate([0, -coupon_w/2, -(mx_plate_th + relief_h)])
            cube([coupon_l, coupon_w, mx_plate_th + relief_h]);
        for (i = [0 : len(sizes) - 1]) {
            x = site * (i + 0.5);
            translate([x, 1.5, 0]) socket_cuts(sizes[i]);
            label(sizes[i], x);
        }
        // corner notch: marks the small-hole end, so a coupon that has been
        // turned round on the bench still reads correctly
        translate([0, -coupon_w/2, -(mx_plate_th + relief_h) - 1])
            linear_extrude(mx_plate_th + relief_h + 2)
                polygon([[0, 0], [6, 0], [0, 6]]);
    }
}

// Flat version for the laser, cut in the SAME 1.5 mm stock as the real switch
// plate — kerf depends on material and thickness, so testing it in anything
// else answers the wrong question.
module coupon_2d() {
    difference() {
        square([coupon_l, coupon_w]);
        for (i = [0 : len(sizes) - 1])
            translate([site * (i + 0.5), coupon_w/2 + 1.5])
                square([sizes[i], sizes[i]], center = true);
        for (i = [0 : len(sizes) - 1])
            translate([site * (i + 0.5), 4.5])
                text(fmt1(sizes[i]), size = 4.2, halign = "center",
                     valign = "baseline");
        polygon([[0, 0], [6, 0], [0, 6]]);
    }
}

echo(str("coupon: ", len(sizes), " holes, ", sizes[0], " to ",
         sizes[len(sizes)-1], " mm, ", coupon_l, " x ", coupon_w, " mm"));
echo(str("datasheet nominal is ", mx_cut, " — CAD is currently set to that"));

mode = "printed";

if      (mode == "printed")  coupon_3d();
else if (mode == "2d_laser") coupon_2d();
