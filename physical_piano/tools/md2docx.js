// Generic Markdown -> DOCX converter for the physical piano docs.
// Handles: ATX headings, paragraphs, bullet/numbered lists, tables (incl.
// alignment row), fenced code, blockquotes, HR, and inline **bold**, *italic*,
// `code`, [text](url). Deliberately small — it only needs to cover what these
// documents actually use.
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ExternalHyperlink, AlignmentType,
} = require("docx");
const fs = require("fs");
const path = require("path");

const PAGE_W = 12240, PAGE_H = 15840, MARGIN = 1080;
const CONTENT_W = PAGE_W - 2 * MARGIN;
const INK = "1A1A1A", MUTED = "5C5C5C", RULE = "D8D8D8", ACCENT = "6B4D0F", HEAD_FILL = "F3EEE3";
const thin = { style: BorderStyle.SINGLE, size: 2, color: RULE };
const cellBorders = { top: thin, bottom: thin, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } };

// Backslash-escaped characters are swapped for private-use codepoints BEFORE
// the markup scan, so \* is removed from the text the italic rule sees and
// cannot pair with another asterisk. push() swaps them back on the way out.
// Marking them in place is not enough - the character itself must leave the
// string, or the surviving pair still reads as markup.
const ESC_MAP = { "*": "\uE001", "_": "\uE002", "`": "\uE003", "~": "\uE004",
                  "[": "\uE005", "]": "\uE006", "\\": "\uE007" };
const UNESC = Object.fromEntries(Object.entries(ESC_MAP).map(([k, v]) => [v, k]));

// ---- inline markdown -> TextRun[] ----
function inline(md, base = {}) {
  const runs = [];
  md = md.replace(/\\([*_`~\[\]\\])/g, (_, c) => ESC_MAP[c]);
  const re = /(\[([^\]]+)\]\(([^)]+)\))|(\*\*([^*]+)\*\*)|(`([^`]+)`)|(\*([^*]+)\*)|(~~([^~]+)~~)/g;
  let last = 0, m;
  const push = (t, o = {}) => { t = t.replace(/[\uE001-\uE007]/g, (c) => UNESC[c]); if (t) runs.push(new TextRun({ text: t, size: 19, color: INK, ...base, ...o })); };
  while ((m = re.exec(md)) !== null) {
    push(md.slice(last, m.index));
    if (m[1]) {
      runs.push(new ExternalHyperlink({
        link: m[3],
        children: [new TextRun({ text: m[2], size: 19, color: ACCENT, underline: { type: "single" }, ...base })],
      }));
    } else if (m[4]) push(m[5], { bold: true });
    else if (m[6]) push(m[7], { font: "Consolas", size: 17, color: "7A3E00" });
    else if (m[8]) push(m[9], { italics: true });
    else if (m[10]) push(m[11], { strike: true, color: MUTED });
    last = re.lastIndex;
  }
  push(md.slice(last));
  return runs.length ? runs : [new TextRun({ text: "", size: 19 })];
}

const stripFmt = (s) => s.replace(/\*\*|\*|`|~~/g, "").trim();
const isSep = (l) => /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(l) && l.includes("-");
const cells = (l) => l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());

function tableFrom(lines, widths) {
  const header = cells(lines[0]);
  const n = header.length;
  const w = widths || Array(n).fill(Math.floor(CONTENT_W / n));
  const rows = [new TableRow({
    tableHeader: true, cantSplit: true,
    children: header.map((h, i) => new TableCell({
      width: { size: w[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: "auto", fill: HEAD_FILL },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      borders: { top: thin, bottom: { style: BorderStyle.SINGLE, size: 4, color: "B8AE95" }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
      children: [new Paragraph({ children: [new TextRun({ text: stripFmt(h), bold: true, size: 15, color: MUTED, allCaps: true, characterSpacing: 10 })] })],
    })),
  })];
  for (let r = 2; r < lines.length; r++) {
    const c = cells(lines[r]);
    while (c.length < n) c.push("");
    rows.push(new TableRow({
      cantSplit: true,
      children: c.slice(0, n).map((t, i) => new TableCell({
        width: { size: w[i], type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 100, right: 100 },
        borders: cellBorders,
        children: [new Paragraph({ children: inline(t) })],
      })),
    }));
  }
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: w, rows });
}

function convert(mdPath, outPath) {
  const src = fs.readFileSync(mdPath, "utf8").split(/\r?\n/);
  const body = [];
  let i = 0;
  while (i < src.length) {
    const line = src[i];

    if (/^\s*$/.test(line)) { i++; continue; }

    if (/^```/.test(line)) {                       // fenced code
      i++; const buf = [];
      while (i < src.length && !/^```/.test(src[i])) buf.push(src[i++]);
      i++;
      buf.forEach((t) => body.push(new Paragraph({
        spacing: { after: 0 },
        shading: { type: ShadingType.CLEAR, color: "auto", fill: "F5F3EE" },
        children: [new TextRun({ text: t || " ", font: "Consolas", size: 16, color: INK })],
      })));
      body.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      continue;
    }

    if (/^---+\s*$/.test(line)) {                  // horizontal rule
      body.push(new Paragraph({ spacing: { before: 120, after: 120 }, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE } }, children: [] }));
      i++; continue;
    }

    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      const lvl = h[1].length;
      const sizes = { 1: 34, 2: 25, 3: 21, 4: 19 };
      body.push(new Paragraph({
        heading: [null, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3, HeadingLevel.HEADING_4][lvl],
        keepNext: true,
        spacing: { before: lvl === 1 ? 0 : 300, after: 120 },
        border: lvl <= 2 ? { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } } : undefined,
        children: inline(h[2], { bold: true, size: sizes[lvl] }),
      }));
      i++; continue;
    }

    if (line.includes("|") && i + 1 < src.length && isSep(src[i + 1])) {
      const buf = [];
      while (i < src.length && src[i].includes("|")) buf.push(src[i++]);
      body.push(tableFrom(buf));
      body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
      continue;
    }

    const q = line.match(/^>\s?(.*)$/);
    if (q) {
      const buf = [q[1]]; i++;
      while (i < src.length && /^>\s?/.test(src[i])) buf.push(src[i++].replace(/^>\s?/, ""));
      body.push(new Paragraph({
        spacing: { before: 80, after: 200 },
        indent: { left: 160 },
        border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 8 } },
        children: inline(buf.join(" ")),
      }));
      continue;
    }

    const li = line.match(/^\s*([-*]|\d+\.)\s+(.*)$/);
    if (li) {
      const ordered = /\d/.test(li[1]);
      const buf = [];
      while (i < src.length) {
        const m2 = src[i].match(/^\s*([-*]|\d+\.)\s+(.*)$/);
        if (!m2) {
          if (/^\s{2,}\S/.test(src[i]) && buf.length) { buf[buf.length - 1] += " " + src[i].trim(); i++; continue; }
          break;
        }
        buf.push(m2[2]); i++;
      }
      buf.forEach((t, k) => body.push(new Paragraph({
        spacing: { after: 60 },
        indent: { left: 360, hanging: 200 },
        children: [new TextRun({ text: ordered ? `${k + 1}.  ` : "•  ", size: 19, color: MUTED }), ...inline(t)],
      })));
      body.push(new Paragraph({ spacing: { after: 100 }, children: [] }));
      continue;
    }

    const buf = [line]; i++;                        // paragraph
    while (i < src.length && !/^\s*$/.test(src[i]) && !/^(#{1,4}\s|>|```|---+\s*$)/.test(src[i])
           && !/^\s*([-*]|\d+\.)\s/.test(src[i]) && !src[i].includes("|")) buf.push(src[i++]);
    body.push(new Paragraph({ spacing: { after: 180 }, children: inline(buf.join(" ")) }));
  }

  const doc = new Document({
    styles: { default: { document: { run: { font: "Calibri", size: 19, color: INK } } } },
    sections: [{
      properties: { page: { size: { width: PAGE_W, height: PAGE_H }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
      children: body,
    }],
  });
  return Packer.toBuffer(doc).then((b) => { fs.writeFileSync(outPath, b); console.log("wrote", path.basename(outPath)); });
}

const [, , ...args] = process.argv;
(async () => { for (let k = 0; k < args.length; k += 2) await convert(args[k], args[k + 1]); })();
