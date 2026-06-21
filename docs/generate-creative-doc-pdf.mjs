/**
 * 将创意文档 Markdown 转为 PDF（支持中文）
 * 用法: node docs/generate-creative-doc-pdf.mjs
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

const mdPath = path.join(__dirname, 'StoryCraft_创意文档.md');
const outPath = path.join(__dirname, 'StoryCraft_创意文档.pdf');

const FONT_CANDIDATES = [
  'C:\\Windows\\Fonts\\simhei.ttf',
  'C:\\Windows\\Fonts\\simkai.ttf',
  'C:\\Windows\\Fonts\\simfang.ttf',
  'C:\\Windows\\Fonts\\msyh.ttf',
  'C:\\Windows\\Fonts\\Deng.ttf',
  'C:\\Windows\\Fonts\\Dengb.ttf',
];

function findFont() {
  for (const p of FONT_CANDIDATES) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error('未找到中文字体，请安装微软雅黑或黑体');
}

function parseMarkdown(md) {
  const blocks = [];
  const lines = md.split(/\r?\n/);
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith('# ')) {
      blocks.push({ type: 'h1', text: line.slice(2).trim() });
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      blocks.push({ type: 'h2', text: line.slice(3).trim() });
      i++;
      continue;
    }
    if (line.startsWith('### ')) {
      blocks.push({ type: 'h3', text: line.slice(4).trim() });
      i++;
      continue;
    }
    if (line.startsWith('#### ')) {
      blocks.push({ type: 'h4', text: line.slice(5).trim() });
      i++;
      continue;
    }
    if (line.trim() === '---') {
      blocks.push({ type: 'hr' });
      i++;
      continue;
    }
    if (line.startsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: 'table', rows: tableLines });
      continue;
    }
    if (/^\d+\.\s/.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s/, '').trim());
        i++;
      }
      blocks.push({ type: 'ol', items });
      continue;
    }
    if (line.trim() === '') {
      i++;
      continue;
    }

    const para = [];
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].startsWith('#') &&
      !lines[i].startsWith('|') &&
      !/^\d+\.\s/.test(lines[i]) &&
      lines[i].trim() !== '---'
    ) {
      para.push(lines[i]);
      i++;
    }
    if (para.length) {
      blocks.push({ type: 'p', text: para.join(' ') });
    }
  }

  return blocks;
}

function stripBold(text) {
  return text.replace(/\*\*(.+?)\*\*/g, '$1');
}

async function main() {
  const PDFDocument = require('pdfkit');
  const md = fs.readFileSync(mdPath, 'utf8');
  const blocks = parseMarkdown(md);
  const fontPath = findFont();

  const doc = new PDFDocument({
    size: 'A4',
    margins: { top: 56, bottom: 56, left: 56, right: 56 },
    info: {
      Title: 'StoryCraft 创意文档',
      Author: 'StoryCraft',
      Subject: '通义千问 手机端创意 AI 参赛文档',
    },
  });

  const stream = fs.createWriteStream(outPath);
  doc.pipe(stream);

  doc.registerFont('cn', fontPath);
  doc.font('cn');

  const pageWidth = doc.page.width - doc.page.margins.left - doc.page.margins.right;
  const bottomLimit = doc.page.height - doc.page.margins.bottom;

  function ensureSpace(h) {
    if (doc.y + h > bottomLimit) doc.addPage();
  }

  function writeParagraph(text, opts = {}) {
    const fontSize = opts.fontSize ?? 11;
    const lineGap = opts.lineGap ?? 4;
    doc.fontSize(fontSize).fillColor('#222');
    const clean = stripBold(text);
    const h = doc.heightOfString(clean, { width: pageWidth, lineGap });
    ensureSpace(Math.min(h, 120) + 8);
    doc.text(clean, { width: pageWidth, lineGap, align: opts.align ?? 'left' });
    doc.moveDown(opts.after ?? 0.4);
  }

  function writeHeading(text, level) {
    const sizes = { h1: 20, h2: 16, h3: 13, h4: 12 };
    const after = { h1: 0.8, h2: 0.6, h3: 0.5, h4: 0.4 };
    const size = sizes[level] ?? 12;
    ensureSpace(size + 16);
    doc.fontSize(size).fillColor('#111');
    doc.text(stripBold(text), { width: pageWidth });
    doc.moveDown(after[level] ?? 0.4);
  }

  function writeTable(rows) {
    const parsed = rows
      .filter((r) => !/^\|[\s\-:|]+\|$/.test(r.trim()))
      .map((r) =>
        r
          .split('|')
          .slice(1, -1)
          .map((c) => stripBold(c.trim()))
      );

    if (!parsed.length) return;

    const colCount = parsed[0].length;
    const colWidth = pageWidth / colCount;
    const cellPad = 4;
    const fontSize = 9;

    doc.fontSize(fontSize);

    for (let ri = 0; ri < parsed.length; ri++) {
      const row = parsed[ri];
      let rowHeight = 0;
      for (const cell of row) {
        const h = doc.heightOfString(cell, {
          width: colWidth - cellPad * 2,
          lineGap: 2,
        });
        rowHeight = Math.max(rowHeight, h + cellPad * 2);
      }
      ensureSpace(rowHeight + 4);

      const y0 = doc.y;
      let x = doc.page.margins.left;

      for (const cell of row) {
        if (ri === 0) doc.fillColor('#333');
        else doc.fillColor('#222');
        doc
          .rect(x, y0, colWidth, rowHeight)
          .strokeColor('#ccc')
          .lineWidth(0.5)
          .stroke();
        doc.text(cell, x + cellPad, y0 + cellPad, {
          width: colWidth - cellPad * 2,
          lineGap: 2,
        });
        x += colWidth;
      }

      doc.y = y0 + rowHeight;
    }
    doc.moveDown(0.6);
  }

  for (const block of blocks) {
    switch (block.type) {
      case 'h1':
      case 'h2':
      case 'h3':
      case 'h4':
        writeHeading(block.text, block.type);
        break;
      case 'hr':
        ensureSpace(12);
        doc
          .moveTo(doc.page.margins.left, doc.y)
          .lineTo(doc.page.width - doc.page.margins.right, doc.y)
          .strokeColor('#ddd')
          .stroke();
        doc.moveDown(0.6);
        break;
      case 'table':
        writeTable(block.rows);
        break;
      case 'ol':
        block.items.forEach((item, idx) => {
          writeParagraph(`${idx + 1}. ${item}`, { fontSize: 11 });
        });
        break;
      case 'p':
        writeParagraph(block.text);
        break;
      default:
        break;
    }
  }

  doc.end();

  await new Promise((resolve, reject) => {
    stream.on('finish', resolve);
    stream.on('error', reject);
  });

  console.log(`PDF 已保存: ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
