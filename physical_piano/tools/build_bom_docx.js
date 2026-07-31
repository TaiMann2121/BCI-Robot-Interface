const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ExternalHyperlink, AlignmentType, VerticalAlign,
} = require("docx");
const fs = require("fs");

// ---- US Letter, 1" margins ----
const PAGE_W = 12240, PAGE_H = 15840, MARGIN = 1440;
const CONTENT_W = PAGE_W - 2 * MARGIN; // 9360

const INK = "1A1A1A";
const MUTED = "5C5C5C";
const RULE = "D8D8D8";
const ACCENT = "6B4D0F";
const HEAD_FILL = "F3EEE3";

const dot = () => new TextRun({ text: "  ·  ", size: 17, color: MUTED });
const orEquiv = () => new TextRun({ text: "  — or equivalent", size: 15, italics: true, color: MUTED });

const link = (text, url) =>
  new ExternalHyperlink({
    link: url,
    children: [new TextRun({ text, style: "Hyperlink" })],
  });

const cell = (children, { width, fill, valign = VerticalAlign.TOP, borders } = {}) =>
  new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { type: ShadingType.CLEAR, color: "auto", fill } : undefined,
    verticalAlign: valign,
    margins: { top: 90, bottom: 90, left: 100, right: 100 },
    children,
    borders,
  });

const p = (text, opts = {}) =>
  new Paragraph({
    spacing: { after: opts.after ?? 0 },
    children: [
      new TextRun({
        text,
        bold: opts.bold,
        italics: opts.italics,
        size: opts.size ?? 18,
        color: opts.color ?? INK,
      }),
    ],
  });

const thinBorder = { style: BorderStyle.SINGLE, size: 2, color: RULE };
const cellBorders = { top: thinBorder, bottom: thinBorder, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } };

function headerRow(labels, widths) {
  return new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: labels.map((label, i) =>
      cell(
        [new Paragraph({
          children: [new TextRun({ text: label, bold: true, size: 15, color: MUTED, allCaps: true, characterSpacing: 10 })],
        })],
        { width: widths[i], fill: HEAD_FILL, borders: { top: thinBorder, bottom: { style: BorderStyle.SINGLE, size: 4, color: "B8AE95" }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } } }
      )
    ),
  });
}

function itemRow({ item, desc, qty, price, sourceRuns }, widths) {
  const itemParas = [p(item, { bold: true, size: 18 })];
  if (desc) itemParas.push(p(desc, { size: 15, color: MUTED, after: 0 }));
  return new TableRow({
    cantSplit: true,
    children: [
      cell(itemParas, { width: widths[0], borders: cellBorders }),
      cell([new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: qty, size: 18, color: INK })] })], { width: widths[1], borders: cellBorders }),
      cell([new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: price, size: 18, color: INK })] })], { width: widths[2], borders: cellBorders }),
      cell([new Paragraph({ children: sourceRuns })], { width: widths[3], borders: cellBorders }),
    ],
  });
}

function sectionTable(rows, colWidths = [4680, 900, 1300, 2480]) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow(["Item", "Qty", "Price", "Source"], colWidths), ...rows.map((r) => itemRow(r, colWidths))],
  });
}

function h2(num, text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    keepNext: true,
    spacing: { before: 320, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
    children: [
      new TextRun({ text: num + "  ", font: "Consolas", size: 18, color: MUTED }),
      new TextRun({ text, bold: true, size: 24, color: INK }),
    ],
  });
}

function note(text) {
  return new Paragraph({ spacing: { after: 160 }, keepNext: true, children: [new TextRun({ text, size: 17, color: MUTED, italics: true })] });
}

// ---- Summary card row (as a borderless 3-col table) ----
function summaryCards() {
  const w = CONTENT_W / 3;
  const card = (label, value, sub, accent) =>
    cell(
      [
        new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: label, size: 14, color: accent ? ACCENT : MUTED, allCaps: true, bold: true, characterSpacing: 10 })] }),
        new Paragraph({ spacing: { after: 20 }, children: [new TextRun({ text: value, bold: true, size: 30, color: accent ? ACCENT : INK, font: "Consolas" })] }),
        new Paragraph({ children: [new TextRun({ text: sub, size: 15, color: accent ? ACCENT : MUTED })] }),
      ],
      { width: w, fill: accent ? "F6EFDE" : "F7F7F5", borders: { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder } }
    );
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [w, w, w],
    rows: [
      new TableRow({
        children: [
          card("Parts to purchase", "~$135", "Sections 1–3, solder path", true),
          card("Fabrication", "$176–315", "Billed by TechSpark", false),
          card("Keys", "11 + 7", "White, plus decorative black", false),
        ],
      }),
    ],
  });
}

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 20, color: INK } },
    },
    paragraphStyles: [
      { id: "Hyperlink", name: "Hyperlink", basedOn: "Normal", run: { color: ACCENT, underline: { type: "single" } } },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: PAGE_W, height: PAGE_H },
          margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
        },
      },
      children: [
        new Paragraph({ children: [new TextRun({ text: "BCI ARM AND HAND PIANO TASK", size: 16, color: MUTED, bold: true, characterSpacing: 14 })], spacing: { after: 60 } }),
        new Paragraph({
          children: [new TextRun({ text: "Physical Piano — Parts to Purchase", bold: true, size: 40, color: INK })],
          spacing: { after: 80 },
        }),
        new Paragraph({
          children: [new TextRun({ text: "Shopping list for the 11-key physical piano that replaces the toy playmat. Every dimension in the design has been measured against the robot on the bench.", size: 19, color: MUTED })],
          spacing: { after: 240 },
        }),

        summaryCards(),

        new Paragraph({
          spacing: { before: 220, after: 240 },
          border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 8 } },
          indent: { left: 100 },
          children: [
            new TextRun({ text: "Suggested first step:  ", bold: true, size: 18, color: INK }),
            new TextRun({ text: "order Sections 1–3 now. Electronics and mechanical fabrication are independent — with these parts on hand, the switches, sound, and tuning software can be built and tested on a breadboard while the keys are still being made at TechSpark.", size: 18, color: MUTED }),
          ],
        }),

        h2("01", "Key Switches"),
        note("MX-style linear switches. Each supplies the electrical contact, the return spring, and 4 mm of travel in one part. They actuate at ~45 gf — far below the robot’s weakest finger, measured at 362 gf."),
        sectionTable([
          {
            item: "Kailh linear red switches, 10-pack",
            desc: "MX-compatible. Two packs covers 11 keys plus 9 spares.",
            qty: "2 packs",
            price: "$12",
            sourceRuns: [link("Adafruit #4952", "https://www.adafruit.com/product/4952")],
          },
          {
            item: "Cherry MX Red 45g, 10-pack",
            desc: "Equivalent alternative if Kailh is out of stock.",
            qty: "—",
            price: "$24",
            sourceRuns: [link("MechanicalKeyboards", "https://mechanicalkeyboards.com/products/cherry-mx-red-45g-linear"), new TextRun({ text: "  ·  ", size: 18, color: MUTED }), link("Amazon", "https://www.amazon.com/Original-Cherry-Switches-Mechanical-Keyboard/dp/B09J3GSY6Y")],
          },
        ]),

        h2("02", "Microcontroller and Sound"),
        note("The Arduino reads the 11 keys and plays one tone per key. Pitches are set from a computer over USB and saved on the board."),
        sectionTable([
          {
            item: "Arduino Uno R3",
            desc: "Official board.",
            qty: "1",
            price: "$28",
            sourceRuns: [link("Arduino Store", "https://store-usa.arduino.cc/products/arduino-uno-rev3"), new TextRun({ text: "  ·  ", size: 18, color: MUTED }), link("SparkFun", "https://www.sparkfun.com/arduino-uno-r3.html")],
          },
          {
            item: "Uno R3 compatible board",
            desc: "Budget option, functionally identical.",
            qty: "—",
            price: "$13",
            sourceRuns: [link("ELEGOO", "https://us.elegoo.com/products/elegoo-uno-r3-board")],
          },
          {
            item: "Piezo buzzer",
            desc: "Driven directly by the Arduino; no amp needed.",
            qty: "1",
            price: "$2",
            sourceRuns: [link("Adafruit #160", "https://www.adafruit.com/product/160")],
          },
          {
            item: "Enclosed piezo element",
            desc: "Optional, louder than the bare buzzer.",
            qty: "1",
            price: "$3",
            sourceRuns: [link("Adafruit #1739", "https://www.adafruit.com/product/1739")],
          },
        ]),

        h2("03", "Wiring and Assembly"),
        note("Bring up the firmware on a breadboard first (no soldering, fully reversible), then solder a permanent perfboard build — the keys are struck repeatedly at 362–520 gf, which can work a breadboard's connections loose over time."),
        sectionTable([
          { item: "Full-size solderless breadboard", desc: "Bring-up and testing only.", qty: "1", price: "$5", sourceRuns: [link("Adafruit #239", "https://www.adafruit.com/product/239")] },
          { item: "USB A–B cable", desc: "Powers the Arduino; carries the tuning connection. Likely already in lab stock.", qty: "1", price: "$6", sourceRuns: [link("Adafruit #62", "https://www.adafruit.com/product/62"), dot(), link("Arduino Store", "https://store-usa.arduino.cc/products/usb-2-0-cable-type-a-b")] },
          { item: "Hookup wire, 22 AWG stranded", desc: "11 signal lines plus a common ground, six colors.", qty: "1 set", price: "$15", sourceRuns: [link("Adafruit #3111", "https://www.adafruit.com/product/3111"), dot(), link("SparkFun", "https://www.sparkfun.com/hook-up-wire-assortment-stranded-22-awg.html")] },
          { item: "Perfboard", desc: "Ground bus for the 11 switch commons — final build.", qty: "1", price: "$11", sourceRuns: [link("Adafruit #1606", "https://www.adafruit.com/product/1606")] },
          { item: "Beginner soldering iron kit", desc: "Iron, stand, solder, sucker, wick.", qty: "1", price: "$20", sourceRuns: [link("Amazon", "https://www.amazon.com/Beginner-Soldering-LCDalternatives-v3-solder/dp/B00SH2MOB6")] },
          { item: "K&S 3 mm brass rod, 3-pack", desc: "Hinge pins for the key levers — brass works as well as steel here and is easier to cut.", qty: "1", price: "$8", sourceRuns: [link("Amazon", "https://www.amazon.com/Round-Brass-Rod-Diameter-Engineering/dp/B013Y2EACO")] },
          { item: "M3 nut/bolt/washer assortment kit", desc: "Screws and nuts for joining base sections.", qty: "1 set", price: "$12", sourceRuns: [link("Amazon", "https://www.amazon.com/Assortment-Stainless-Washers-Assorted-Machine/dp/B0BC24J6SS")] },
          { item: "Gorilla super glue (cyanoacrylate)", desc: "Sets the black keys into their locating grooves.", qty: "1", price: "$7", sourceRuns: [link("Amazon", "https://www.amazon.com/Gorilla-Super-Glue-Gram-Clear/dp/B00KPYB05A")] },
        ]),
        new Paragraph({
          spacing: { after: 240 },
          keepNext: true,
          children: [
            new TextRun({ text: "No-solder alternative:  ", bold: true, size: 17, color: INK }),
            new TextRun({ text: "skip the perfboard and soldering kit above and use a screw-terminal shield instead — each wire clamps under a screw. Less permanent than solder but far more robust than a bare breadboard.  ", size: 17, color: MUTED }),
            link("Amazon, ~$15", "https://www.amazon.com/Screw-Terminal-Shield-Arduino-Uno/dp/B0F5NVVY1Q"),
          ],
        }),

        h2("04", "Fabrication — Not a Purchase"),
        note("Keys, base, and black keys are made at CMU TechSpark and billed to a university account. PLA is $0.64/gram."),
        sectionTable(
          [
            { item: "All parts 3D printed", desc: "~490 g. Base prints as three tiles — the printers are only 10″ wide — so the 50 mm key pitch must survive two joins.", qty: "—", price: "$315", sourceRuns: [new TextRun({ text: "", size: 17 })] },
            { item: "Laser-cut base + printed keys", desc: "~275 g printed, plus laser time. Cuts all 11 switch holes in one operation on one sheet, with no tile seams.", qty: "—", price: "$176 + time", sourceRuns: [new TextRun({ text: "", size: 17 })] },
          ],
          [5560, 900, 1300, 1600]
        ),
        note("Which approach we use is the main question for the TechSpark consult. The case for laser cutting is accuracy — the arm is calibrated to that 50 mm pitch. On cost it is a modest win, not a dramatic one: laser machine time is billed hourly and is not published, so the net saving is likely $30–80 rather than half."),

        new Paragraph({
          spacing: { before: 260 },
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: RULE, space: 8 } },
          children: [new TextRun({ text: "Prices are approximate and exclude tax and shipping; confirm at checkout. Full specification and fabrication plan are in the shared project folder alongside this document.", size: 15, color: MUTED, italics: true })],
        }),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Physical_Piano_BOM.docx", buf);
  console.log("wrote Physical_Piano_BOM.docx");
});
