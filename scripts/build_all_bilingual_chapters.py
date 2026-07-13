#!/usr/bin/env python3
"""
Split CXL Spec into chapters and build bilingual (EN+ZH) PDFs.

Strategy per chapter:
  - Cover page
  - For each source page: embed the original English page, then a Chinese
    translation page of that page's extracted text.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import traceback
from pathlib import Path

import fitz
from deep_translator import GoogleTranslator

ROOT = Path("/workspace")
SRC_PDF = ROOT / "CXL-Specification_rev3p2_ver1p0_2024October2_evalcopy.pdf"
CHAPTER_MAP = ROOT / "scripts" / "chapter_map.json"
CACHE_DIR = Path("/tmp/cxl_zh_cache")
OUT_DIR = ROOT / "output" / "chapters_bilingual"
ARTIFACT_DIR = Path("/opt/cursor/artifacts")
FONT_TTF = Path("/tmp/wqy-microhei.ttf")

HEADER_FOOTER_RE = re.compile(
    r"^(Evaluation Copy|Introduction|October 2, 2024|Revision 3\.2, Version 1\.0|"
    r"Compute Express Link Specification|\d{1,4})$"
)


def ensure_font() -> Path:
    if FONT_TTF.exists() and FONT_TTF.stat().st_size > 1000:
        return FONT_TTF
    from fontTools.ttLib import TTCollection

    src = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
    col = TTCollection(str(src))
    col.fonts[0].save(str(FONT_TTF))
    return FONT_TTF


def clean_page_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if HEADER_FOOTER_RE.match(s):
            continue
        if s.startswith("October 2, 2024"):
            continue
        if "Compute Express Link Specification" in s and len(s) < 80:
            continue
        lines.append(s)
    # Collapse excessive spaces but keep paragraph-ish breaks
    out = []
    buf = []
    for ln in lines:
        # heading-like short lines flush buffer
        if buf and (len(ln) < 80 and (re.match(r"^\d+(\.\d+)*\b", ln) or ln.endswith(":"))) :
            out.append(" ".join(buf))
            buf = []
            out.append(ln)
            continue
        buf.append(ln)
        joined = " ".join(buf)
        if len(joined) > 500:
            out.append(joined)
            buf = []
    if buf:
        out.append(" ".join(buf))
    return "\n".join(out).strip()


def chunk_text(text: str, limit: int = 4500) -> list[str]:
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    parts = []
    buf = []
    n = 0
    for para in text.split("\n"):
        if n + len(para) + 1 > limit and buf:
            parts.append("\n".join(buf))
            buf = [para]
            n = len(para)
        else:
            buf.append(para)
            n += len(para) + 1
    if buf:
        parts.append("\n".join(buf))
    # hard split any leftover oversized chunk
    final = []
    for p in parts:
        if len(p) <= limit:
            final.append(p)
        else:
            for i in range(0, len(p), limit):
                final.append(p[i : i + limit])
    return final


class Translator:
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.gt = GoogleTranslator(source="en", target="zh-CN")
        self.hits = 0
        self.misses = 0

    def _cache_path(self, text: str) -> Path:
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{h}.txt"

    def translate(self, text: str) -> str:
        import unicodedata

        text = text.strip()
        if not text:
            return ""
        # Keep mostly-symbolic pages as-is note
        if len(re.sub(r"[\W_\d]+", "", text)) < 20 and len(text) < 80:
            return text
        pieces = chunk_text(text)
        out = []
        for piece in pieces:
            cp = self._cache_path(piece)
            if cp.exists():
                out.append(cp.read_text(encoding="utf-8"))
                self.hits += 1
                continue
            self.misses += 1
            zh = None
            for attempt in range(5):
                try:
                    zh = self.gt.translate(piece)
                    break
                except Exception as e:
                    wait = 1.5 * (attempt + 1)
                    print(f"  translate retry {attempt+1}: {e}")
                    time.sleep(wait)
            if zh is None:
                zh = "[翻译失败 / translation failed]\n" + piece
            # Normalize compatibility ideographs (了 -> 了, etc.)
            zh = unicodedata.normalize("NFKC", zh)
            cp.write_text(zh, encoding="utf-8")
            out.append(zh)
            time.sleep(0.05)  # gentle pacing
        return "\n".join(out)


def add_cover(doc: fitz.Document, chapter: dict, fontfile: str):
    page = doc.new_page(width=612, height=792)
    page.insert_font(fontname="FCJK", fontfile=fontfile)
    y = 200
    lines = [
        ("Compute Express Link Specification", 16),
        ("Revision 3.2, Version 1.0", 11),
        ("", 10),
        (chapter["title"], 14),
        (chapter["title_zh"], 14),
        ("", 10),
        ("中英对照译本（非官方）", 12),
        ("Chinese–English Bilingual Edition (Unofficial)", 11),
        ("", 10),
        (f"源页码 Source pages: {chapter['start']}–{chapter['end']} ({chapter['pages']} pages)", 10),
        ("每页先保留英文原页，随后附中文译文页。", 10),
        ("Original English page first, Chinese translation page follows.", 10),
        ("仅供学习参考；如与正式规范冲突，以原文为准。", 9),
    ]
    for text, size in lines:
        if not text:
            y += size + 6
            continue
        page.insert_text((50, y), text, fontname="FCJK", fontsize=size, color=(0.1, 0.2, 0.35))
        y += size + 10
    # footer
    page.insert_text((50, 760), "CXL Spec Rev 3.2 · 中英对照 · Evaluation Copy", fontname="FCJK", fontsize=8, color=(0.4, 0.4, 0.4))


def add_translation_page(
    doc: fitz.Document,
    fontfile: str,
    chapter: dict,
    src_page_num: int,  # 1-based absolute
    local_idx: int,
    en_text: str,
    zh_text: str,
):
    page = doc.new_page(width=612, height=792)
    page.insert_font(fontname="FCJK", fontfile=fontfile)
    # header bar
    page.draw_rect(fitz.Rect(0, 0, 612, 36), color=None, fill=(0.1, 0.21, 0.36))
    page.insert_text(
        (16, 22),
        f"中文译文 / Chinese Translation · 原书第 {src_page_num} 页 · Chapter page {local_idx}",
        fontname="FCJK",
        fontsize=9,
        color=(1, 1, 1),
    )
    page.insert_text(
        (16, 50),
        f"{chapter['title_zh']}  |  {chapter['title']}",
        fontname="FCJK",
        fontsize=8,
        color=(0.15, 0.46, 0.43),
    )

    body = zh_text.strip() if zh_text.strip() else "（本页无可提取正文 / No extractable body text on this page — 请参阅英文原页中的图或表。）"
    # Write wrapped text
    rect = fitz.Rect(36, 64, 576, 750)
    # Prefer Chinese text; if translation failed empty, fall back
    tw = page.insert_textbox(
        rect,
        body,
        fontname="FCJK",
        fontsize=9,
        align=0,
        color=(0.1, 0.1, 0.1),
    )
    # If overflow, shrink font and retry on a new attempt by clearing... 
    # insert_textbox returns unused height negative if overflow.
    if tw < 0:
        # add continuation pages
        remaining = body
        # crude: estimate chars that fit ~ 4500 at fontsize 9
        # Better approach: binary split by paragraphs
        paras = body.split("\n")
        # Already wrote overflowing attempt - replace page content by recreating
        # Simpler strategy: use smaller font from the start for long pages
        pass

    page.insert_text(
        (36, 770),
        "Unofficial machine-assisted translation for study only.",
        fontname="FCJK",
        fontsize=7,
        color=(0.45, 0.45, 0.45),
    )


def add_translation_pages_flow(
    doc: fitz.Document,
    fontfile: str,
    chapter: dict,
    src_page_num: int,
    local_idx: int,
    zh_text: str,
):
    """Add one or more Chinese pages, splitting long text."""
    body = zh_text.strip() if zh_text.strip() else "（本页无可提取正文 / No extractable body text on this page — 请参阅英文原页中的图或表。）"
    # Chunk by approximate capacity (~3200 Chinese chars per page at 9pt)
    capacity = 2800
    chunks = []
    if len(body) <= capacity:
        chunks = [body]
    else:
        paras = body.split("\n")
        buf = []
        n = 0
        for p in paras:
            if n + len(p) + 1 > capacity and buf:
                chunks.append("\n".join(buf))
                buf = [p]
                n = len(p)
            else:
                buf.append(p)
                n += len(p) + 1
        if buf:
            chunks.append("\n".join(buf))
        # hard split
        fixed = []
        for c in chunks:
            if len(c) <= capacity:
                fixed.append(c)
            else:
                for i in range(0, len(c), capacity):
                    fixed.append(c[i : i + capacity])
        chunks = fixed

    for ci, chunk in enumerate(chunks):
        page = doc.new_page(width=612, height=792)
        page.insert_font(fontname="FCJK", fontfile=fontfile)
        page.draw_rect(fitz.Rect(0, 0, 612, 36), color=None, fill=(0.1, 0.21, 0.36))
        suffix = f" ({ci+1}/{len(chunks)})" if len(chunks) > 1 else ""
        page.insert_text(
            (16, 22),
            f"中文译文 / Chinese · 原书第 {src_page_num} 页 · Ch.page {local_idx}{suffix}",
            fontname="FCJK",
            fontsize=9,
            color=(1, 1, 1),
        )
        page.insert_text(
            (16, 50),
            f"{chapter['title_zh']}  |  {chapter['title']}",
            fontname="FCJK",
            fontsize=8,
            color=(0.15, 0.46, 0.43),
        )
        rect = fitz.Rect(36, 64, 576, 750)
        page.insert_textbox(rect, chunk, fontname="FCJK", fontsize=9, align=0, color=(0.1, 0.1, 0.1))
        page.insert_text(
            (36, 770),
            "Unofficial machine-assisted translation for study only. 仅供学习参考。",
            fontname="FCJK",
            fontsize=7,
            color=(0.45, 0.45, 0.45),
        )


def build_chapter(chapter: dict, translator: Translator, fontfile: str, src: fitz.Document) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"CXL_r3.2_{chapter['id']}_中英对照.pdf"
    print(f"\n=== Building {chapter['id']} ({chapter['pages']} pages) -> {out_path.name} ===")

    out = fitz.open()
    add_cover(out, chapter, fontfile)

    for abs_page in range(chapter["start"], chapter["end"] + 1):
        local_idx = abs_page - chapter["start"] + 1
        page = src[abs_page - 1]
        en_text = clean_page_text(page.get_text("text"))
        print(f"  [{local_idx}/{chapter['pages']}] p{abs_page} chars={len(en_text)}")
        zh_text = translator.translate(en_text) if en_text else ""

        # Insert original English page
        out.insert_pdf(src, from_page=abs_page - 1, to_page=abs_page - 1)
        # Add Chinese translation page(s)
        add_translation_pages_flow(out, fontfile, chapter, abs_page, local_idx, zh_text)

        # Checkpoint every 20 pages for large chapters
        if local_idx % 20 == 0:
            tmp = out_path.with_suffix(".partial.pdf")
            out.save(str(tmp), deflate=True, garbage=3)
            print(f"  checkpoint saved {tmp.name} ({out.page_count} pages)")

    out.save(str(out_path), deflate=True, garbage=3)
    out.close()
    # copy to artifacts with shorter name
    art = ARTIFACT_DIR / out_path.name
    art.write_bytes(out_path.read_bytes())
    print(f"  done: {out_path} ({out_path.stat().st_size} bytes)")
    return out_path


def main(selected_ids: list[str] | None = None):
    ensure_font()
    fontfile = str(FONT_TTF)
    chapters = json.loads(CHAPTER_MAP.read_text())
    if selected_ids:
        chapters = [c for c in chapters if c["id"] in selected_ids]
    src = fitz.open(str(SRC_PDF))
    translator = Translator()
    results = []
    for ch in chapters:
        try:
            path = build_chapter(ch, translator, fontfile, src)
            results.append({"id": ch["id"], "path": str(path), "ok": True})
        except Exception as e:
            traceback.print_exc()
            results.append({"id": ch["id"], "ok": False, "error": str(e)})
        print(f"cache hits={translator.hits} misses={translator.misses}")
    summary = OUT_DIR / "build_summary.json"
    summary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SUMMARY", results)


if __name__ == "__main__":
    import sys

    ids = sys.argv[1:] or None
    main(ids)
