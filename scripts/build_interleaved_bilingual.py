#!/usr/bin/env python3
"""
Regenerate CXL chapter bilingual PDFs with interleaved quality layout:

  - Each English body paragraph is immediately followed by its Chinese translation
  - Section/TOC titles are kept in English only (not translated)
  - Embedded images and vector figures/tables are preserved (page graphics render)
  - Contents / cover chapters keep original pages (no body translation)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import traceback
import unicodedata
from pathlib import Path

import fitz
from deep_translator import GoogleTranslator

ROOT = Path("/workspace")
SRC_PDF = ROOT / "CXL-Specification_rev3p2_ver1p0_2024October2_evalcopy.pdf"
CHAPTER_MAP = ROOT / "scripts" / "chapter_map.json"
CACHE_DIR = Path("/tmp/cxl_zh_cache_v2")
OUT_DIR = ROOT / "output" / "chapters_bilingual"
ARTIFACT_DIR = Path("/opt/cursor/artifacts") / "chapters_bilingual"
FONT_TTF = Path("/tmp/wqy-microhei.ttf")

SKIP_CHAPTER_TRANSLATE = {"00_cover", "00_contents"}  # original pages only

HEADER_RE = re.compile(
    r"^(Evaluation Copy|October 2, 2024|Revision 3\.2, Version 1\.0|"
    r"Compute Express Link Specification)$"
)
FOOTER_FRAG_RE = re.compile(
    r"(October 2, 2024|Compute Express Link Specification|Revision 3\.2, Version 1\.0)"
)
PAGE_NUM_RE = re.compile(r"^\d{1,4}$")
FIGURE_TABLE_CAP_RE = re.compile(r"^(Figure|Table)\s+\d+-\d+\.", re.I)
# Diagram/UI short labels — keep via page graphics, do not translate as body
LABEL_LIKE_RE = re.compile(
    r"^("
    r"[A-Za-z0-9 ._/+\-()]{1,48}"
    r")$"
)


def ensure_font() -> str:
    if FONT_TTF.exists() and FONT_TTF.stat().st_size > 1000:
        return str(FONT_TTF)
    from fontTools.ttLib import TTCollection

    src = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
    col = TTCollection(str(src))
    col.fonts[0].save(str(FONT_TTF))
    return str(FONT_TTF)


class Translator:
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.gt = GoogleTranslator(source="en", target="zh-CN")
        self.hits = 0
        self.misses = 0

    def translate(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""
        # Skip pure symbols / very short non-linguistic
        letters = re.sub(r"[^A-Za-z]+", "", text)
        if len(letters) < 8:
            return text
        key = hashlib.sha1(text.encode("utf-8")).hexdigest()
        cp = CACHE_DIR / f"{key}.txt"
        if cp.exists():
            self.hits += 1
            return cp.read_text(encoding="utf-8")
        self.misses += 1
        # Chunk long paragraphs
        chunks = []
        if len(text) <= 4500:
            parts = [text]
        else:
            parts = []
            buf = []
            n = 0
            for sent in re.split(r"(?<=[.!?])\s+", text):
                if n + len(sent) + 1 > 4500 and buf:
                    parts.append(" ".join(buf))
                    buf = [sent]
                    n = len(sent)
                else:
                    buf.append(sent)
                    n += len(sent) + 1
            if buf:
                parts.append(" ".join(buf))
        for part in parts:
            zh = None
            for attempt in range(5):
                try:
                    zh = self.gt.translate(part)
                    break
                except Exception as e:
                    time.sleep(1.2 * (attempt + 1))
                    last = e
            if zh is None:
                zh = f"[翻译失败] {part}"
            chunks.append(unicodedata.normalize("NFKC", zh))
            time.sleep(0.03)
        out = "".join(chunks) if len(chunks) == 1 else "\n".join(chunks)
        # Prefer joining without extra newlines for sentence chunks
        if len(parts) > 1:
            out = "".join(chunks)
        out = unicodedata.normalize("NFKC", out)
        # Extra compatibility cleanups sometimes left by MT fonts
        out = (
            out.replace("\uf9ba", "了")
            .replace("\uf967", "不")
            .replace("\uf901", "更")
            .replace("\uf9ea", "了")
        )
        cp.write_text(out, encoding="utf-8")
        return out


def is_noise_line(s: str) -> bool:
    s = s.strip()
    if not s:
        return True
    if HEADER_RE.match(s):
        return True
    if PAGE_NUM_RE.match(s):
        return True
    if FOOTER_FRAG_RE.search(s) and len(s) < 80:
        return True
    if "Compute Express Link Specification" in s and len(s) < 60:
        return True
    return False


def is_heading(text: str) -> bool:
    t = text.strip()
    if FIGURE_TABLE_CAP_RE.match(t):
        return True  # captions stay EN-only
    if re.match(r"^\d+(\.\d+){0,5}\s+\S+", t) and len(t) <= 140:
        if t.endswith(".") and len(t) > 90:
            return False
        return True
    if re.match(r"^Appendix\s+[A-Z]\b", t):
        return True
    return False


def is_body_paragraph(text: str) -> bool:
    """Only real prose body — not diagram labels / table crumbs."""
    t = text.strip()
    if len(t) < 55:
        return False
    words = t.split()
    if len(words) < 8:
        return False
    # Must look like a sentence / prose
    if not re.search(r"[.:;]", t) and len(t) < 100:
        return False
    # Reject dotted TOC leaders
    if re.search(r"\.{4,}\s*\d+\s*$", t):
        return False
    # Reject if mostly ALLCAPS short tokens (register dumps)
    caps = sum(1 for w in words if w.isupper() and len(w) > 1)
    if caps >= max(4, len(words) * 0.6) and len(t) < 180:
        return False
    return True


def merge_block_text(block: dict, page_height: float) -> str:
    lines = []
    for line in block.get("lines", []):
        y0 = line["bbox"][1]
        # skip header/footer bands
        if y0 < 68 or y0 > page_height - 48:
            continue
        t = "".join(span["text"] for span in line["spans"]).strip()
        if t and not is_noise_line(t):
            # strip footer fragments accidentally concatenated
            t = FOOTER_FRAG_RE.sub("", t).strip(" |")
            if t:
                lines.append(t)
    if not lines:
        return ""
    out = lines[0]
    for ln in lines[1:]:
        if out.endswith("-") and ln and ln[0].islower():
            out = out[:-1] + ln
        else:
            out = out + " " + ln
    return re.sub(r"\s+", " ", out).strip()


def extract_page_items(page: fitz.Page, page_index: int, img_dir: Path) -> list[dict]:
    """Return ordered content items for one page."""
    items: list[dict] = []
    d = page.get_text("dict")
    blocks = sorted(d.get("blocks", []), key=lambda b: (round(b["bbox"][1], 1), b["bbox"][0]))
    drawings = page.get_drawings()
    has_graphics_ctx = len(drawings) >= 5 or bool(page.get_images())

    has_raster = False
    seen_para = set()
    for b in blocks:
        if b.get("type") == 1:  # image
            has_raster = True
            bbox = fitz.Rect(b["bbox"])
            if bbox.width < 40 or bbox.height < 40:
                continue
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), clip=bbox, alpha=False)
                path = img_dir / f"p{page_index+1}_img_{len(items)}.jpg"
                path.write_bytes(pix.tobytes("jpeg", jpg_quality=82))
                items.append({"type": "image", "path": str(path)})
            except Exception:
                continue
        else:
            text = merge_block_text(b, page.rect.height)
            if not text:
                continue
            if b["bbox"][1] < 70 and len(text) < 60 and not re.match(r"^\d", text):
                continue
            if is_heading(text):
                items.append({"type": "heading", "text": text})
                continue
            # Skip diagram/table fragment labels — preserved in page graphics
            if has_graphics_ctx and not is_body_paragraph(text):
                continue
            if not is_body_paragraph(text):
                # Outside graphics pages, still skip ultra-short labels
                if len(text) < 55:
                    continue
            key = text.lower()
            if key in seen_para:
                continue
            seen_para.add(key)
            items.append({"type": "para", "text": text})

    need_graphics = has_raster or len(drawings) >= 8
    if not need_graphics:
        if any(
            it.get("type") == "heading" and FIGURE_TABLE_CAP_RE.match(it["text"])
            for it in items
        ) and len(drawings) >= 3:
            need_graphics = True
    # Table-heavy pages often have many drawings
    if not need_graphics and len(drawings) >= 15:
        need_graphics = True

    if need_graphics:
        clip = fitz.Rect(36, 70, page.rect.width - 36, page.rect.height - 50)
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.55, 1.55), clip=clip, alpha=False)
            path = img_dir / f"p{page_index+1}_graphics.jpg"
            path.write_bytes(pix.tobytes("jpeg", jpg_quality=80))
            items.append(
                {
                    "type": "page_graphics",
                    "path": str(path),
                    "note": f"[Original page {page_index+1} figures/tables retained]",
                }
            )
        except Exception:
            pass

    return items


class DocWriter:
    def __init__(self, fontfile: str):
        self.fontfile = fontfile
        self.doc = fitz.open()
        self.page = None
        self.y = 0
        self.margin = 48
        self.width = 612
        self.height = 792
        self.bottom = 742
        self.content_w = self.width - 2 * self.margin

    def _new_page(self, header: str = ""):
        self.page = self.doc.new_page(width=self.width, height=self.height)
        self.page.insert_font(fontname="FCJK", fontfile=self.fontfile)
        # header
        self.page.draw_rect(fitz.Rect(0, 0, self.width, 28), color=None, fill=(0.12, 0.22, 0.38))
        if header:
            self.page.insert_text(
                (self.margin, 18),
                header[:110],
                fontname="FCJK",
                fontsize=8,
                color=(1, 1, 1),
            )
        self.y = 44

    def ensure_space(self, need: float, header: str):
        if self.page is None:
            self._new_page(header)
        if self.y + need > self.bottom:
            self._new_page(header)

    def add_cover(self, chapter: dict):
        self._new_page("CXL Spec Rev 3.2 · 中英对照（逐段）")
        y = 180
        lines = [
            ("Compute Express Link Specification", 16, (0.1, 0.2, 0.35)),
            ("Revision 3.2, Version 1.0", 11, (0.35, 0.4, 0.45)),
            ("", 8, None),
            (chapter["title"], 14, (0.1, 0.2, 0.35)),
            (chapter["title_zh"], 13, (0.08, 0.45, 0.42)),
            ("", 10, None),
            ("逐段中英对照译本（非官方）", 12, (0.2, 0.2, 0.2)),
            ("English paragraph → Chinese paragraph", 10, (0.4, 0.4, 0.4)),
            ("", 8, None),
            ("目录/章节标题保留英文；仅翻译正文。图片与图表版式保留。", 9, (0.35, 0.35, 0.35)),
            (f"源页码: {chapter['start']}–{chapter['end']}", 9, (0.35, 0.35, 0.35)),
        ]
        for text, size, color in lines:
            if not text:
                y += size + 6
                continue
            self.page.insert_text((self.margin, y), text, fontname="FCJK", fontsize=size, color=color)
            y += size + 12
        # Always start body on a fresh page after cover
        self._new_page(f"CXL Rev3.2 · {chapter['title']} · 逐段中英对照")

    def _textbox(self, text: str, fontsize: float, color, indent: float = 0) -> float:
        """Write wrapped text at self.y; returns height used (may span pages via ensure)."""
        rect = fitz.Rect(self.margin + indent, self.y, self.width - self.margin, self.bottom)
        # Probe
        remaining = text
        total_h = 0
        header = getattr(self, "header", "")
        while remaining:
            self.ensure_space(fontsize * 2 + 4, header)
            rect = fitz.Rect(self.margin + indent, self.y, self.width - self.margin, self.bottom)
            # Use insert_textbox; if overflow, binary-split text
            rc = self.page.insert_textbox(
                rect, remaining, fontname="FCJK", fontsize=fontsize, color=color, align=0
            )
            if rc >= 0:
                used = rect.height - rc
                self.y += used + 4
                total_h += used + 4
                break
            # overflow: split remaining roughly by capacity
            # Estimate chars that fit
            capacity = max(200, int((rect.height / (fontsize * 1.35)) * 55))
            if len(remaining) <= capacity:
                # force new page and retry
                self._new_page(header)
                continue
            # split at paragraph/sentence boundary
            cut = remaining.rfind(" ", 0, capacity)
            if cut < capacity // 3:
                cut = capacity
            piece = remaining[:cut].rstrip()
            remaining = remaining[cut:].lstrip()
            rc2 = self.page.insert_textbox(
                rect, piece, fontname="FCJK", fontsize=fontsize, color=color, align=0
            )
            used = rect.height - max(rc2, 0)
            self.y = self.bottom  # force new page next
            total_h += used
            self._new_page(header)
        return total_h

    def add_heading(self, text: str, header: str):
        self.header = header
        self.ensure_space(28, header)
        self.y += 6
        self._textbox(text, 11, (0.1, 0.22, 0.38))
        self.y += 2

    def add_en_zh(self, en: str, zh: str, header: str):
        self.header = header
        self.ensure_space(48, header)
        # English body
        self._textbox(en, 9.5, (0.1, 0.1, 0.12))
        # Chinese translation immediately below
        self._textbox(zh, 9.5, (0.05, 0.35, 0.32))
        # separator
        self.ensure_space(8, header)
        self.page.draw_line(
            fitz.Point(self.margin, self.y + 2),
            fitz.Point(self.width - self.margin, self.y + 2),
            color=(0.85, 0.88, 0.9),
            width=0.4,
        )
        self.y += 10

    def add_image(self, path: str, header: str, note: str = ""):
        self.header = header
        if not Path(path).exists():
            return
        max_w = self.content_w
        max_h = 460
        pm = fitz.Pixmap(path)
        iw, ih = pm.width, pm.height
        scale = min(max_w / iw, max_h / ih, 1.0)
        dw, dh = iw * scale, ih * scale
        self.ensure_space(min(dh, max_h) + 28, header)
        if note:
            self._textbox(note, 8, (0.4, 0.4, 0.4))
        rect = fitz.Rect(self.margin, self.y, self.margin + dw, self.y + dh)
        self.page.insert_image(rect, filename=path)
        self.y += dh + 10

    def insert_original_pages(self, src: fitz.Document, start: int, end: int):
        self.doc.insert_pdf(src, from_page=start - 1, to_page=end - 1)

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(path), deflate=True, garbage=3)
        self.doc.close()


def build_chapter(chapter: dict, src: fitz.Document, translator: Translator, fontfile: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"CXL_r3.2_{chapter['id']}_中英对照.pdf"
    print(f"\n=== {chapter['id']} ({chapter['pages']}p) ===", flush=True)

    writer = DocWriter(fontfile)
    header = f"CXL Rev3.2 · {chapter['title']} · 逐段中英对照"

    # Cover / Contents: keep original pages only
    if chapter["id"] in SKIP_CHAPTER_TRANSLATE:
        writer.add_cover(chapter)
        writer.insert_original_pages(src, chapter["start"], chapter["end"])
        writer.save(out_path)
        print(f"  saved original-passthrough {out_path.name}", flush=True)
        return out_path

    writer.add_cover(chapter)
    img_dir = Path(f"/tmp/cxl_imgs_v2/{chapter['id']}")
    img_dir.mkdir(parents=True, exist_ok=True)

    for abs_p in range(chapter["start"], chapter["end"] + 1):
        local = abs_p - chapter["start"] + 1
        page = src[abs_p - 1]
        items = extract_page_items(page, abs_p - 1, img_dir)
        print(f"  [{local}/{chapter['pages']}] p{abs_p} items={len(items)}", flush=True)

        # Page marker (not a TOC title — helpful navigation)
        writer.ensure_space(18, header)
        writer.page.insert_text(
            (writer.margin, writer.y + 10),
            f"— Source page {abs_p} —",
            fontname="FCJK",
            fontsize=8,
            color=(0.55, 0.55, 0.55),
        )
        writer.y += 16

        for it in items:
            if it["type"] == "heading":
                # Titles / figure captions: English only
                writer.add_heading(it["text"], header)
            elif it["type"] == "para":
                en = it["text"]
                # Skip TOC-like dotted leaders lines even outside contents chapter
                if re.search(r"\.{4,}\s*\d+\s*$", en) and len(en) < 160:
                    writer.add_heading(en, header)
                    continue
                zh = translator.translate(en)
                writer.add_en_zh(en, zh, header)
            elif it["type"] in ("image", "page_graphics"):
                note = it.get("note", "")
                writer.add_image(it["path"], header, note=note)

        if local % 25 == 0:
            partial = out_path.with_suffix(".partial.pdf")
            # Save checkpoint copy
            tmp_doc = fitz.open()
            tmp_doc.insert_pdf(writer.doc)
            tmp_doc.save(str(partial), deflate=True, garbage=3)
            tmp_doc.close()
            print(f"  checkpoint {partial.name} pages={writer.doc.page_count}", flush=True)

    writer.save(out_path)
    # sync artifact
    art = ARTIFACT_DIR / out_path.name
    art.write_bytes(out_path.read_bytes())
    print(
        f"  done {out_path.name} ({out_path.stat().st_size/1024/1024:.1f} MB) "
        f"cache hits={translator.hits} misses={translator.misses}",
        flush=True,
    )
    return out_path


def main(selected: list[str] | None = None):
    fontfile = ensure_font()
    chapters = json.loads(CHAPTER_MAP.read_text())
    if selected:
        want = set(selected)
        chapters = [c for c in chapters if c["id"] in want]
    src = fitz.open(str(SRC_PDF))
    translator = Translator()
    results = []
    for ch in chapters:
        try:
            p = build_chapter(ch, src, translator, fontfile)
            results.append({"id": ch["id"], "ok": True, "path": str(p)})
        except Exception as e:
            traceback.print_exc()
            results.append({"id": ch["id"], "ok": False, "error": str(e)})
    summary = OUT_DIR / "build_summary_v2.json"
    summary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SUMMARY", json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys

    main(sys.argv[1:] or None)
