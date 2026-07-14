#!/usr/bin/env python3
"""
Facing-page bilingual PDF generator:

  [English original page] then [Chinese page with SAME layout]
  Chinese page keeps images/drawings/tables geometry; only body text is
  replaced with Chinese in the original text boxes.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import traceback
import unicodedata
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path

import fitz
from deep_translator import GoogleTranslator

ROOT = Path("/workspace")
SRC_PDF = ROOT / "CXL-Specification_rev3p2_ver1p0_2024October2_evalcopy.pdf"
CHAPTER_MAP = ROOT / "scripts" / "chapter_map.json"
CACHE_DIR = Path("/tmp/cxl_zh_cache_layout")
OUT_DIR = ROOT / "output" / "chapters_bilingual"
ARTIFACT_DIR = Path("/opt/cursor/artifacts") / "chapters_bilingual"
FONT_TTF = Path("/tmp/wqy-microhei.ttf")

# Keep these chapters as original-only (cover art / TOC list pages)
PASSTHROUGH_IDS = {"00_cover"}

NOISE_EXACT = {
    "Evaluation Copy",
    "October 2, 2024",
    "Revision 3.2, Version 1.0",
    "Compute Express Link Specification",
}
NOISE_RE = re.compile(
    r"^(Evaluation Copy|October 2, 2024|Revision 3\.2, Version 1\.0|"
    r"Compute Express Link Specification|\d{1,4})$"
)


def ensure_font() -> str:
    if FONT_TTF.exists() and FONT_TTF.stat().st_size > 1000:
        return str(FONT_TTF)
    from fontTools.ttLib import TTCollection

    col = TTCollection("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
    col.fonts[0].save(str(FONT_TTF))
    return str(FONT_TTF)


class Translator:
    def __init__(self, timeout_s: float = 20.0):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.gt = GoogleTranslator(source="en", target="zh-CN")
        self.hits = 0
        self.misses = 0
        self.timeout_s = timeout_s
        self._pool = ThreadPoolExecutor(max_workers=1)

    def _call_gt(self, part: str) -> str:
        return self.gt.translate(part)

    def translate(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return ""
        letters = re.sub(r"[^A-Za-z]+", "", text)
        # Keep pure numbers / symbols / very short codes
        if len(letters) < 3:
            return text
        key = hashlib.sha1(text.encode("utf-8")).hexdigest()
        cp = CACHE_DIR / f"{key}.txt"
        if cp.exists():
            self.hits += 1
            return cp.read_text(encoding="utf-8")
        self.misses += 1
        parts = [text] if len(text) <= 4500 else [text[i : i + 4200] for i in range(0, len(text), 4200)]
        out_parts = []
        for part in parts:
            zh = None
            for attempt in range(5):
                try:
                    fut = self._pool.submit(self._call_gt, part)
                    zh = fut.result(timeout=self.timeout_s)
                    break
                except FuturesTimeout:
                    print(f"    translate timeout ({self.timeout_s}s), retry {attempt+1}/5", flush=True)
                    # recreate translator + pool (old worker may still be hung)
                    try:
                        self._pool.shutdown(wait=False, cancel_futures=True)
                    except TypeError:
                        self._pool.shutdown(wait=False)
                    self._pool = ThreadPoolExecutor(max_workers=1)
                    self.gt = GoogleTranslator(source="en", target="zh-CN")
                    time.sleep(1.0 * (attempt + 1))
                except Exception as e:
                    print(f"    translate err: {type(e).__name__}: {e}", flush=True)
                    time.sleep(1.2 * (attempt + 1))
            if zh is None:
                zh = text
            zh = unicodedata.normalize("NFKC", zh)
            zh = (
                zh.replace("\uf9ba", "了")
                .replace("\uf967", "不")
                .replace("\uf901", "更")
                .replace("\uf9ea", "了")
            )
            out_parts.append(zh)
            time.sleep(0.02)
        out = "".join(out_parts)
        cp.write_text(out, encoding="utf-8")
        return out


def is_header_footer(bbox, page_h: float, text: str) -> bool:
    y0, y1 = bbox[1], bbox[3]
    t = text.strip()
    if NOISE_RE.match(t) or t in NOISE_EXACT:
        return True
    if y0 < 62:  # running header band
        return True
    if y1 > page_h - 42:  # footer band
        return True
    # sideways Evaluation Copy watermark
    if bbox[0] < 5 and bbox[2] - bbox[0] < 120 and bbox[3] - bbox[1] > 200:
        return True
    return False


def collect_replace_units(page: fitz.Page) -> list[dict]:
    """
    Collect paragraph-like units with union bbox for in-place replacement.
    Lines that are vertically close and left-aligned are merged.
    """
    d = page.get_text("dict")
    page_h = page.rect.height
    lines = []
    for b in d.get("blocks", []):
        if b.get("type") != 0:
            continue
        for line in b.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s["text"] for s in spans)
            if not text.strip():
                continue
            bbox = fitz.Rect(line["bbox"])
            if is_header_footer(bbox, page_h, text):
                continue
            size = max(s.get("size", 9) for s in spans)
            flags = spans[0].get("flags", 0)
            lines.append(
                {
                    "text": text,
                    "bbox": bbox,
                    "size": size,
                    "flags": flags,
                    "x0": bbox.x0,
                    "y0": bbox.y0,
                    "y1": bbox.y1,
                }
            )
    if not lines:
        return []
    lines.sort(key=lambda L: (round(L["y0"], 1), L["x0"]))

    units: list[dict] = []
    cur = None
    for ln in lines:
        t = ln["text"].strip()
        if cur is None:
            cur = {
                "lines": [ln],
                "text": t,
                "bbox": fitz.Rect(ln["bbox"]),
                "size": ln["size"],
                "flags": ln["flags"],
            }
            continue
        prev = cur["lines"][-1]
        gap = ln["y0"] - prev["y1"]
        same_col = abs(ln["x0"] - prev["x0"]) < 25
        # merge wrapped paragraph lines
        if same_col and gap < max(3.0, prev["size"] * 0.55) and not re.match(r"^\d+(\.\d+)+\s+\S", t):
            cur["lines"].append(ln)
            # join hyphenated breaks
            if cur["text"].endswith("-") and t[:1].islower():
                cur["text"] = cur["text"][:-1] + t
            else:
                cur["text"] = cur["text"] + " " + t
            cur["bbox"] |= ln["bbox"]
            cur["size"] = min(cur["size"], ln["size"])
        else:
            units.append(cur)
            cur = {
                "lines": [ln],
                "text": t,
                "bbox": fitz.Rect(ln["bbox"]),
                "size": ln["size"],
                "flags": ln["flags"],
            }
    if cur:
        units.append(cur)

    # Clean whitespace
    for u in units:
        u["text"] = re.sub(r"\s+", " ", u["text"]).strip()
    return [u for u in units if u["text"]]


def fit_textbox(page: fitz.Page, rect: fitz.Rect, text: str, fontname: str, max_size: float) -> float:
    """Insert text into rect, shrinking fontsize until it fits. Returns used fontsize."""
    size = max_size
    while size >= 4.0:
        rc = page.insert_textbox(
            rect,
            text,
            fontname=fontname,
            fontsize=size,
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT,
        )
        if rc >= 0:
            return size
        size -= 0.5
    # Last resort: still write tiny text (may clip)
    page.insert_textbox(rect, text, fontname=fontname, fontsize=4.0, color=(0, 0, 0))
    return 4.0


def should_translate(text: str) -> bool:
    """Translate body/heading prose; keep short diagram labels in English."""
    t = text.strip()
    if not t:
        return False
    letters = re.sub(r"[^A-Za-z]+", "", t)
    if len(letters) < 3:
        return False
    words = t.split()
    # Numbered section headings always translate
    if re.match(r"^\d+(\.\d+)+\s+\S+", t):
        return True
    if re.match(r"^(Figure|Table)\s+\d+-\d+\.", t, re.I):
        return True
    # Short diagram/UI labels — keep English
    if len(t) <= 22 and len(words) <= 4 and not re.search(r"[.!?]", t):
        return False
    return True


def make_chinese_page(
    src_doc: fitz.Document,
    page_index: int,
    out_doc: fitz.Document,
    translator: Translator,
    fontfile: str,
) -> None:
    """Append EN original page, then a layout-matched ZH page."""
    # 1) English original
    out_doc.insert_pdf(src_doc, from_page=page_index, to_page=page_index)

    # 2) Chinese clone
    out_doc.insert_pdf(src_doc, from_page=page_index, to_page=page_index)
    zh_page = out_doc[-1]
    zh_page.insert_font(fontname="FCJK", fontfile=fontfile)

    units = collect_replace_units(zh_page)
    replacements = []
    for u in units:
        en = u["text"]
        if not should_translate(en):
            continue
        zh = translator.translate(en)
        if not zh:
            continue
        replacements.append((u, zh))

    # Redact original English text areas (keep images/vector art)
    for u, _zh in replacements:
        r = fitz.Rect(u["bbox"])
        r.x0 -= 0.4
        r.y0 -= 0.4
        r.x1 += 0.4
        r.y1 += 0.6
        zh_page.add_redact_annot(r, fill=(1, 1, 1))

    zh_page.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE,
        graphics=fitz.PDF_REDACT_LINE_ART_NONE,
        text=fitz.PDF_REDACT_TEXT_REMOVE,
    )

    zh_page.insert_font(fontname="FCJK", fontfile=fontfile)

    for u, zh in replacements:
        rect = fitz.Rect(u["bbox"])
        rect.y1 = min(zh_page.rect.height - 36, rect.y1 + max(1.0, u["size"] * 0.15))
        rect.x1 = min(zh_page.rect.width - 36, max(rect.x1, rect.x0 + 20))
        max_size = max(5.0, min(u["size"], 11.0))
        fit_textbox(zh_page, rect, zh, "FCJK", max_size)


def add_cover(out_doc: fitz.Document, chapter: dict, fontfile: str):
    page = out_doc.new_page(width=612, height=792)
    page.insert_font(fontname="FCJK", fontfile=fontfile)
    page.draw_rect(fitz.Rect(0, 0, 612, 28), color=None, fill=(0.12, 0.22, 0.38))
    page.insert_text((40, 18), "CXL Spec Rev 3.2 · 中英对照（原版+同版式中文）", fontname="FCJK", fontsize=9, color=(1, 1, 1))
    y = 180
    for text, size, color in [
        ("Compute Express Link Specification", 16, (0.1, 0.2, 0.35)),
        ("Revision 3.2, Version 1.0", 11, (0.35, 0.4, 0.45)),
        ("", 8, None),
        (chapter["title"], 14, (0.1, 0.2, 0.35)),
        (chapter["title_zh"], 13, (0.08, 0.45, 0.42)),
        ("", 10, None),
        ("一页英文原版 + 一页同版式中文", 12, (0.15, 0.15, 0.15)),
        ("English original page, then Chinese page with identical layout", 9, (0.4, 0.4, 0.4)),
        ("仅替换正文文字为中文；图片/线框/表格版式保留。", 9, (0.35, 0.35, 0.35)),
        (f"源页码: {chapter['start']}–{chapter['end']}", 9, (0.35, 0.35, 0.35)),
    ]:
        if not text:
            y += size + 6
            continue
        page.insert_text((48, y), text, fontname="FCJK", fontsize=size, color=color)
        y += size + 12


def expected_out_pages(chapter: dict) -> int:
    """Cover + (EN+ZH) per source page; passthrough is cover + source pages."""
    if chapter["id"] in PASSTHROUGH_IDS:
        return 1 + chapter["pages"]
    return 1 + chapter["pages"] * 2


def build_chapter(chapter: dict, src: fitz.Document, translator: Translator, fontfile: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"CXL_r3.2_{chapter['id']}_中英对照.pdf"
    partial = out_path.with_suffix(".partial.pdf")
    print(f"\n=== {chapter['id']} ({chapter['pages']}p) → facing layout ===", flush=True)

    # Skip if final already complete
    if out_path.exists():
        try:
            done = fitz.open(str(out_path))
            n = done.page_count
            done.close()
            if n >= expected_out_pages(chapter):
                print(f"  skip existing complete {out_path.name} pages={n}", flush=True)
                art = ARTIFACT_DIR / out_path.name
                if not art.exists() or art.stat().st_size != out_path.stat().st_size:
                    art.write_bytes(out_path.read_bytes())
                return out_path
        except Exception:
            pass

    out = fitz.open()
    resume_local = 1  # first source page index within chapter (1-based)

    if chapter["id"] not in PASSTHROUGH_IDS and partial.exists():
        try:
            prev = fitz.open(str(partial))
            # cover(1) + 2 pages per completed source page
            completed = max(0, (prev.page_count - 1) // 2)
            if completed > 0:
                out.insert_pdf(prev)
                resume_local = completed + 1
                print(
                    f"  resume from partial pages={prev.page_count} "
                    f"→ continue at [{resume_local}/{chapter['pages']}]",
                    flush=True,
                )
            prev.close()
        except Exception:
            traceback.print_exc()
            out = fitz.open()
            resume_local = 1

    if out.page_count == 0:
        add_cover(out, chapter, fontfile)

    if chapter["id"] in PASSTHROUGH_IDS:
        out.insert_pdf(src, from_page=chapter["start"] - 1, to_page=chapter["end"] - 1)
        out.save(str(out_path), deflate=True, garbage=3)
        out.close()
        print(f"  passthrough saved {out_path.name}", flush=True)
        return out_path

    for abs_p in range(chapter["start"] + resume_local - 1, chapter["end"] + 1):
        local = abs_p - chapter["start"] + 1
        print(f"  [{local}/{chapter['pages']}] p{abs_p}", flush=True)
        try:
            make_chinese_page(src, abs_p - 1, out, translator, fontfile)
        except Exception:
            traceback.print_exc()
            # fallback: at least keep English page twice
            out.insert_pdf(src, from_page=abs_p - 1, to_page=abs_p - 1)
            out.insert_pdf(src, from_page=abs_p - 1, to_page=abs_p - 1)

        if local % 20 == 0 or local == chapter["pages"]:
            tmp = fitz.open()
            tmp.insert_pdf(out)
            tmp.save(str(partial), deflate=True, garbage=3)
            tmp.close()
            print(f"  checkpoint {partial.name} pages={out.page_count}", flush=True)

    out.save(str(out_path), deflate=True, garbage=3)
    out.close()
    if partial.exists():
        try:
            partial.unlink()
        except OSError:
            pass
    art = ARTIFACT_DIR / out_path.name
    art.write_bytes(out_path.read_bytes())
    print(
        f"  done {out_path.name} ({out_path.stat().st_size/1024/1024:.1f} MB) "
        f"hits={translator.hits} misses={translator.misses}",
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
    translator = Translator(timeout_s=20.0)
    results = []
    for ch in chapters:
        try:
            p = build_chapter(ch, src, translator, fontfile)
            results.append({"id": ch["id"], "ok": True, "path": str(p)})
        except Exception as e:
            traceback.print_exc()
            results.append({"id": ch["id"], "ok": False, "error": str(e)})
    (OUT_DIR / "build_summary_layout.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys

    main(sys.argv[1:] or None)
