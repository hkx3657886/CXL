#!/usr/bin/env python3
"""Generate bilingual CN/EN PDF for CXL Spec Rev 3.2 Chapter 1 (Introduction)."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path("/workspace")
OUT = ROOT / "output" / "CXL_Spec_Rev3.2_Ch1_Introduction_中英对照.pdf"
ARTIFACT = Path("/opt/cursor/artifacts") / "CXL_Spec_Rev3.2_Ch1_Introduction_中英对照.pdf"
TERMS = json.loads((ROOT / "scripts" / "cxl_terms_bilingual.json").read_text())
IMGS = Path("/tmp/cxl_imgs")

def _ensure_cjk_font() -> Path:
    """Extract a TrueType CJK face that also covers Latin glyphs."""
    out = Path("/tmp/wqy-microhei.ttf")
    if out.exists() and out.stat().st_size > 1000:
        return out
    from fontTools.ttLib import TTCollection
    src = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
    col = TTCollection(str(src))
    col.fonts[0].save(str(out))
    return out


_CJK = _ensure_cjk_font()
pdfmetrics.registerFont(TTFont("NotoSansSC", str(_CJK)))
pdfmetrics.registerFont(TTFont("NotoSansSC-Bold", str(_CJK)))

PAGE_W, PAGE_H = letter
MARGIN = 0.7 * inch

NAVY = colors.HexColor("#1a365d")
TEAL = colors.HexColor("#0f766e")
LIGHT = colors.HexColor("#f0f7f7")
RULE = colors.HexColor("#cbd5e1")
MUTED = colors.HexColor("#475569")


def styles():
    base = getSampleStyleSheet()
    s = {
        "cover_brand": ParagraphStyle(
            "cover_brand",
            fontName="NotoSansSC-Bold",
            fontSize=22,
            leading=28,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName="NotoSansSC",
            fontSize=12,
            leading=18,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="NotoSansSC-Bold",
            fontSize=16,
            leading=22,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="NotoSansSC-Bold",
            fontSize=13,
            leading=18,
            textColor=TEAL,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName="NotoSansSC-Bold",
            fontSize=11,
            leading=15,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "en": ParagraphStyle(
            "en",
            fontName="NotoSansSC",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
            alignment=TA_JUSTIFY,
            spaceAfter=2,
        ),
        "zh": ParagraphStyle(
            "zh",
            fontName="NotoSansSC",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            backColor=None,
        ),
        "label_en": ParagraphStyle(
            "label_en",
            fontName="NotoSansSC-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
            spaceBefore=4,
            spaceAfter=1,
        ),
        "label_zh": ParagraphStyle(
            "label_zh",
            fontName="NotoSansSC-Bold",
            fontSize=8,
            leading=10,
            textColor=TEAL,
            spaceBefore=2,
            spaceAfter=1,
        ),
        "term": ParagraphStyle(
            "term",
            fontName="NotoSansSC-Bold",
            fontSize=8.5,
            leading=11,
            textColor=NAVY,
        ),
        "tdef": ParagraphStyle(
            "tdef",
            fontName="NotoSansSC",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#334155"),
            alignment=TA_LEFT,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="NotoSansSC",
            fontSize=9,
            leading=12,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        ),
        "bullet_en": ParagraphStyle(
            "bullet_en",
            fontName="NotoSansSC",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
            leftIndent=10,
        ),
        "bullet_zh": ParagraphStyle(
            "bullet_zh",
            fontName="NotoSansSC",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
            leftIndent=10,
            spaceAfter=6,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="NotoSansSC",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "note": ParagraphStyle(
            "note",
            fontName="NotoSansSC",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
    }
    return s


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def bilingual_para(story, s, en: str, zh: str):
    story.append(Paragraph("EN", s["label_en"]))
    story.append(Paragraph(esc(en), s["en"]))
    story.append(Paragraph("中文", s["label_zh"]))
    story.append(Paragraph(esc(zh), s["zh"]))


def bilingual_bullets(story, s, pairs: list[tuple[str, str]]):
    for en, zh in pairs:
        story.append(Paragraph("• " + esc(en), s["bullet_en"]))
        story.append(Paragraph("　" + esc(zh), s["bullet_zh"]))


def add_figure(story, s, path: Path, caption_en: str, caption_zh: str, max_w=6.8 * inch, max_h=4.2 * inch):
    if not path.exists():
        story.append(Paragraph(f"[Missing figure: {path.name}]", s["note"]))
        return
    img = Image(str(path))
    iw, ih = img.imageWidth, img.imageHeight
    scale = min(max_w / iw, max_h / ih, 1.0)
    img.drawWidth = iw * scale
    img.drawHeight = ih * scale
    story.append(Spacer(1, 6))
    story.append(img)
    story.append(Paragraph(esc(f"{caption_en} / {caption_zh}"), s["caption"]))


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, PAGE_H - 0.45 * inch, PAGE_W - MARGIN, PAGE_H - 0.45 * inch)
    canvas.setFont("NotoSansSC", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, PAGE_H - 0.38 * inch, "CXL Specification Rev 3.2 · Chapter 1 · 中英对照")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.38 * inch, "Evaluation Copy")
    canvas.line(MARGIN, 0.5 * inch, PAGE_W - MARGIN, 0.5 * inch)
    canvas.drawCentredString(PAGE_W / 2, 0.32 * inch, f"{doc.page}")
    canvas.restoreState()


def build_terms_table(s, start: int, end: int):
    data = [
        [
            Paragraph("<b>Term<br/>术语</b>", s["term"]),
            Paragraph("<b>English Definition / 英文定义</b>", s["term"]),
            Paragraph("<b>Chinese Definition / 中文定义</b>", s["term"]),
        ]
    ]
    for e in TERMS[start:end]:
        term = e["term"]
        if e.get("alias"):
            term = f"{term} / {e['alias']}"
        data.append(
            [
                Paragraph(esc(term), s["term"]),
                Paragraph(esc(e["definition_en"]), s["tdef"]),
                Paragraph(esc(e["definition_zh"]), s["tdef"]),
            ]
        )
    col_w = [1.35 * inch, 2.85 * inch, 2.85 * inch]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def build():
    s = styles()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=0.65 * inch,
        bottomMargin=0.7 * inch,
        title="CXL Specification Rev 3.2 Chapter 1 — 中英对照",
        author="Bilingual translation (unofficial)",
    )
    story = []

    # ---- Cover ----
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph("Compute Express Link Specification", s["cover_brand"]))
    story.append(Paragraph("Revision 3.2, Version 1.0", s["cover_sub"]))
    story.append(Paragraph("第 1 章　导论 / Chapter 1.0 Introduction", s["cover_brand"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("中英对照译本（非官方）", s["cover_sub"]))
    story.append(Paragraph("Chinese–English Bilingual Edition (Unofficial)", s["cover_sub"]))
    story.append(Spacer(1, 0.4 * inch))
    story.append(
        Paragraph(
            "源文档：CXL Specification Rev 3.2, Version 1.0（2024-10-02）Evaluation Copy — Chapter 1<br/>"
            "本译本仅供学习参考，术语以原文为准。插图保留英文原图。",
            s["cover_sub"],
        )
    )
    story.append(PageBreak())

    # ---- 1.0 / 1.1 ----
    story.append(Paragraph("1.0 Introduction / 导论", s["h1"]))
    story.append(Paragraph("1.1 Audience / 读者对象", s["h2"]))
    bilingual_para(
        story,
        s,
        "The information in this document is intended for anyone designing or architecting any "
        "hardware or software associated with Compute Express Link (CXL) or Flex Bus.",
        "本文档中的信息面向任何设计或架构与 Compute Express Link（CXL）或 Flex Bus 相关的"
        "硬件或软件的人员。",
    )

    # ---- 1.2 Terms ----
    story.append(Paragraph("1.2 Terminology/Acronyms / 术语与缩略语", s["h2"]))
    bilingual_para(
        story,
        s,
        "Refer to PCIe Base Specification for additional terminology and acronym definitions "
        "beyond those listed in Table 1-1.",
        "表 1-1 未列出的其他术语与缩略语定义，请参阅 PCIe 基础规范。",
    )
    story.append(Paragraph("Table 1-1. Terminology/Acronyms / 表 1-1 术语与缩略语", s["h3"]))
    story.append(
        Paragraph(
            "下表按英文字母序给出原文定义与中文译文。专有缩写在译文中保留英文形式。",
            s["note"],
        )
    )

    # Split terms into chunks to keep table rendering manageable
    chunk = 40
    for i in range(0, len(TERMS), chunk):
        story.append(build_terms_table(s, i, i + chunk))
        story.append(Spacer(1, 8))
        if i + chunk < len(TERMS):
            story.append(PageBreak())

    story.append(PageBreak())

    # ---- 1.3 Reference Documents ----
    story.append(Paragraph("1.3 Reference Documents / 参考文档", s["h2"]))
    story.append(Paragraph("Table 1-2. Reference Documents / 表 1-2 参考文档", s["h3"]))

    refs = [
        (
            "PCI Express Base Specification Revision 6.2 (abbreviated as PCIe Base Specification)",
            "PCI Express 基础规范修订版 6.2（在 CXL 规范中简称为 PCIe 基础规范）",
            "N/A",
            "www.pcisig.com",
        ),
        (
            "PCI Firmware Specification (revision 3.3 or later)",
            "PCI 固件规范（修订版 3.3 或更高）",
            "Various / 多处",
            "www.pcisig.com",
        ),
        (
            "Unordered IO (UIO) ECN to PCI Express Base Specification Revision 6.0",
            "针对 PCI Express 基础规范修订版 6.0 的无序 I/O（UIO）ECN",
            "N/A",
            "members.pcisig.com/wg/PCI-SIG/document/19388",
        ),
        (
            "Management Message Passthrough via MMIO Mailbox (MMPT) ECN to PCI Express Specification Revision 6.1",
            "针对 PCI Express 规范修订版 6.1 的经由 MMIO 邮箱的管理消息透传（MMPT）ECN",
            "N/A",
            "members.pcisig.com/wg/PCI-SIG/document/20109",
        ),
        (
            "ACPI Specification (version 6.5 or later)",
            "ACPI 规范（版本 6.5 或更高）",
            "Various / 多处",
            "www.uefi.org",
        ),
        (
            "Coherent Device Attribute Table (CDAT) Specification (version 1.04 or later)",
            "一致性设备属性表（CDAT）规范（版本 1.04 或更高）",
            "Various / 多处",
            "www.uefi.org/acpi",
        ),
        (
            "RFC 4122 A Universally Unique IDentifier UUID URN Namespace",
            "RFC 4122 通用唯一标识符 UUID URN 命名空间",
            "Various / 多处",
            "www.ietf.org/rfc/rfc4122",
        ),
        (
            "UEFI Specification (version 2.10 or later)",
            "UEFI 规范（版本 2.10 或更高）",
            "Various / 多处",
            "www.uefi.org",
        ),
        (
            "CXL Fabric Manager API over MCTP Binding Specification (DSP0234) (version 1.0.0 or later)",
            "基于 MCTP 绑定的 CXL 结构管理器 API 规范（DSP0234）（版本 1.0.0 或更高）",
            "Chapter 7 / 第 7 章",
            "www.dmtf.org/dsp/DSP0234",
        ),
        (
            "Management Component Transport Protocol (MCTP) Base Specification (DSP0236) (version 1.3.1 or later)",
            "管理组件传输协议（MCTP）基础规范（DSP0236）（版本 1.3.1 或更高）",
            "Chapters 7, 8, 11 / 第 7、8、11 章",
            "www.dmtf.org/dsp/DSP0236",
        ),
        (
            "MCTP SMBus/I2C Transport Binding Specification (DSP0237) (version 1.2.0 or later)",
            "MCTP SMBus/I2C 传输绑定规范（DSP0237）（版本 1.2.0 或更高）",
            "Chapter 11 / 第 11 章",
            "www.dmtf.org/dsp/DSP0237",
        ),
        (
            "MCTP PCIe VDM Transport Binding Specification (DSP0238) (version 1.2.0 or later)",
            "MCTP PCIe VDM 传输绑定规范（DSP0238）（版本 1.2.0 或更高）",
            "Chapters 7, 11 / 第 7、11 章",
            "www.dmtf.org/dsp/DSP0238",
        ),
        (
            "Security Protocol and Data Model (SPDM) Specification (DSP0274) (version 1.2.0 or later)",
            "安全协议与数据模型（SPDM）规范（DSP0274）（版本 1.2.0 或更高）",
            "Chapters 11, 14 / 第 11、14 章",
            "www.dmtf.org/dsp/DSP0274",
        ),
        (
            "SPDM over MCTP Binding Specification (DSP0275) (version 1.0.0 or later)",
            "基于 MCTP 绑定的 SPDM 规范（DSP0275）（版本 1.0.0 或更高）",
            "Chapter 11 / 第 11 章",
            "www.dmtf.org/dsp/DSP0275",
        ),
        (
            "Secured Messages using SPDM over MCTP Binding Specification (DSP0276) (version 1.0.0 or later)",
            "基于 MCTP 绑定使用 SPDM 的安全消息规范（DSP0276）（版本 1.0.0 或更高）",
            "Chapter 11 / 第 11 章",
            "www.dmtf.org/dsp/DSP0276",
        ),
        (
            "Secured Messages using SPDM Specification (DSP0277) (version 1.0.0 or later)",
            "使用 SPDM 的安全消息规范（DSP0277）（版本 1.0.0 或更高）",
            "Chapter 11 / 第 11 章",
            "www.dmtf.org/dsp/DSP0277",
        ),
        (
            "CXL Type 3 Component Command Interface over MCTP Binding Specification (DSP0281) (version 1.0.0 or later)",
            "基于 MCTP 绑定的 CXL Type 3 组件命令接口规范（DSP0281）（版本 1.0.0 或更高）",
            "Chapters 7, 9 / 第 7、9 章",
            "www.dmtf.org/dsp/DSP0281",
        ),
        (
            "NIST SP 800-38D Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC",
            "NIST SP 800-38D 分组密码工作模式建议：伽罗瓦/计数器模式（GCM）与 GMAC",
            "Chapters 8, 11 / 第 8、11 章",
            "nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf",
        ),
        (
            "JEDEC DDR5 Specification, JESD79-5 (5B, version 1.2 or later)",
            "JEDEC DDR5 规范，JESD79-5（5B，版本 1.2 或更高）",
            "Chapters 8, 13 / 第 8、13 章",
            "www.jedec.org",
        ),
        (
            "Security Features for SCSI Commands (SFSC)",
            "SCSI 命令安全特性（SFSC）",
            "Chapter 8 / 第 8 章",
            "webstore.ansi.org",
        ),
    ]

    ref_data = [
        [
            Paragraph("<b>Document / 文档</b>", s["term"]),
            Paragraph("<b>Chapter / 章节</b>", s["term"]),
            Paragraph("<b>Location / 位置</b>", s["term"]),
        ]
    ]
    for en, zh, chap, loc in refs:
        ref_data.append(
            [
                Paragraph(esc(en) + "<br/><font color='#0f766e'>" + esc(zh) + "</font>", s["tdef"]),
                Paragraph(esc(chap), s["tdef"]),
                Paragraph(esc(loc), s["tdef"]),
            ]
        )
    ref_table = Table(ref_data, colWidths=[4.2 * inch, 1.4 * inch, 1.5 * inch], repeatRows=1)
    ref_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(ref_table)
    story.append(Spacer(1, 8))
    bilingual_para(
        story,
        s,
        "Note 1: Peer-to-peer flows to CXL.mem regions are supported using Unordered I/O (UIO) on the "
        "CXL.io protocol or with Direct CXL.mem access as described in this specification.",
        "注 1：到 CXL.mem 区域的点对点流可通过 CXL.io 协议上的无序 I/O（UIO），或通过本规范所述的"
        "直接 CXL.mem 访问来支持。",
    )

    story.append(PageBreak())

    # ---- 1.4 Motivation ----
    story.append(Paragraph("1.4 Motivation and Overview / 动机与概述", s["h2"]))
    story.append(Paragraph("1.4.1 CXL", s["h3"]))
    bilingual_para(
        story,
        s,
        "CXL is a dynamic multi-protocol technology designed to support accelerators and memory devices. "
        "CXL provides a rich set of protocols that include I/O semantics similar to PCIe (i.e., CXL.io), "
        "caching protocol semantics (i.e., CXL.cache), and memory access semantics (i.e., CXL.mem) over a "
        "discrete or on-package link. CXL.io is required for discovery and enumeration, error reporting, "
        "P2P accesses to CXL memory and host physical address (HPA) lookup. CXL.cache and CXL.mem protocols "
        "may be optionally implemented by the particular accelerator or memory device usage model. An "
        "important benefit of CXL is that it provides a low-latency, high-bandwidth path for an accelerator "
        "to access the system and for the system to access the memory attached to the CXL device. "
        "Figure 1-1 is a conceptual diagram that shows a device attached to a Host processor via CXL.",
        "CXL 是一种面向加速器与内存设备的动态多协议技术。CXL 提供丰富的协议集合，包括与 PCIe 类似的 "
        "I/O 语义（即 CXL.io）、缓存协议语义（即 CXL.cache）以及内存访问语义（即 CXL.mem），可运行于"
        "分立链路或封装内链路上。CXL.io 是发现与枚举、错误报告、对 CXL 内存的 P2P 访问以及主机物理地址"
        "（HPA）查找所必需的。CXL.cache 与 CXL.mem 协议可由特定加速器或内存设备使用模型选择实现。"
        "CXL 的一项重要收益是：它为加速器访问系统、以及系统访问连接到 CXL 设备的内存，提供了低延迟、"
        "高带宽路径。图 1-1 是经由 CXL 将设备连接到主机处理器的概念图。",
    )
    add_figure(
        story,
        s,
        IMGS / "p13_img1.png",
        "Figure 1-1. Conceptual Diagram of Device Attached to Processor via CXL",
        "图 1-1. 设备经 CXL 连接到处理器的概念图",
    )

    bilingual_para(
        story,
        s,
        "The CXL 2.0 specification enables additional usage models beyond the CXL 1.1 specification, while "
        "being fully backward compatible with the CXL 1.1 (and CXL 1.0) specification. It enables managed "
        "Hot-Plug, security enhancements, persistent memory support, memory error reporting, and telemetry. "
        "The CXL 2.0 specification also enables single-level switching support for fan-out as well as the "
        "ability to pool devices across multiple virtual hierarchies, including multi-domain support of "
        "memory devices. Figure 1-2 demonstrates memory and accelerator disaggregation through single level "
        "switching, in addition to fan-out, across multiple virtual hierarchies, each represented by a unique "
        "color. The CXL 2.0 specification also enables these resources (memory or accelerators) to be "
        "off-lined from one domain and on-lined into another domain, thereby allowing the resources to be "
        "time-multiplexed across different virtual hierarchies, depending on their resource demand.",
        "CXL 2.0 规范在完全向后兼容 CXL 1.1（以及 CXL 1.0）规范的同时，支持超出 CXL 1.1 的更多使用模型。"
        "它支持受管热插拔、安全增强、持久内存支持、内存错误报告与遥测。CXL 2.0 还支持用于扇出的单级交换，"
        "以及跨多个虚拟层级池化设备的能力，包括内存设备的多域支持。图 1-2 展示了通过单级交换实现内存与"
        "加速器解聚，以及跨多个虚拟层级（各用不同颜色表示）的扇出。CXL 2.0 还允许将这些资源（内存或加速器）"
        "从一个域下线并上线到另一域，从而可按资源需求在不同虚拟层级间进行时分复用。",
    )

    bilingual_para(
        story,
        s,
        "The CXL 3.0 specification doubles the bandwidth while enabling additional usage models beyond the "
        "CXL 2.0 specification. The CXL 3.0 specification is fully backward compatible with the CXL 2.0 "
        "specification (and hence with the CXL 1.1 and CXL 1.0 specifications). The maximum Data Rate doubles "
        "to 64.0 GT/s with PAM-4 signaling, leveraging the PCIe Base Specification PHY along with its CRC and "
        "FEC, to double the bandwidth, with provision for an optional Flit arrangement for low latency. "
        "Multi-level switching is enabled with the CXL 3.0 specification, supporting up to 4K Ports, to enable "
        "CXL to evolve as a fabric extending, including non-tree topologies, to the Rack and Pod level. The "
        "CXL 3.0 specification enables devices to perform direct peer-to-peer accesses to HDM memory using UIO "
        "(in addition to MMIO memory that existed before) to deliver performance at scale, as shown in "
        "Figure 1-3. Snoop Filter support can be implemented in Type 2 and Type 3 devices to enable direct "
        "peer-to-peer accesses using the back-invalidate channels introduced in CXL.mem. Shared memory support "
        "across multiple virtual hierarchies is provided for collaborative processing across multiple virtual "
        "hierarchies, as shown in Figure 1-4.",
        "CXL 3.0 规范在带宽翻倍的同时，支持超出 CXL 2.0 的更多使用模型，并与 CXL 2.0（因此也与 CXL 1.1、"
        "CXL 1.0）完全向后兼容。最大数据速率在 PAM-4 信令下提升至 64.0 GT/s，利用 PCIe 基础规范 PHY 及其 "
        "CRC 与 FEC 实现带宽翻倍，并可选采用面向低延迟的 Flit 编排。CXL 3.0 启用多级交换，最多支持 4K 端口，"
        "使 CXL 可演进为扩展到机架与 Pod 级别的结构（含非树形拓扑）。CXL 3.0 允许设备使用 UIO 对 HDM 内存"
        "进行直接点对点访问（此外仍支持此前已有的 MMIO 内存），以实现规模化性能，如图 1-3 所示。Type 2 与 "
        "Type 3 设备可实现探听过滤器支持，以便利用 CXL.mem 引入的反向使无效通道进行直接点对点访问。"
        "还提供跨多个虚拟层级的共享内存支持，用于跨虚拟层级的协同处理，如图 1-4 所示。",
    )

    bilingual_para(
        story,
        s,
        "CXL protocol is compatible with PCIe CEM Form Factor (4.0 and later), all form factors relating to "
        "EDSFF SSF-TA-1009 (revision 2.0 and later) and other form factors that support PCIe.",
        "CXL 协议与 PCIe CEM 形态规格（4.0 及更高）、与 EDSFF SSF-TA-1009（修订版 2.0 及更高）相关的所有"
        "形态规格，以及其他支持 PCIe 的形态规格兼容。",
    )
    story.append(
        Paragraph(
            "Figure 1-2. Fan-out and Pooling Enabled by Switches / 图 1-2. 交换机实现的扇出与池化"
            "（原图为矢量示意，见源 PDF 第 63 页）",
            s["caption"],
        )
    )
    add_figure(
        story,
        s,
        IMGS / "p15_img1.png",
        "Figure 1-3. Direct Peer-to-Peer Access to an HDM Memory by PCIe/CXL Devices without Going through the Host",
        "图 1-3. PCIe/CXL 设备不经主机直接点对点访问 HDM 内存",
        max_h=3.6 * inch,
    )
    add_figure(
        story,
        s,
        IMGS / "p15_img2.png",
        "Figure 1-4. Shared Memory across Multiple Virtual Hierarchies",
        "图 1-4. 跨多个虚拟层级的共享内存",
        max_h=3.6 * inch,
    )

    story.append(Paragraph("1.4.2 Flex Bus", s["h3"]))
    bilingual_para(
        story,
        s,
        "A Flex Bus port allows designs to choose between providing native PCIe protocol or CXL over a "
        "high-bandwidth, off-package link; the selection happens during link training via alternate protocol "
        "negotiation and depends on the device that is plugged into the slot. Flex Bus uses PCIe electricals, "
        "making it compatible with PCIe retimers and with form factors that support PCIe.",
        "Flex Bus 端口允许设计在高带宽、封装外链路上选择提供原生 PCIe 协议或 CXL；选择在链路训练期间通过"
        "备用协议协商完成，并取决于插入插槽的设备。Flex Bus 使用 PCIe 电气特性，因此与 PCIe 重定时器以及"
        "支持 PCIe 的形态规格兼容。",
    )
    bilingual_para(
        story,
        s,
        "Figure 1-5 provides a high-level diagram of a Flex Bus port implementation, illustrating both a slot "
        "implementation and a custom implementation where the device is soldered down on the motherboard. The "
        "slot implementation can accommodate either a Flex Bus.CXL card or a PCIe card. One or two optional "
        "retimers can be inserted between the CPU and the device to extend the channel length. As illustrated "
        "in Figure 1-6, this flexible port can be used to attach coherent accelerators or smart I/O to a Host "
        "processor. Figure 1-7 illustrates how a Flex Bus.CXL port can be used as a memory expansion port.",
        "图 1-5 给出 Flex Bus 端口实现的高层示意，同时展示插槽实现以及设备焊接在主板上的定制实现。"
        "插槽实现可容纳 Flex Bus.CXL 卡或 PCIe 卡。可在 CPU 与设备之间插入一或两个可选重定时器以延长通道。"
        "如图 1-6 所示，该灵活端口可用于将一致性加速器或智能 I/O 连接到主机处理器。图 1-7 说明如何将 "
        "Flex Bus.CXL 端口用作内存扩展端口。",
    )
    add_figure(
        story,
        s,
        IMGS / "p16_img1.png",
        "Figure 1-5. CPU Flex Bus Port Example",
        "图 1-5. CPU Flex Bus 端口示例",
        max_h=4.5 * inch,
    )
    add_figure(
        story,
        s,
        IMGS / "p17_img1.png",
        "Figure 1-6. Flex Bus Usage Model Examples",
        "图 1-6. Flex Bus 使用模型示例",
    )
    add_figure(
        story,
        s,
        IMGS / "p17_img2.png",
        "Figure 1-7. Remote Far Memory Usage Model Example",
        "图 1-7. 远程远端内存使用模型示例",
    )
    bilingual_para(
        story,
        s,
        "Figure 1-8 illustrates the connections that are supported below a CXL Downstream Port.",
        "图 1-8 说明 CXL 下游端口下方所支持的连接。",
    )
    story.append(
        Paragraph(
            "Figure 1-8. CXL Downstream Port Connections / 图 1-8. CXL 下游端口连接"
            "（示意见源 PDF 第 67 页）",
            s["caption"],
        )
    )

    # ---- 1.5 ----
    story.append(Paragraph("1.5 Flex Bus Link Features / Flex Bus 链路特性", s["h2"]))
    bilingual_para(
        story,
        s,
        "Flex Bus provides a point-to-point interconnect that can transmit native PCIe protocol or dynamic "
        "multi-protocol CXL to provide I/O, caching, and memory protocols over PCIe electricals. The primary "
        "link attributes include support of the following features:",
        "Flex Bus 提供点对点互连，可传输原生 PCIe 协议或动态多协议 CXL，从而在 PCIe 电气上提供 I/O、缓存与"
        "内存协议。主要链路属性包括以下特性支持：",
    )
    bilingual_bullets(
        story,
        s,
        [
            (
                "Native PCIe mode, full feature support as defined in PCIe Base Specification",
                "原生 PCIe 模式，完整特性支持如 PCIe 基础规范所定义",
            ),
            (
                "CXL mode, as defined in this specification",
                "CXL 模式，如本规范所定义",
            ),
            (
                "Configuration of PCIe vs. CXL protocol mode",
                "PCIe 与 CXL 协议模式的配置",
            ),
            (
                "With PAM4, signaling rate of 64 GT/s, and degraded rates of 32 GT/s, 16 GT/s, or 8 GT/s in CXL mode. "
                "Otherwise, signaling rate of 32 GT/s, degraded rate of 16 GT/s or 8 GT/s in CXL mode",
                "在 PAM4 下，CXL 模式信令速率为 64 GT/s，降级速率为 32/16/8 GT/s；否则 CXL 模式信令速率为 "
                "32 GT/s，降级速率为 16 或 8 GT/s",
            ),
            (
                "Link width support for x16, x8, x4, x2 (degraded mode), and x1 (degraded mode) in CXL mode",
                "CXL 模式下链路宽度支持 x16、x8、x4、x2（降级）与 x1（降级）",
            ),
            (
                "Bifurcation (aka Link Subdivision) support to x4 in CXL mode",
                "CXL 模式下支持分叉（即链路细分）至 x4",
            ),
        ],
    )

    # ---- 1.6 ----
    story.append(Paragraph("1.6 Flex Bus Layering Overview / Flex Bus 分层概述", s["h2"]))
    bilingual_para(
        story,
        s,
        "Flex Bus architecture is organized as multiple layers, as illustrated in Figure 1-9. The CXL "
        "transaction (protocol) layer is subdivided into logic that handles CXL.io and logic that handles "
        "CXL.cache and CXL.mem; the CXL link layer is subdivided in the same manner. Note that the CXL.cache "
        "and CXL.mem logic are combined within the transaction layer and within the link layer. The CXL link "
        "layer interfaces with the CXL ARB/MUX, which interleaves the traffic from the two logic streams. "
        "Additionally, the PCIe transaction and data link layers are optionally implemented and, if "
        "implemented, are permitted to be converged with the CXL.io transaction and link layers, respectively. "
        "As a result of the link training process, the transaction and link layers are configured to operate "
        "in either PCIe mode or CXL mode. While a host CPU would most likely implement both modes, an "
        "accelerator AIC is permitted to implement only the CXL mode. The logical sub-block of the Flex Bus "
        "physical layer is a converged logical physical layer that can operate in either PCIe mode or CXL mode, "
        "depending on the results of alternate mode negotiation during link training.",
        "Flex Bus 架构组织为多层，如图 1-9 所示。CXL 事务（协议）层细分为处理 CXL.io 的逻辑，以及处理 "
        "CXL.cache 与 CXL.mem 的逻辑；CXL 链路层亦按同样方式细分。注意：CXL.cache 与 CXL.mem 逻辑在事务层"
        "与链路层内部是合并的。CXL 链路层与 CXL ARB/MUX 接口，后者对两路逻辑流的流量进行交织。"
        "此外，PCIe 事务层与数据链路层为可选实现；若实现，则允许分别与 CXL.io 事务层和链路层融合。"
        "链路训练结束后，事务层与链路层被配置为以 PCIe 模式或 CXL 模式运行。主机 CPU 很可能实现两种模式，"
        "而加速器 AIC 允许仅实现 CXL 模式。Flex Bus 物理层的逻辑子块是融合的逻辑物理层，可根据链路训练期间"
        "备用模式协商结果，以 PCIe 模式或 CXL 模式运行。",
    )
    add_figure(
        story,
        s,
        IMGS / "p19_img1.png",
        "Figure 1-9. Conceptual Diagram of Flex Bus Layering",
        "图 1-9. Flex Bus 分层概念图",
        max_h=5.2 * inch,
    )

    # ---- 1.7 ----
    story.append(Paragraph("1.7 Document Scope / 文档范围", s["h2"]))
    bilingual_para(
        story,
        s,
        "This document specifies the functional and operational details of the Flex Bus interconnect and the "
        "CXL protocol. It describes the CXL usage model and defines how the transaction, link, and physical "
        "layers operate. Reset, power management, and initialization/configuration flows are described. "
        "Additionally, RAS behavior is described. Refer to PCIe Base Specification for PCIe protocol details.",
        "本文档规定 Flex Bus 互连与 CXL 协议的功能与运行细节。它描述 CXL 使用模型，并定义事务层、链路层与"
        "物理层如何工作。同时描述复位、电源管理以及初始化/配置流程，并描述 RAS 行为。PCIe 协议细节请参阅 "
        "PCIe 基础规范。",
    )
    bilingual_para(
        story,
        s,
        "The contents of this document are summarized in the following chapter highlights:",
        "本文档内容按以下章节要点概述：",
    )

    chapters = [
        (
            "Chapter 2.0, “CXL System Architecture” – This chapter describes Type 1, Type 2, and Type 3 devices "
            "that might attach to a CPU Root Complex or a CXL switch over a CXL-capable link. For each device "
            "profile, a description of the typical workload and system resource usage is provided along with an "
            "explanation of which CXL capabilities are relevant for that workload. Bias-based and "
            "Back-Invalidate-based coherency models are introduced. This chapter also covers multi-headed "
            "devices and G-FAM devices and how they enable memory pooling and memory sharing usages. It also "
            "provides a summary of the CXL fabric extensions and its scalability.",
            "第 2.0 章“CXL 系统架构”——描述可能通过支持 CXL 的链路连接到 CPU 根复合体或 CXL 交换机的 "
            "Type 1、Type 2 与 Type 3 设备。对每种设备配置给出典型工作负载与系统资源使用说明，并解释哪些 "
            "CXL 能力与该工作负载相关。介绍基于 Bias 与基于 Back-Invalidate 的一致性模型。本章还涵盖多头设备与 "
            "G-FAM 设备，及其如何支持内存池化与内存共享，并概述 CXL 结构扩展及其可扩展性。",
        ),
        (
            "Chapter 3.0, “CXL Transaction Layer” – This chapter is divided into subsections that describe "
            "details for CXL.io, CXL.cache, and CXL.mem. The CXL.io protocol is required for all implementations, "
            "while the other two protocols are optional depending on expected device usage and workload. The "
            "transaction layer specifies the transaction types, transaction layer packet formatting, transaction "
            "ordering rules, and crediting. The CXL.io protocol is based on the “Transaction Layer Specification” "
            "chapter of PCIe Base Specification; any deltas from PCIe Base Specification are described in this "
            "chapter. These deltas include PCIe Vendor Defined Messages for reset and power management, "
            "modifications to the PCIe ATS request and completion formats to support accelerators. For CXL.cache, "
            "this chapter describes the channels in each direction (i.e., request, response, and data), the "
            "transaction opcodes that flow through each channel, and the channel crediting and ordering rules. "
            "The transaction fields associated with each channel are also described. For CXL.mem, this chapter "
            "defines the message classes in each direction, the fields associated with each message class, and "
            "the message class ordering rules. Finally, this chapter provides flow diagrams that illustrate the "
            "sequence of transactions involved in completing host-initiated and device-initiated accesses to "
            "device-attached memory.",
            "第 3.0 章“CXL 事务层”——分节描述 CXL.io、CXL.cache 与 CXL.mem。所有实现均需 CXL.io；另两种协议"
            "可视预期设备用途与工作负载选择实现。事务层规定事务类型、事务层包格式、事务排序规则与信用机制。"
            "CXL.io 基于 PCIe 基础规范“事务层规范”章节；与 PCIe 的差异在本章说明，包括用于复位与电源管理的 "
            "PCIe 厂商定义消息，以及对 PCIe ATS 请求与完成格式的修改以支持加速器。对 CXL.cache，本章描述各方向"
            "通道（请求、响应与数据）、流经各通道的事务操作码，以及通道信用与排序规则，并描述各通道相关事务字段。"
            "对 CXL.mem，本章定义各方向消息类、各类相关字段以及消息类排序规则。最后给出流程图，说明完成主机发起"
            "与设备发起的对设备附属内存访问所涉及的事务序列。",
        ),
        (
            "Chapter 4.0, “CXL Link Layers” – The link layer is responsible for reliable transmission of the "
            "transaction layer packets across the Flex Bus link. This chapter is divided into subsections that "
            "describe details for CXL.io and for CXL.cache and CXL.mem. The CXL.io protocol is based on the "
            "“Data Link Layer Specification” chapter of PCIe Base Specification; any deltas from PCIe Base "
            "Specification are described in this chapter. For CXL.cache and CXL.mem, the 68B flit format and "
            "256B flit format are specified. The flit packing rules for selecting transactions from internal "
            "queues to fill the slots in the flit are described. Other features described for 68B flit mode "
            "include the retry mechanism, link layer control flits, CRC calculation, and viral and poison.",
            "第 4.0 章“CXL 链路层”——链路层负责在 Flex Bus 链路上可靠传输事务层包。本章分节描述 CXL.io 以及 "
            "CXL.cache 与 CXL.mem。CXL.io 基于 PCIe 基础规范“数据链路层规范”章节；差异在本章说明。"
            "对 CXL.cache 与 CXL.mem，规定 68B 与 256B flit 格式，并描述从内部队列选择事务填充 flit 槽位的打包规则。"
            "对 68B flit 模式还描述重试机制、链路层控制 flit、CRC 计算，以及 viral 与 poison。",
        ),
        (
            "Chapter 5.0, “CXL ARB/MUX” – The ARB/MUX arbitrates between requests from the CXL link layers and "
            "multiplexes the data to forward to the physical layer. On the receiver side, the ARB/MUX decodes "
            "the flit to determine the target to forward transactions to the appropriate CXL link layer. "
            "Additionally, the ARB/MUX maintains virtual link state machines for every link layer it interfaces "
            "with, processing power state transition requests from the local link layers and generating ARB/MUX "
            "link management packets to communicate with the remote ARB/MUX.",
            "第 5.0 章“CXL ARB/MUX”——ARB/MUX 对来自 CXL 链路层的请求进行仲裁，并将数据复用后转发给物理层。"
            "在接收侧，ARB/MUX 解码 flit 以确定目标，并将事务转发到相应 CXL 链路层。此外，ARB/MUX 为其对接的"
            "每个链路层维护虚拟链路状态机，处理本地链路层的电源状态转换请求，并生成 ARB/MUX 链路管理包与远端 "
            "ARB/MUX 通信。",
        ),
        (
            "Chapter 6.0, “Flex Bus Physical Layer” – The Flex Bus physical layer is responsible for training "
            "the link to bring it to operational state for transmission of PCIe packets or CXL flits. During "
            "operational state, it prepares the data from the CXL link layers or the PCIe link layer for "
            "transmission across the Flex Bus link; likewise, it converts data received from the link to the "
            "appropriate format to pass on to the appropriate link layer. This chapter describes the deltas from "
            "PCIe Base Specification to support the CXL mode of operation. The framing of the CXL flits and the "
            "physical layer packet layout for 68B Flit mode as well as 256B Flit mode are described. The mode "
            "selection process to decide between CXL mode or PCIe mode, including hardware autonomous negotiation "
            "and software-controlled selection is also described. Finally, CXL low-latency modes are described.",
            "第 6.0 章“Flex Bus 物理层”——负责训练链路使其进入可传输 PCIe 包或 CXL flit 的运行状态。"
            "在运行状态中，它准备来自 CXL 链路层或 PCIe 链路层的数据以便在 Flex Bus 链路上传输；同样，它将从"
            "链路接收的数据转换为适当格式并交给相应链路层。本章描述相对 PCIe 基础规范为支持 CXL 模式所需的差异，"
            "说明 68B 与 256B Flit 模式下 CXL flit 成帧与物理层包布局，并描述在 CXL 与 PCIe 模式间选择的过程"
            "（含硬件自主协商与软件控制选择），最后描述 CXL 低延迟模式。",
        ),
        (
            "Chapter 7.0, “Switching” – This chapter provides an overview of different CXL switching "
            "configurations and describes rules for how to configure switches. Additionally, the Fabric Manager "
            "application interface is specified and CXL Fabric is introduced.",
            "第 7.0 章“交换”——概述不同 CXL 交换配置并描述交换机配置规则。此外规定结构管理器应用接口，并引入 "
            "CXL Fabric。",
        ),
        (
            "Chapter 8.0, “Control and Status Registers” – This chapter provides details of the Flex Bus and CXL "
            "control and status registers. It describes the configuration space and memory mapped registers that "
            "are located in various CXL components. It also describes the CXL Component Command Interface.",
            "第 8.0 章“控制与状态寄存器”——详述 Flex Bus 与 CXL 控制与状态寄存器，描述位于各 CXL 组件中的配置空间"
            "与内存映射寄存器，并描述 CXL 组件命令接口。",
        ),
        (
            "Chapter 9.0, “Reset, Initialization, Configuration, and Manageability” – This chapter describes the "
            "flows for boot, reset entry, and sleep-state entry; this includes the transactions sent across the "
            "link to initiate and acknowledge entry as well as steps taken by a CXL device to prepare for entry "
            "into each of these states. Additionally, this chapter describes the software enumeration model of "
            "both RCD and CXL virtual hierarchy and how the System Firmware view of the hierarchy may differ from "
            "the OS view. This chapter discusses the software view of CXL.mem, CXL extensions to Firmware-OS "
            "interfaces, and the CXL device manageability model.",
            "第 9.0 章“复位、初始化、配置与可管理性”——描述启动、进入复位与进入睡眠状态的流程，包括链路上用于"
            "发起并确认进入的事务，以及 CXL 设备为进入各状态所做准备。此外描述 RCD 与 CXL 虚拟层级的软件枚举模型，"
            "以及系统固件与操作系统对层级视图可能存在的差异；并讨论 CXL.mem 的软件视图、对固件-OS 接口的 CXL 扩展，"
            "以及 CXL 设备可管理性模型。",
        ),
        (
            "Chapter 10.0, “Power Management” – This chapter provides details on protocol specific link power "
            "management and physical layer power management. It describes the overall power management flow in "
            "three phases: protocol specific PM entry negotiation, PM entry negotiation for ARB/MUX interfaces "
            "(managed independently per protocol), and PM entry process for the physical layer. The PM entry "
            "process for CXL.cache and CXL.mem is slightly different than the process for CXL.io; these processes "
            "are described in separate subsections in this chapter.",
            "第 10.0 章“电源管理”——详述协议特定的链路电源管理与物理层电源管理。整体电源管理流程分三阶段："
            "协议特定的 PM 进入协商、ARB/MUX 接口的 PM 进入协商（按协议独立管理），以及物理层 PM 进入过程。"
            "CXL.cache 与 CXL.mem 的 PM 进入过程与 CXL.io 略有不同，分别在本章各小节描述。",
        ),
        (
            "Chapter 11.0, “CXL Security” – This chapter provides details on the CXL Integrity and Data "
            "Encryption (CXL IDE) scheme that is used for securing CXL protocol flits that are transmitted across "
            "the link, IDE modes, and configuration flows.",
            "第 11.0 章“CXL 安全”——详述用于保护链路上传输的 CXL 协议 flit 的 CXL 完整性与数据加密（CXL IDE）"
            "方案、IDE 模式与配置流程。",
        ),
        (
            "Chapter 12.0, “Reliability, Availability, and Serviceability” – This chapter describes the RAS "
            "capabilities supported by a CXL host, a CXL switch, and a CXL device. It describes how various types "
            "of errors are logged and signaled to the appropriate hardware or software error handling agent. It "
            "describes the Link Down flow and the viral handling expectation. Finally, it describes the error "
            "injection requirements.",
            "第 12.0 章“可靠性、可用性与可服务性”——描述 CXL 主机、交换机与设备支持的 RAS 能力；说明各类错误如何"
            "被记录并通告给相应硬件或软件错误处理代理；描述链路断开流程与 viral 处理期望；最后描述错误注入要求。",
        ),
        (
            "Chapter 13.0, “Performance Considerations” – This chapter describes hardware and software "
            "considerations for optimizing performance across the Flex Bus link in CXL mode. It also describes "
            "the performance monitoring infrastructure for CXL components.",
            "第 13.0 章“性能考虑”——描述在 CXL 模式下优化 Flex Bus 链路性能的硬件与软件考虑，并描述 CXL 组件的"
            "性能监控基础设施。",
        ),
        (
            "Chapter 14.0, “CXL Compliance Testing” – This chapter describes methodologies for ensuring that a "
            "device is compliant with the CXL specification.",
            "第 14.0 章“CXL 合规测试”——描述确保设备符合 CXL 规范的方法。",
        ),
    ]
    for en, zh in chapters:
        story.append(Paragraph("• " + esc(en), s["bullet_en"]))
        story.append(Paragraph("　" + esc(zh), s["bullet_zh"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("§ §", s["cover_sub"]))
    story.append(
        Paragraph(
            "— 第 1 章结束 / End of Chapter 1 —<br/>"
            "本中英对照译本依据 Evaluation Copy 生成，仅供学习参考；如与正式规范冲突，以原文为准。",
            s["note"],
        )
    )

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    # copy to artifacts
    ARTIFACT.write_bytes(OUT.read_bytes())
    print(f"Wrote {OUT}")
    print(f"Wrote {ARTIFACT}")
    print(f"Size: {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    build()
