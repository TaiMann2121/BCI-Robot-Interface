// =====================================================================
// piano_params.scad — SINGLE SOURCE OF TRUTH for the physical piano
// =====================================================================
// Both fabrication routes include this file:
//   piano_keys.scad         key levers + black keys (printed in BOTH routes)
//   piano_base_printed.scad all-printed base   \  pick ONE
//   piano_base_laser.scad   laser-cut base     /
//
// Every dimension the two routes must agree on lives HERE and nowhere else.
// This is not housekeeping: pivot_z was previously defined in both files and
// silently drifted to 26.5 in one and 28 in the other, which would have put
// the laser route's hinge pin 1.5 mm too high.
//
// Values marked MEASURED were taken off the physical rig. Do not change them
// without re-measuring.
// =====================================================================

// ---------------- ORIENTATION — read this before changing any layout ----
// x = along the key, 0 at the FRONT edge (the side the fingers press)
// z = up
// y = across the keys
//
// Standing at the front looking at the board: forward = +x, up = +z, so the
// viewer's right = (+x cross +z) = -y. In other words **+y is the viewer's
// LEFT**.
//
// The simulator draws key 0 LEFTMOST, so key 0 must sit at HIGH y. The layout
// functions in the base files handle that. Do NOT "fix" a mirrored-looking
// render by editing black_idx — the board is near enough symmetric that a
// camera on the wrong side swaps the C#D# pair and the F#G#A# triplet, and
// mirroring the list to compensate leaves key 0 at the wrong end, which would
// wire the whole piano backwards.
n_keys    = 11;

// ---------------- Key layout (MEASURED) ----------------
key_w     = 45;      // key width  (mm)
key_len   = 140;     // key length (mm)
key_gap   = 5;       // gap between keys
pitch     = key_w + key_gap;    // 50 mm — what the arm is calibrated to
cap_th    = 4;       // key cap thickness
side_rail = 3;       // cosmetic side skirt

// Fingertip contact point, MEASURED at 35 mm from the key's front edge.
contact_x = 35;

// ---------------- Base / pivot ----------------
base_th   = 6;       // printed base plate thickness
pin_d     = 3.4;     // hinge pin bore (3 mm rod)
pivot_x   = key_len - 13;
clr       = 0.4;     // print clearance for moving mates
// hinge_h and pivot_z are DERIVED further down, from the stop geometry. They
// used to be set here by hand (hinge_h = 20.2), which is what let the press
// the switch actually sees drift 0.3 mm below the nominal mx_press figure —
// see the note on stop_r_lead.

// Knuckle must nearly fill the span between hinge supports or nothing stops
// the key sliding along the pin (see the note in piano_keys.scad).
knuckle_wid    = 45;
knuckle_boss_d = 9;
post_w         = 2;  // hinge post thickness — must fit the 5 mm inter-key gap
post_len       = 9;

// ---------------- MX switch ----------------
// EVERY VALUE IN THIS BLOCK IS READ OFF THE DATASHEET, not estimated:
//   Kailh CPG1511F01S04-1 "Red Shaft", doc KH-PS1706-10 rev B
//   -> ../docs/datasheets/kailh_CPG1511F01S04-1_red.pdf
// The section it comes from is named on each line, so any of these can be
// re-checked in one look. Where a tolerance is given the WORST CASE is used.
// Values that are NOT from the datasheet live in the two blocks below this
// one — do not add estimates here.
//
// s.5  = Profile Dimensions (p.3)
// s.10 = Loading Parameter Specification + Metal Frame Cutout (p.10)

// s.10 "Metal Frame Cutout Dimensions" specifies the PLATE HOLE directly:
// 14.00 +/-0.05 square, corners R0.30 max, in 1.50 +/-0.1 material. So this is
// not inferred from the 13.95 body width — it is the manufacturer's own plate
// spec, and the two agree.
mx_cut       = 14.0;   // s.10  plate cutout, 14.00 +/-0.05
mx_cut_r_max = 0.30;   // s.10  max corner radius of that cutout
mx_plate_th  = 1.5;    // s.10  1.50 +/-0.1 — the thickness the clips grip
mx_travel    = 3.6;    // s.10  TT total travel, 3.60 +/-0.3 -> worst MIN 3.3
mx_travel_tol = 0.3;
mx_actuate   = 1.8;    // s.10  PT pretravel,   1.80 +/-0.3 -> worst MAX 2.1
mx_actuate_tol = 0.3;
// s.10 OT: the travel guaranteed to remain BEYOND the operating point. Since
// TT = PT + OT, this rules out the corner the checks below assume — a switch
// cannot both actuate as late as 2.1 and bottom out as early as 3.3, because
// that would leave OT = 1.2. Designing against both extremes at once is
// therefore conservative, which is deliberate. Do not "recover" the margin.
mx_overtravel = 1.30;  // s.10  OT, minimum
mx_stem_h    = 11.20;  // s.5   stem top above the mounting plate
mx_cross_h   = 3.80;   // s.5   keycap cross post height. This is ALL the
                       //       engagement a keycap can ever get, and it sits
                       //       at the TOP of the stem: the cross spans
                       //       stem_top_z - 3.80 .. stem_top_z. A socket
                       //       placed above stem_top_z grips nothing.
mx_lower_h   = 5.00;   // s.5   lower housing, plate underside downwards
mx_pin_h     = 1.40;   // s.5   pins below that
mx_below_plate = mx_lower_h + mx_pin_h;   // 6.4 below the plate
mx_body_h    = 10.70;  // s.5   whole body, stem and pins excluded
mx_housing_h = mx_body_h - mx_lower_h;    // 5.70 of housing ABOVE the plate

// The top flange is RECTANGULAR, not square, and the switch is lowered between
// the stop shoulders to reach the plate — so it is the WIDE axis the stop
// clearance has to swallow. stop_clear was 15.0, which is under 15.60: the
// switch then only went in turned 90 degrees, with 0.55 mm per side on a
// printed part and nothing in the model saying so. stop_clear is now 17.0 and
// it fits either way round.
mx_housing_w = 15.60;  // s.5  top flange, WIDE axis
mx_housing_d = 13.90;  // s.5  top flange, NARROW axis
mx_clip_w    = 14.87;  // s.5  clips at full width below the plate, +/-0.5, so
                       //      worst case 15.37 — this is what the relief under
                       //      the plate has to clear, not the 13.95 body

// ---------------- OUR CHOICE, not the switch's ----------------------------
mx_riser_h   = 4.5;    // how high we stand the switch plate above the base
                       // plate. Nothing in the datasheet asks for this; it is
                       // set so the stack lands on the shared heights below.

// ---------------- NOT dimensioned on the datasheet — MEASURE THESE ---------
// The datasheet DRAWS all four of these but never dimensions them. The figures
// here were scaled off the s.5 top view against the known 15.60 mm width, so
// treat them as +/-0.15 mm at best. All four gate the black keycap, which is
// the one part that grips the switch rather than merely clearing it.
mx_well_w     = 7.0;   // housing opening the stem slides through. Caps how fat
                       // the black keycap's lower boss may be (blk_boss_w).
mx_shoulder_w = 6.6;   // stem top face — what the keycap seats on
// The cross scales to 4.0 mm across with arms of ~1.27 and ~1.10 mm. It is
// NOT symmetric — that matches the usual MX figures of 1.35 and 1.15 — so a
// square socket has real clearance on one axis and almost none on the other.
mx_cross_w    = 4.0;   // cross span, both arms
mx_cross_th   = 1.35;  // THICKER arm. The thin one is ~1.15; sizing the socket
                       // to the thick arm is what makes it fit both.

// ---------------- Stops ----------------
// The hard bottom stop for the white keys. Both routes build it: the printed
// route as shoulders either side of the socket, the laser route as a rail
// across the board. Sharing the numbers here is what keeps the two agreeing.
stop_clear = 17.0;   // square hole at each key, clears the 15.60 housing
stop_width = 4.0;    // stop material either side of that hole
// A GIVEN, not a free choice: it is the laser stack, 9.0 + 1.5 + 13.0 mm of
// stock. pivot_z is derived from it rather than the other way round.
stop_top   = 23.5;

// ---------------- Motion ----------------
rest_gap  = 0;     // key RESTS on the stem; a gap is physically impossible
// Chosen as the midpoint between the worst-case actuation depth (2.1) and the
// worst-case bottom-out depth (3.3), so it has 0.6 mm of margin either way.
// This is the press AT THE PLUNGER, which is what the switch sees.
mx_press  = 2.7;

// ---------------- Self-actuation figures ----------------
key_mass_g    = 16;   // printed key lever, ~20% infill
// RF (return force) is specified as a MINIMUM of 15 gf. The datasheet gives no
// preload figure, so 15 gf is the only guaranteed force holding the key up —
// design against it, not against a typical value.
mx_preload_gf = 15;
mx_act_gf     = 45;   // OF operating force, 45 +/-10 gf
com_arm       = 57;   // key centre of mass from the pivot

// ---------------- Black keys (mirrors the simulator) ----------------
// IDENTICAL to blackKeyIndices in Piano_Application_vel.py:775. A black key
// sits between white keys b and b+1. Left to right this reads as a single,
// then the C#/D# pair, then the F#/G#/A# triplet, then a single.
black_idx    = [0, 2, 3, 5, 6, 7, 9];

// true if a black key sits between white key i and i+1
function is_black(i) = len([for (b = black_idx) if (b == i) 1]) > 0;

black_w      = key_w   * 0.58;   // 26.1
black_len    = key_len * 0.62;   // 86.8, occupies the REAR
black_rise   = 10;
black_stem_w = 3.6;
blk_cap_th   = 5;
// blk_web_x0 / blk_web_x1 / blk_groove_d used to describe the web that dropped
// into a glued groove. Black keys have been switched keycaps for a while and
// nothing referenced them any more, so they are gone rather than left here
// describing a design that no longer exists.
front_clear  = key_len - black_len;   // 53.2 — fingers must contact inside this

// ---------------- Black keys are SWITCHED, not decorative -------------
// This forces the white keys to be notched. An MX switch housing is 15.6 mm
// across and the inter-key gap is only 5 mm, so a switch cannot sit under a
// black key until that gap is widened. Narrowing the white keys where a black
// key sits is exactly what a real piano does, so the board also ends up
// looking more authentic.
blk_notch    = 7.5;   // how much a white key narrows on each black-key side
blk_notch_x0 = front_clear;  // notch starts where the black keys start
blk_notch_x1 = 122;   // ...and stops before the hinge knuckle, which needs
                      // its full 45 mm width to locate the key on the pin
// WHERE THE STEM SITS UNDER THE CAP. The single MX stem is the black key's
// only support, so this one number decides both how far the key tilts under an
// off-centre press and whether it hangs level at rest at all.
//
// It was 75: 21.8 mm behind the cap's front edge but 65 mm ahead of its back.
// That put the cap's own weight ~22 mm BEHIND the stem, so the key sat
// nose-up under nothing but gravity, and a press on the back end applied three
// times the moment of a press on the front.
//
// Under the cap's CENTROID the static bias is zero and the worst-case press
// moment drops from 65 mm of arm to 43.4. The trade is real and worth knowing:
// a press near the FRONT now has a 43 mm arm instead of 22, so the typical
// press is worse while the worst press is better and neither end is
// unbounded. A 87 mm keycap on one stem really wants a stabiliser — this is
// the best a single stem can do.
blk_switch_x = key_len - black_len/2;   // 96.6, the cap's centroid

// MX keycap mount: the black keycap pushes straight onto the switch stem, the
// way any keyboard keycap does. No lever, no separate return spring.
//
// Sized FROM the cross plus an explicit clearance, so the two numbers that are
// measurements and the two that are fit allowances stay visibly separate. The
// socket used to be a bare 4.2 x 1.35 with no stated origin, and 1.35 is the
// thick arm's own size — nominally zero clearance, on a printed part, where
// FDM narrows a slot like this by a further 0.1-0.2 mm. It would not have gone
// on without force, and the post wall around it is only 0.65 mm.
mx_mount_clr   = 0.2;   // per-axis clearance, printed socket over moulded cross
mx_mount_cross = mx_cross_w  + mx_mount_clr;   // 4.2
mx_mount_th    = mx_cross_th + 0.1;            // 1.45
mx_mount_depth = 4.0;   // socket deeper than mx_cross_h (3.80) on purpose, so
                        // the cap seats on the stem SHOULDER and not on the
                        // tip of the cross

// Black keys are pressed by hand, never by the robot (fingers land at
// contact_x = 35, well forward of front_clear). They therefore need NO stop
// shoulders: bottoming out on the switch at 3.6 mm is ordinary keyboard use,
// which the 80 M cycle rating covers. The stops on the white keys exist only
// because the robot presses those with 362-520 gf.
blk_travel   = mx_travel;

// ---------------- Derived heights — DO NOT hardcode these anywhere ----
mx_plate_z  = base_th + mx_riser_h;                 // 10.5 switch plate top
stem_top_z  = mx_plate_z + mx_stem_h;               // 21.7 stem top at rest
housing_top_z = mx_plate_z + mx_housing_h;          // 16.2 top of the housing
shoulder_z  = stem_top_z - mx_cross_h;              // 17.9 base of the cross,
                                                    //      i.e. what a keycap
                                                    //      actually seats on
plunger_arm = pivot_x - contact_x;                  // 92 mm

// ---- Where the key really lands, and why the pivot sits where it does -----
// The cap underside is a PLANE THROUGH THE PIVOT AXIS, so a point r from the
// pivot drops r/plunger_arm as far as the plunger does. The stop that binds is
// therefore the FORWARDMOST stop material — furthest from the pivot — not the
// stop nearest the plunger, and not the plunger's own radius.
//
// Ignoring that is what cost 0.3 mm: with the pivot at 26.2 and the stop top
// at 23.5 the plunger only travelled 2.40 mm before the cap grounded out, not
// the 2.7 the parameters claimed, leaving 0.3 mm over worst-case actuation
// instead of 0.6. So pivot_z is now solved FROM the stop rather than assumed.
stop_r_lead = pivot_x - (contact_x - (stop_clear/2 + stop_width));   // 104.5
pivot_z     = stop_top + mx_press * stop_r_lead / plunger_arm;       // 26.57
hinge_h     = pivot_z - base_th;                    //      for the hinge posts
under_rest  = pivot_z;                              //      cap underside
throw       = rest_gap + mx_press;                  //  2.7 travel AT the stem
plunger_len = pivot_z - (stem_top_z + rest_gap);    //  4.87
key_top_z   = pivot_z + cap_th;                     // 30.57 above the board
black_top_z = key_top_z + black_rise;               // 40.57

// ---- Black keycap: where the socket has to be ----------------------------
// The socket mouth sits at the BASE of the cross (shoulder_z), not at the top
// of the stem. Placing the post's bottom face at stem_top_z — which is what
// this design did — leaves the whole 3.80 mm cross below the socket and the
// cap grips nothing at all.
blk_socket_z = shoulder_z;
// The post's lower section has to be slim enough to follow the stem down into
// the housing opening, exactly as a real keycap's does. If it is not, the cap
// grounds on the housing after only shoulder_z - housing_top_z = 1.7 mm, which
// is less than the 2.1 mm a worst-case switch needs to actuate.
blk_boss_w   = 5.5;   // MEASURE mx_well_w before trusting this
// ...and it must stay slim until it is clear of the housing at full travel.
blk_step_z   = housing_top_z + blk_travel + 0.8;    // 20.6

foot_h      = 12;    // standoff height under the board (wiring space)

// ---------------- Orientation marker ----------------
// KEY 0 IS AT LOW Y. The board is nearly symmetric, so a mirrored view reads
// as a wrong black-key layout (the C#D# pair and F#G#A# triplet swap places).
// A physical notch at the key-0 end removes the ambiguity, both on screen and
// on the bench when wiring 18 switches in the right order.
mark_size   = 8;     // notch cut into the board's front-left corner

// ---------------- Worst-case switch travel (datasheet tolerances) -----
travel_min   = mx_travel  - mx_travel_tol;    // 3.3 — earliest bottom-out
actuate_max  = mx_actuate + mx_actuate_tol;   // 2.1 — latest actuation

// ---------------- Lever arms and the self-actuation limit -------------
// (plunger_arm is defined with the derived heights — it is needed there.)
static_gf    = key_mass_g * com_arm / plunger_arm;  // key weight felt at the stem
max_key_g    = mx_preload_gf * plunger_arm / com_arm;  // heaviest safe key

// =====================================================================
// Sanity checks — these run for EVERY file that includes this one, so a
// bad edit is caught no matter which route you happen to have open.
// =====================================================================
echo(str("plate top ", mx_plate_z, " | stem top ", stem_top_z, " | pivot ", pivot_z,
         " | stop ", stop_top, " | plunger ", plunger_len, " | key top ", key_top_z));
echo(str("key top above TABLE = ", key_top_z + foot_h, " mm (on ", foot_h, " mm feet)"));
echo(str("press ", mx_press, " mm: actuates by ", actuate_max,
         " (margin ", mx_press - actuate_max, "), bottoms at ", travel_min,
         " (margin ", travel_min - mx_press, ")"));
echo(str("key ", key_mass_g, " g -> ", static_gf, " gf at stem; limit is ",
         mx_preload_gf, " gf, i.e. a key under ", max_key_g, " g"));

if (plunger_len < 2)
    echo("*** WARNING: plunger_len too short — raise hinge_h ***");
if (mx_press >= travel_min)
    echo("*** WARNING: press exceeds the worst-case travel — the SWITCH would ",
         "take the finger overshoot instead of the stops. Reduce mx_press. ***");
if (mx_press <= actuate_max)
    echo("*** WARNING: press may not reach actuation on a worst-case switch ***");
if (static_gf >= mx_preload_gf)
    echo("*** WARNING: the key outweighs the switch's guaranteed return force — ",
         "it will sag onto the stem and self-trigger. Keep the key under ",
         max_key_g, " g (print at low infill). ***");
if (contact_x >= front_clear)
    echo("*** WARNING: contact_x is inside the BLACK KEY zone — the fingertip ",
         "will collide with a black key. Keep it below ", front_clear, " mm ***");

// ---------------- Switch fit checks (datasheet-driven) ----------------
echo(str("housing top ", housing_top_z, " | cross base ", shoulder_z,
         " | stem top ", stem_top_z, " | black socket mouth ", blk_socket_z));
echo(str("stop binds at r = ", stop_r_lead, " (plunger at ", plunger_arm,
         ") -> plunger travels ", mx_press, " mm, as intended"));
echo(str("stop gap ", stop_clear, " vs housing ", mx_housing_w, " x ",
         mx_housing_d, " -> ", (stop_clear - mx_housing_w)/2,
         " mm per side in the worst rotation (fits either way round)"));

// The switch is lowered between the stops to reach the plate, so the gap has
// to pass the WIDE axis. At 15.0 it did not, and the switch could only be
// fitted one way round — with 0.55 mm per side on a printed part.
if (stop_clear < mx_housing_w)
    echo("*** WARNING: stop clearance ", stop_clear, " is under the ",
         mx_housing_w, " mm housing, so the switch either will not fit at all ",
         "or fits only in one rotation. Widen stop_clear. ***");
// A keycap socket placed above the cross grips nothing.
if (blk_socket_z + mx_cross_h > stem_top_z + 0.001)
    echo("*** WARNING: the black keycap socket starts above the cross base (",
         shoulder_z, ") — it would sit on the stem tip and pull straight off ***");
// ...and the cap must clear the housing for its whole travel.
if (blk_step_z - housing_top_z < blk_travel)
    echo("*** WARNING: the black keycap's full-width section reaches the switch ",
         "housing after only ", blk_step_z - housing_top_z, " mm — less than the ",
         blk_travel, " mm of travel it needs ***");
if (blk_boss_w >= mx_well_w)
    echo("*** WARNING: black keycap boss ", blk_boss_w, " will not enter the ",
         mx_well_w, " mm housing opening — the key will jam short of actuation ***");
// The clips spring out to mx_clip_w +/-0.5 once through the plate. The relief
// under the plate has to clear the WORST CASE, or they never latch.
if (mx_cut + 2 < mx_clip_w + 0.5)
    echo("*** WARNING: relief under the plate is ", mx_cut + 2, " but the clips ",
         "reach ", mx_clip_w + 0.5, " worst case — they cannot latch ***");
// The socket must be at least as big as the cross in both axes, or the black
// keycap will not go on at all.
if (mx_mount_cross <= mx_cross_w || mx_mount_th <= mx_cross_th)
    echo("*** WARNING: keycap socket ", mx_mount_cross, " x ", mx_mount_th,
         " is not larger than the cross ", mx_cross_w, " x ", mx_cross_th, " ***");
// TT = PT + OT, so the two worst cases the checks above use cannot co-occur.
echo(str("worst-case corner check: PT max ", actuate_max, " forces TT >= ",
         actuate_max + mx_overtravel, ", and TT min ", travel_min,
         " forces PT <= ", travel_min - mx_overtravel,
         " — press ", mx_press, " clears both by >= ",
         min(mx_press - (travel_min - mx_overtravel),
             (actuate_max + mx_overtravel) - mx_press)));
