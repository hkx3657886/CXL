#!/usr/bin/env python3
"""Generate Chinese-English bilingual PDF for CXL Spec eval excerpt (Rev 3.2)."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib import colors
import os

# Fonts
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
FALLBACK = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("CJK", FONT_PATH, subfontIndex=0))
else:
    pdfmetrics.registerFont(TTFont("CJK", FALLBACK))

# Colors
NAVY = HexColor("#1a365d")
TEAL = HexColor("#0d7377")
LIGHT_BG = HexColor("#f7fafc")
EN_BG = HexColor("#edf2f7")
ZH_BG = HexColor("#e6fffa")
BORDER = HexColor("#cbd5e0")
HEADER_BG = HexColor("#2c5282")
ACCENT = HexColor("#2b6cb0")

OUT = "/opt/cursor/artifacts/CXL_Specification_Rev3.2_Bilingual_ZH_EN.pdf"
OUT2 = "/workspace/cxl_bilingual/CXL_Specification_Rev3.2_Bilingual_ZH_EN.pdf"


def styles():
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName="CJK", fontSize=20, leading=28,
            textColor=NAVY, alignment=TA_CENTER, spaceAfter=8
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="CJK", fontSize=12, leading=18,
            textColor=TEAL, alignment=TA_CENTER, spaceAfter=4
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="CJK", fontSize=10, leading=14,
            textColor=HexColor("#4a5568"), alignment=TA_CENTER, spaceAfter=2
        ),
        "h1": ParagraphStyle(
            "h1", fontName="CJK", fontSize=14, leading=20,
            textColor=NAVY, spaceBefore=14, spaceAfter=8
        ),
        "h2": ParagraphStyle(
            "h2", fontName="CJK", fontSize=12, leading=17,
            textColor=ACCENT, spaceBefore=12, spaceAfter=6
        ),
        "h3": ParagraphStyle(
            "h3", fontName="CJK", fontSize=11, leading=15,
            textColor=TEAL, spaceBefore=10, spaceAfter=5
        ),
        "en": ParagraphStyle(
            "en", fontName="CJK", fontSize=8.5, leading=12,
            textColor=HexColor("#1a202c"), alignment=TA_JUSTIFY, spaceAfter=1,
            wordWrap="CJK",
        ),
        "zh": ParagraphStyle(
            "zh", fontName="CJK", fontSize=8.5, leading=12,
            textColor=HexColor("#234e52"), alignment=TA_JUSTIFY, spaceAfter=1,
            wordWrap="CJK",
        ),
        "label_en": ParagraphStyle(
            "label_en", fontName="CJK", fontSize=7, leading=9,
            textColor=HexColor("#718096"), spaceAfter=1
        ),
        "label_zh": ParagraphStyle(
            "label_zh", fontName="CJK", fontSize=7, leading=9,
            textColor=HexColor("#319795"), spaceAfter=1
        ),
        "caption": ParagraphStyle(
            "caption", fontName="CJK", fontSize=9, leading=12,
            textColor=HexColor("#4a5568"), spaceBefore=4, spaceAfter=8
        ),
        "note": ParagraphStyle(
            "note", fontName="CJK", fontSize=8, leading=11,
            textColor=HexColor("#744210"), alignment=TA_JUSTIFY, wordWrap="CJK",
        ),
        "footer": ParagraphStyle(
            "footer", fontName="CJK", fontSize=7, leading=9,
            textColor=HexColor("#718096"), alignment=TA_CENTER
        ),
        "toc": ParagraphStyle(
            "toc", fontName="CJK", fontSize=10, leading=16,
            textColor=HexColor("#2d3748"), leftIndent=10
        ),
        "cell": ParagraphStyle(
            "cell", fontName="CJK", fontSize=7.5, leading=10,
            textColor=black, wordWrap="CJK",
        ),
        "cell_h": ParagraphStyle(
            "cell_h", fontName="CJK", fontSize=7.5, leading=10,
            textColor=white, wordWrap="CJK",
        ),
    }


def esc(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def pair(en: str, zh: str, S) -> KeepTogether:
    """Side-by-side English | Chinese paragraph pair."""
    left = [
        Paragraph("<b>EN</b>", S["label_en"]),
        Paragraph(esc(en), S["en"]),
    ]
    right = [
        Paragraph("<b>中文</b>", S["label_zh"]),
        Paragraph(esc(zh), S["zh"]),
    ]
    t = Table(
        [[left, right]],
        colWidths=[88 * mm, 88 * mm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), EN_BG),
        ("BACKGROUND", (1, 0), (1, 0), ZH_BG),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return KeepTogether([t, Spacer(1, 3 * mm)])


def bullet_pair(en: str, zh: str, S) -> KeepTogether:
    return pair("• " + en, "• " + zh, S)


def heading(level: int, en: str, zh: str, S):
    key = {1: "h1", 2: "h2", 3: "h3"}[level]
    return Paragraph(f"{esc(en)} ｜ {esc(zh)}", S[key])


def figure_cap(en: str, zh: str, S):
    return Paragraph(
        f"<i>{esc(en)}</i><br/><i>{esc(zh)}</i>",
        S["caption"]
    )


def note_pair(en: str, zh: str, S):
    left = Paragraph(f"<b>Note:</b> {esc(en)}", S["note"])
    right = Paragraph(f"<b>注：</b>{esc(zh)}", S["note"])
    t = Table([[left, right]], colWidths=[88 * mm, 88 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fefcbf")),
        ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#d69e2e")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return KeepTogether([t, Spacer(1, 3 * mm)])


def simple_table(headers, rows, S, col_widths=None):
    """Bilingual table: each cell can be 'en / zh' or just text."""
    h = [Paragraph(esc(x), S["cell_h"]) for x in headers]
    data = [h]
    for row in rows:
        data.append([Paragraph(esc(c), S["cell"]) for c in row])
    if col_widths is None:
        w = 176 * mm / len(headers)
        col_widths = [w] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_BG))
    t.setStyle(TableStyle(style_cmds))
    return KeepTogether([t, Spacer(1, 4 * mm)])


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(HEADER_BG)
    canvas.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("CJK", 8)
    canvas.drawString(15 * mm, A4[1] - 9 * mm,
                      "CXL Spec Rev 3.2 ｜ 中英对照 Evaluation Copy")
    canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 9 * mm,
                           f"第 {doc.page} 页")
    canvas.setFillColor(HexColor("#e2e8f0"))
    canvas.rect(0, 0, A4[0], 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#718096"))
    canvas.setFont("CJK", 7)
    canvas.drawCentredString(
        A4[0] / 2, 4 * mm,
        "Compute Express Link Specification Rev 3.2 Ver 1.0 — 非官方中英对照译本（仅供学习参考）"
    )
    canvas.restoreState()


def build_content(S):
    story = []

    # ===== COVER =====
    story.append(Spacer(1, 25 * mm))
    story.append(Paragraph("Compute Express Link® Specification", S["cover_title"]))
    story.append(Paragraph("计算高速链路（CXL）规范", S["cover_title"]))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="80%", thickness=1.5, color=TEAL, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph("中英对照译本 ｜ Chinese–English Bilingual Edition", S["cover_sub"]))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Revision 3.2, Version 1.0 ｜ 修订版 3.2，版本 1.0", S["cover_meta"]))
    story.append(Paragraph("October 2, 2024 ｜ 2024年10月2日", S["cover_meta"]))
    story.append(Paragraph("Evaluation Copy Excerpt（评估副本摘录）", S["cover_meta"]))
    story.append(Paragraph("原文页码 Pages 81–100", S["cover_meta"]))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph(
        "涵盖内容 / Coverage：§2.5 Multi-Headed Device — §3.1.11 Host Management Flows of GFD",
        S["cover_meta"]
    ))
    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph(
        "声明：本文件为非官方翻译，仅供学习与技术参考。原文版权归 CXL Consortium 所有。"
        "术语尽量保留英文缩写（如 MH-SLD、CCI、PBR、GFD 等），并在首次出现时给出中文释义。",
        S["cover_meta"]
    ))
    story.append(PageBreak())

    # ===== TOC =====
    story.append(Paragraph("目录 ｜ Table of Contents", S["h1"]))
    toc_items = [
        "2.5 Multi-Headed Device ｜ 多头设备",
        "2.5.1 LD Management in MH-MLDs ｜ MH-MLD 中的逻辑设备管理",
        "2.6 CXL Device Scaling ｜ CXL 设备扩展",
        "2.7 CXL Fabric ｜ CXL 结构网络",
        "2.8 Global FAM (G-FAM) Type 3 Device ｜ 全局结构附加内存 Type 3 设备",
        "2.9 Manageability Overview ｜ 可管理性概述",
        "3.0 CXL Transaction Layer ｜ CXL 事务层",
        "3.1 CXL.io",
        "3.1.1 CXL.io Endpoint ｜ CXL.io 端点",
        "3.1.2 CXL Power Management VDM Format ｜ CXL 电源管理 VDM 格式",
        "3.1.2.1 Credit and PM Initialization ｜ 信用与电源管理初始化",
        "3.1.3 CXL Error VDM Format ｜ CXL 错误 VDM 格式",
        "3.1.4 Optional PCIe Features Required for CXL ｜ CXL 所需的可选 PCIe 特性",
        "3.1.5 Error Propagation ｜ 错误传播",
        "3.1.6 Memory Type Indication on ATS ｜ ATS 上的内存类型指示",
        "3.1.7 Deferrable Writes ｜ 可延迟写",
        "3.1.8 PBR TLP Header (PTH) ｜ PBR TLP 头",
        "3.1.9 VendPrefixL0",
        "3.1.10 CXL DevLoad (CDL) Field in UIO Completions ｜ UIO 完成中的 CDL 字段",
        "3.1.11 CXL Fabric-related VDMs ｜ CXL 结构相关 VDM",
        "3.1.11.1 Host Management Transaction Flows of GFD ｜ GFD 主机管理事务流",
    ]
    for item in toc_items:
        story.append(Paragraph("• " + esc(item), S["toc"]))
    story.append(PageBreak())

    # ===== CHAPTER: System Architecture =====
    story.append(Paragraph("第 2 章摘录 ｜ Chapter 2 Excerpt — CXL System Architecture", S["h1"]))
    story.append(heading(2, "2.5 Multi-Headed Device", "2.5 多头设备（Multi-Headed Device）", S))

    story.append(pair(
        "A Type 3 device with multiple CXL ports is considered a Multi-Headed Device. "
        "Each port is referred to as a “head”. There are two types of Multi-Headed Devices "
        "that are distinguished by how they present themselves on each head:",
        "带有多个 CXL 端口的 Type 3 设备被视为多头设备（Multi-Headed Device）。"
        "每个端口称为一个“头（head）”。多头设备有两种类型，按各头如何呈现自身加以区分：",
        S
    ))
    story.append(bullet_pair(
        "MH-SLD, which present SLDs on all heads",
        "MH-SLD：在所有头上呈现单逻辑设备（SLD）",
        S
    ))
    story.append(bullet_pair(
        "MH-MLD, which may present MLDs on any of their heads",
        "MH-MLD：可在其任一头上呈现多逻辑设备（MLD）",
        S
    ))
    story.append(pair(
        "Management of heads in Multi-Headed Devices follows the model defined for the device "
        "presented by that head:",
        "多头设备中各头的管理遵循该头所呈现设备类型所定义的模型：",
        S
    ))
    story.append(bullet_pair(
        "Heads that present SLDs may support the port management and control features that are available for SLDs",
        "呈现 SLD 的头可支持 SLD 可用的端口管理与控制特性",
        S
    ))
    story.append(bullet_pair(
        "Heads that present MLDs may support the port management and control features that are available for MLDs",
        "呈现 MLD 的头可支持 MLD 可用的端口管理与控制特性",
        S
    ))
    story.append(pair(
        "Management of memory resources in Multi-Headed Devices follows the model defined for MLD "
        "components because both MH-SLDs and MH-MLDs must support the isolation of memory resources, "
        "state, context, and management on a per-LD basis. LDs within the device are mapped to a single head.",
        "多头设备中内存资源的管理遵循为 MLD 组件定义的模型，因为 MH-SLD 与 MH-MLD 都必须支持按逻辑设备（LD）"
        "隔离内存资源、状态、上下文与管理。设备内的 LD 被映射到单个头。",
        S
    ))
    story.append(bullet_pair(
        "In MH-SLDs, there is a 1:1 mapping between heads and LDs.",
        "在 MH-SLD 中，头与 LD 之间为 1:1 映射。",
        S
    ))
    story.append(bullet_pair(
        "In MH-MLDs, multiple LDs are mapped to at most one head. A head in a Multi-Headed Device shall "
        "have at least one and no more than 16 LDs mapped. A head with one LD mapped shall present itself "
        "as an SLD and a head with more than one LD mapped shall present itself as an MLD. Each head may "
        "have a different number of LDs mapped to it.",
        "在 MH-MLD 中，多个 LD 最多映射到一个头。多头设备中的一个头应至少映射 1 个、至多映射 16 个 LD。"
        "仅映射一个 LD 的头应呈现为 SLD；映射多于一个 LD 的头应呈现为 MLD。各头映射的 LD 数量可以不同。",
        S
    ))
    story.append(pair(
        "Figure 2-7 and Figure 2-8 illustrate the mappings of LDs to heads for MH-SLDs and MH-MLDs, respectively.",
        "图 2-7 与图 2-8 分别示意 MH-SLD 与 MH-MLD 中 LD 到头的映射。",
        S
    ))
    story.append(figure_cap(
        "Figure 2-7. Head-to-LD Mapping in MH-SLDs",
        "图 2-7. MH-SLD 中头到 LD 的映射",
        S
    ))
    story.append(pair(
        "Multi-Headed Devices shall expose a dedicated Component Command Interface (CCI), the LD Pool CCI, "
        "for management of all LDs within the device. The LD Pool CCI may be exposed as an MCTP-based CCI or "
        "can be accessed via the Tunnel Management Command command through a head’s Mailbox CCI, as detailed "
        "in Section 7.6.7.3.1. The LD Pool CCI shall support the Tunnel Management Command for the purpose of "
        "tunneling management commands to all LDs within the device.",
        "多头设备应暴露专用的组件命令接口（CCI），即 LD 池 CCI，用于管理设备内全部 LD。"
        "LD 池 CCI 可作为基于 MCTP 的 CCI 暴露，也可通过某头的邮箱 CCI 经隧道管理命令（Tunnel Management Command）访问，"
        "详见第 7.6.7.3.1 节。LD 池 CCI 应支持隧道管理命令，以便向设备内全部 LD 隧道传输管理命令。",
        S
    ))
    story.append(pair(
        "The number of supported heads reported by a Multi-Headed Device shall remain constant. Devices that "
        "support proprietary mechanisms to dynamically reconfigure the number of accessible heads (e.g., dynamic "
        "bifurcation of 2 x8 ports into a single x16 head, etc.) shall report the maximum number of supported heads.",
        "多头设备所报告的支持头数量应保持恒定。若设备支持通过专有机制动态重配置可访问头数量"
        "（例如将 2 个 x8 端口动态分叉/合并为单个 x16 头等），则应报告所支持的最大头数量。",
        S
    ))

    story.append(heading(3, "2.5.1 LD Management in MH-MLDs", "2.5.1 MH-MLD 中的 LD 管理", S))
    story.append(pair(
        "The LD Pool in an MH-MLD may support more than 16 LDs. MLDs exposed via the heads of an MH-MLD use "
        "LD-IDs from 0 to n-1 relative to that head, where n is the number of LDs mapped to the head. The MH-MLD "
        "maps the LD-IDs received at a head to the device-wide LD index in the MH-MLD’s LD pool. The FMLD within "
        "each head of an MH-MLD shall expose and manage only the LDs that are mapped to that head.",
        "MH-MLD 中的 LD 池可支持超过 16 个 LD。经 MH-MLD 各头暴露的 MLD 使用相对于该头的 LD-ID（从 0 到 n-1），"
        "其中 n 为映射到该头的 LD 数量。MH-MLD 将某头收到的 LD-ID 映射到 MH-MLD 的 LD 池中设备范围的 LD 索引。"
        "MH-MLD 各头内的 FMLD 应仅暴露并管理映射到该头的 LD。",
        S
    ))
    story.append(pair(
        "An LD or FMLD on a head may permit visibility and management of all LDs within the device by using the "
        "Tunnel Management command to access the LD Pool CCI, as detailed in Section 7.6.7.3.1.",
        "某头上的 LD 或 FMLD 可通过隧道管理命令访问 LD 池 CCI，从而允许对设备内全部 LD 的可见性与管理，"
        "详见第 7.6.7.3.1 节。",
        S
    ))
    story.append(figure_cap(
        "Figure 2-8. Head-to-LD Mapping in MH-MLDs",
        "图 2-8. MH-MLD 中头到 LD 的映射",
        S
    ))

    story.append(heading(2, "2.6 CXL Device Scaling", "2.6 CXL 设备扩展", S))
    story.append(pair(
        "CXL supports the ability to connect up to 16 Type 1 and/or Type 2 devices below a VH. To support this "
        "scaling, the Type 2 devices are required to use BISnp channel in the CXL.mem protocol to manage coherence "
        "of the HDM region. The BISnp channel introduced in the CXL 3.0 specification definition replaces the use of "
        "CXL.cache protocol to manage coherence of the device’s HDM region. Type 2 devices that use CXL.cache for "
        "HDM-D coherence management are limited to a single device per Host bridge.",
        "CXL 支持在一个 VH（虚拟层次结构）下连接多达 16 个 Type 1 和/或 Type 2 设备。为支持此扩展，Type 2 设备"
        "须使用 CXL.mem 协议中的 BISnp 通道来管理 HDM 区域的一致性。CXL 3.0 规范引入的 BISnp 通道取代了使用 "
        "CXL.cache 协议管理设备 HDM 区域一致性的方式。使用 CXL.cache 进行 HDM-D 一致性管理的 Type 2 设备"
        "每个主机桥仅限一个设备。",
        S
    ))

    story.append(heading(2, "2.7 CXL Fabric", "2.7 CXL 结构网络（Fabric）", S))
    story.append(pair(
        "CXL Fabric describes features that rely on the Port Based Routing (PBR) messages and flows to enable "
        "scalable switching and advanced switching topologies. PBR enables a flexible low-latency architecture "
        "supporting up to 4096 PIDs in each fabric. G-FAM device attach (see Section 2.8) is supported natively "
        "into the fabric. Hosts and devices use standard messaging flows translated to and from PBR format through "
        "Edge Switches in the fabric. Section 7.7 defines the requirements and use cases.",
        "CXL Fabric 描述依赖基于端口路由（PBR）消息与流程的特性，以实现可扩展交换与高级交换拓扑。"
        "PBR 提供灵活的低延迟架构，每个结构网络最多支持 4096 个 PID。G-FAM 设备挂接（见第 2.8 节）被原生支持。"
        "主机与设备使用标准消息流，经结构网络中的边缘交换机（Edge Switch）在标准格式与 PBR 格式之间转换。"
        "第 7.7 节定义相关要求与用例。",
        S
    ))
    story.append(pair(
        "A CXL Fabric is a collection of one or more switches that are each PBR capable and interconnected with "
        "PBR links. A Domain is of a set of Host Ports and Devices within a single coherent Host Physical Address "
        "(HPA) space. A CXL Fabric connects one or more Host Ports to the devices within each Domain.",
        "CXL Fabric 是一个或多个均具备 PBR 能力、并以 PBR 链路互连的交换机集合。"
        "域（Domain）是位于单个一致主机物理地址（HPA）空间内的一组主机端口与设备。"
        "CXL Fabric 将一个或多个主机端口连接到各域内的设备。",
        S
    ))

    story.append(heading(2, "2.8 Global FAM (G-FAM) Type 3 Device",
                         "2.8 全局结构附加内存（G-FAM）Type 3 设备", S))
    story.append(pair(
        "A G-FAM device (GFD) is a Type 3 device that connects to a CXL Fabric using a PBR link and relies on PBR "
        "message formats to provide FAM with much-higher scalability compared to LD-FAM devices. The associated "
        "FM API documented in Section 8.2.10.9.10 and host mailbox interface details are provided in Section 7.7.14.",
        "G-FAM 设备（GFD）是一类 Type 3 设备，通过 PBR 链路连接到 CXL Fabric，并依赖 PBR 消息格式提供结构附加内存（FAM），"
        "其可扩展性远高于 LD-FAM 设备。相关 FM API 见第 8.2.10.9.10 节，主机邮箱接口细节见第 7.7.14 节。",
        S
    ))
    story.append(pair(
        "Like LD-FAM devices, GFDs can support pooled FAM, Shared FAM, or both. GFDs rely exclusively on the "
        "Dynamic Capacity mechanism for capacity management. See Section 7.7.2.3 for details and for other "
        "comparisons with LD-FAM devices.",
        "与 LD-FAM 设备类似，GFD 可支持池化 FAM、共享 FAM，或二者兼有。GFD 仅依赖动态容量（Dynamic Capacity）"
        "机制进行容量管理。细节及与 LD-FAM 设备的其他对比见第 7.7.2.3 节。",
        S
    ))

    story.append(heading(2, "2.9 Manageability Overview", "2.9 可管理性概述", S))
    story.append(pair(
        "To allow for different types of managed systems, CXL supports multiple types of management interfaces "
        "and management interconnects. Some are defined by external standards, while some are defined in the "
        "CXL specification.",
        "为适应不同类型的受管系统，CXL 支持多种管理接口与管理互连。部分由外部标准定义，部分在 CXL 规范中定义。",
        S
    ))
    story.append(pair(
        "CXL component discovery, enumeration, and basic configuration are defined by PCI-SIG* and CXL "
        "specifications. These functions are accomplished via access to Configuration Space structures and "
        "associated MMIO structures.",
        "CXL 组件发现、枚举与基本配置由 PCI-SIG* 与 CXL 规范定义。这些功能通过访问配置空间结构及相关 MMIO 结构完成。",
        S
    ))
    story.append(pair(
        "Security authentication and data integrity/encryption management are defined in PCI-SIG, DMTF, and CXL "
        "specifications. The associated management traffic is transported either via Data Object Exchange (DOE) "
        "using Configuration Space, or via MCTP-based transports. The latter can operate in-band using PCIe VDMs, "
        "or out-of-band using management interconnects such as SMBus, I3C, or dedicated PCIe links.",
        "安全认证与数据完整性/加密管理由 PCI-SIG、DMTF 与 CXL 规范定义。相关管理流量可通过使用配置空间的数据对象交换（DOE）"
        "传输，也可通过基于 MCTP 的传输。后者可带内使用 PCIe VDM，或带外使用 SMBus、I3C 或专用 PCIe 链路等管理互连。",
        S
    ))
    story.append(pair(
        "The Manageability Model for CXL Devices is covered in Section 9.19. Advanced CXL-specific component "
        "management is handled using one or more CCIs, which are covered in Section 9.20. CCI commands fall into "
        "4 broad sets:",
        "CXL 设备的可管理性模型见第 9.19 节。高级 CXL 专用组件管理通过一个或多个 CCI 处理，见第 9.20 节。"
        "CCI 命令分为四大类：",
        S
    ))
    for en, zh in [
        ("Generic Component commands", "通用组件命令"),
        ("Memory Device commands", "内存设备命令"),
        ("FM API commands", "结构管理器 API（FM API）命令"),
        ("Vendor Specific commands", "厂商专用命令"),
    ]:
        story.append(bullet_pair(en, zh, S))
    story.append(pair(
        "All 4 sets are covered in Section 8.2.10, specifically:",
        "上述四类均在第 8.2.10 节涵盖，具体包括：",
        S
    ))
    for en, zh in [
        ("Command and capability determination", "命令与能力判定"),
        ("Command foreground and background operation", "命令前台与后台操作"),
        ("Event logging, notification, and log retrieval", "事件记录、通知与日志检索"),
        ("Interactions when a component has multiple CCIs", "组件具有多个 CCI 时的交互"),
    ]:
        story.append(bullet_pair(en, zh, S))
    story.append(pair(
        "Each command is mandatory, optional, or prohibited, based on the component type and other attributes. "
        "Commands can be sent to devices, switches, or both.",
        "每条命令根据组件类型及其他属性为强制、可选或禁止。命令可发送至设备、交换机，或两者。",
        S
    ))
    story.append(pair(
        "CCIs use several transports and interconnects to accomplish their operations. The mailbox mechanism is "
        "covered in Section 8.2.9.4, and mailboxes are accessed via an architected MMIO register interface. "
        "MCTP-based transports use PCIe VDMs in-band or any of the previously mentioned out-of-band management "
        "interconnects. FM API commands can be tunneled to MLDs and GFDs via CXL switches. Configuration and "
        "MMIO accesses can be tunneled to LDs within MLDs via CXL switches.",
        "CCI 使用多种传输与互连完成操作。邮箱机制见第 8.2.9.4 节，邮箱通过体系结构定义的 MMIO 寄存器接口访问。"
        "基于 MCTP 的传输可带内使用 PCIe VDM，或使用前述任一带外管理互连。FM API 命令可经 CXL 交换机隧道传输至 "
        "MLD 与 GFD。配置与 MMIO 访问可经 CXL 交换机隧道传输至 MLD 内的 LD。",
        S
    ))
    story.append(pair(
        "DMTF’s Platform-Level Data Model (PLDM) is used for platform monitoring and control, and can be used "
        "for component firmware updates. PLDM may use MCTP to communicate with target CXL components.",
        "DMTF 的平台级数据模型（PLDM）用于平台监控与控制，也可用于组件固件更新。PLDM 可使用 MCTP 与目标 CXL 组件通信。",
        S
    ))
    story.append(pair(
        "Given CXL’s use of multiple manageability standards and interconnects, it is important to consider "
        "interoperability when designing a system that incorporates CXL components.",
        "鉴于 CXL 使用多种可管理性标准与互连，在设计包含 CXL 组件的系统时，必须考虑互操作性。",
        S
    ))
    story.append(Paragraph("§ §", S["cover_meta"]))
    story.append(PageBreak())

    # ===== CHAPTER 3 =====
    story.append(Paragraph("第 3 章 ｜ Chapter 3 — CXL Transaction Layer（CXL 事务层）", S["h1"]))
    story.append(heading(2, "3.0 CXL Transaction Layer", "3.0 CXL 事务层", S))
    story.append(heading(2, "3.1 CXL.io", "3.1 CXL.io", S))
    story.append(pair(
        "CXL.io provides a non-coherent load/store interface for I/O devices. Figure 3-1 shows where the CXL.io "
        "transaction layer exists in the Flex Bus layered hierarchy. Transaction types, transaction packet "
        "formatting, credit-based flow control, virtual channel management, and transaction ordering rules follow "
        "the PCIe* definition; please refer to the “Transaction Layer Specification” chapter of PCIe Base "
        "Specification for details. This chapter highlights notable PCIe modes or features that are used for CXL.io.",
        "CXL.io 为 I/O 设备提供非一致性的 load/store 接口。图 3-1 显示 CXL.io 事务层在 Flex Bus 分层层次中的位置。"
        "事务类型、事务包格式、基于信用的流控、虚拟通道管理与事务排序规则遵循 PCIe* 定义；细节请参阅 PCIe 基础规范"
        "中的“事务层规范”章节。本章重点说明用于 CXL.io 的重要 PCIe 模式或特性。",
        S
    ))
    story.append(figure_cap(
        "Figure 3-1. Flex Bus Layers - CXL.io Transaction Layer Highlighted",
        "图 3-1. Flex Bus 各层 — 突出显示 CXL.io 事务层",
        S
    ))

    story.append(heading(3, "3.1.1 CXL.io Endpoint", "3.1.1 CXL.io 端点", S))
    story.append(pair(
        "The CXL Alternate Protocol negotiation determines the mode of operation. See Section 9.11 and Section 9.12 "
        "for descriptions of how CXL devices are enumerated with the help of CXL.io.",
        "CXL 备用协议协商决定工作模式。关于如何借助 CXL.io 枚举 CXL 设备，见第 9.11 与 9.12 节。",
        S
    ))
    story.append(pair(
        "A Function on a CXL device must not generate INTx messages if that Function participates in CXL.cache "
        "protocol or CXL.mem protocols. A Non-CXL Function Map DVSEC (see Section 8.1.4) enumerates functions that "
        "do not participate in CXL.cache or CXL.mem. Even though not recommended, these non-CXL functions are "
        "permitted to generate INTx messages.",
        "若 CXL 设备上的某功能（Function）参与 CXL.cache 或 CXL.mem 协议，则不得生成 INTx 消息。"
        "非 CXL 功能映射 DVSEC（见第 8.1.4 节）枚举不参与 CXL.cache 或 CXL.mem 的功能。"
        "尽管不推荐，这些非 CXL 功能允许生成 INTx 消息。",
        S
    ))
    story.append(pair(
        "Functions associated with an LD within an MLD component, including non-CXL functions, are not permitted "
        "to generate INTx messages.",
        "与 MLD 组件内 LD 相关联的功能（包括非 CXL 功能）不允许生成 INTx 消息。",
        S
    ))

    story.append(heading(3, "3.1.2 CXL Power Management VDM Format",
                         "3.1.2 CXL 电源管理 VDM 格式", S))
    story.append(pair(
        "The CXL power management messages are sent as PCIe Vendor Defined Type 0 messages with a 4-DWORD data "
        "payload. These include the PMREQ, PMRSP, and PMGO messages. Figure 3-2 and Figure 3-3 provide the format "
        "for the CXL PM VDMs. The following are the characteristics of these messages:",
        "CXL 电源管理消息以带有 4 DWORD 数据载荷的 PCIe 厂商定义 Type 0 消息发送，包括 PMREQ、PMRSP 与 PMGO。"
        "图 3-2 与图 3-3 给出 CXL PM VDM 的格式。这些消息的特征如下：",
        S
    ))
    for en, zh in [
        ("Fmt and Type fields are set to indicate message with data. All messages use routing of "
         "“Local-Terminate at Receiver.” Message Code is set to Vendor Defined Type 0.",
         "Fmt 与 Type 字段设置为指示带数据的消息。所有消息使用“本地—在接收端终止（Local-Terminate at Receiver）”路由。"
         "Message Code 设为 Vendor Defined Type 0。"),
        ("Vendor ID field is set to 1E98h.",
         "Vendor ID 字段设为 1E98h。"),
        ("Byte 15 of the message header contains the VDM Code and is set to the value of “CXL PM Message” (68h).",
         "消息头第 15 字节包含 VDM Code，设为“CXL PM Message”（68h）。"),
        ("The 4-DWORD Data Payload contains the CXL PM Logical Opcode (e.g., PMREQ, GPF) and any other "
         "information related to the CXL PM message. Details of fields within the Data Payload are described in Table 3-1.",
         "4 DWORD 数据载荷包含 CXL PM 逻辑操作码（如 PMREQ、GPF）及与 CXL PM 消息相关的其他信息。"
         "数据载荷内字段细节见表 3-1。"),
    ]:
        story.append(bullet_pair(en, zh, S))
    story.append(pair(
        "If a CXL component receives PM VDM with poison (EP=1), the receiver shall drop such a message. Because "
        "the receiver is able to continue regular operation after receiving such a VDM, it shall treat this event "
        "as an advisory non-fatal error.",
        "若 CXL 组件收到带毒（poison，EP=1）的 PM VDM，接收方应丢弃该消息。由于接收方可在收到此类 VDM 后继续正常操作，"
        "应将此事件视为建议性非致命错误（advisory non-fatal error）。",
        S
    ))
    story.append(pair(
        "If the receiver Power Management Unit (PMU) does not understand the contents of PM VDM Payload, it shall "
        "silently drop that message and shall not signal an uncorrectable error.",
        "若接收方电源管理单元（PMU）无法理解 PM VDM 载荷内容，应静默丢弃该消息，且不得发出不可纠正错误信号。",
        S
    ))
    story.append(note_pair(
        "NOTICE TO USERS: THE UNIQUE VALUE THAT IS PROVIDED IN THIS CXL SPECIFICATION IS FOR USE IN VENDOR "
        "DEFINED MESSAGE FIELDS, DESIGNATED VENDOR SPECIFIC EXTENDED CAPABILITIES, AND ALTERNATE PROTOCOL "
        "NEGOTIATION ONLY AND MAY NOT BE USED IN ANY OTHER MANNER... (full legal notice abbreviated; see original).",
        "用户须知：本 CXL 规范提供的唯一值仅可用于厂商定义消息字段、指定厂商专用扩展能力以及备用协议协商，"
        "不得以任何其他方式使用……（完整法律声明见原文脚注；此处从略）。",
        S
    ))
    story.append(figure_cap(
        "Figure 3-2 / 3-3. CXL Power Management Messages Packet Format (Non-Flit / Flit Mode)",
        "图 3-2 / 3-3. CXL 电源管理消息包格式（非 Flit / Flit 模式）",
        S
    ))

    # Table 3-1
    story.append(Paragraph("Table 3-1. CXL Power Management Messages - Data Payload Field Definitions ｜ "
                           "表 3-1. CXL 电源管理消息 — 数据载荷字段定义", S["h3"]))
    story.append(simple_table(
        ["Field 字段", "Description 描述", "Notes 说明"],
        [
            ["PM Logical Opcode[7:0]\n电源管理逻辑操作码",
             "Power Management Command\n00h=AGENT_INFO; 02h=RESETPREP; 04h=PMREQ (PMRSP/PMGO); "
             "06h=GPF; FEh=CREDIT_RTN",
             "—"],
            ["PM Agent ID[6:0]\nPM 代理 ID",
             "PM2IP: Reserved（保留）\nIP2PM: 分配给设备的 PM agent ID。主机通过首条 CREDIT_RTN 的 "
             "TARGET_AGENT_ID 字段将 PM Agent ID 告知设备。",
             "设备从主机收到消息时不消费此值。"],
            ["Parameter[15:0]\n参数",
             "CREDIT_RTN: Reserved\n"
             "AGENT_INFO: Bit[0] REQUEST/RESPONSE_N; Bits[7:1] INDEX; Bits[15:8] Reserved\n"
             "PMREQ: Bit[0] REQUEST/RESPONSE_N; Bit[2] GO; Bits[15:3] Reserved\n"
             "RESETPREP / GPF: Bit[0] REQUEST/RESPONSE_N; Bits[15:1] Reserved",
             "—"],
            ["Payload[95:0]\n载荷",
             "CREDIT_RTN: Bits[7:0] NUM_CREDITS; Bits[14:8] TARGET_AGENT_ID（仅首条 PM2IP 有效）; Bit[15] Reserved\n"
             "AGENT_INFO (Index==0): Bits[7:0] CAPABILITY_VECTOR — Bit0 支持 CXL 1.1 PM; Bit1 支持 GPF\n"
             "RESETPREP: ResetType (01h S0→S1, 03h S0→S3, 04h S0→S4, 05h S0→S5, 10h System reset); PrepType 00h=General Prep\n"
             "PMREQ: Bits[31:0] PCIe LTR format（见表 3-2）\n"
             "GPF: GPFType / GPF Status / Phase（01h Phase1, 02h Phase2）",
             "向主机归还信用时，CXL Agent 须将 TARGET_AGENT_ID 视为保留。AGENT_INFO 仅定义 Index 0。"],
        ],
        S,
        col_widths=[40 * mm, 95 * mm, 41 * mm],
    ))

    story.append(heading(3, "3.1.2.1 Credit and PM Initialization",
                         "3.1.2.1 信用与电源管理初始化", S))
    story.append(pair(
        "PM Credits and initialization process is link local. Figure 3-4 illustrates the use of PM2IP.CREDIT_RTN "
        "and PM2IP.AGENT_INFO messages to initialize Power Management messaging protocol intended to facilitate "
        "communication between the Downstream Port PMU and the Upstream Port PMU. A CXL switch provides an "
        "aggregation function for PM messages as described in Section 9.1.2.1.",
        "PM 信用与初始化过程是链路本地的。图 3-4 说明如何使用 PM2IP.CREDIT_RTN 与 PM2IP.AGENT_INFO 消息初始化"
        "电源管理消息协议，以促进下游端口 PMU 与上游端口 PMU 之间的通信。CXL 交换机对 PM 消息提供聚合功能，见第 9.1.2.1 节。",
        S
    ))
    story.append(pair(
        "GPF messages do not require credits and the receiver shall not generate CREDIT_RTN in response to GPF messages.",
        "GPF 消息不需要信用，接收方不得因 GPF 消息而生成 CREDIT_RTN。",
        S
    ))
    story.append(pair(
        "The CXL Upstream Port PMU must be able to receive and process CREDIT_RTN messages without dependency on "
        "any other PM2IP messages. Also, CREDIT_RTN messages do not use a credit. The CREDIT_RTN messages are used "
        "to initialize and update the Tx credits on each side, so that flow control can be appropriately managed. "
        "During the first CREDIT_RTN message during PM Initialization, the credits being sent via NUM_CREDITS field "
        "represent the number of credit-dependent PM messages that the initiator of CREDIT_RTN can receive from the "
        "other end. During the subsequent CREDIT_RTN messages, the NUM_CREDITS field represents the number of PM "
        "credits that were freed up since the last CREDIT_RTN message in the same direction. The first CREDIT_RTN "
        "message is also used by the Downstream Port PMU to assign a PM_AGENT_ID to the Upstream Port PMU. This ID "
        "is communicated via the TARGET_AGENT_ID field in the CREDIT_RTN message. The Upstream Port PMU must wait "
        "for the CREDIT_RTN message from the Downstream Port PMU before initiating any IP2PM messages.",
        "CXL 上游端口 PMU 必须能够接收并处理 CREDIT_RTN 消息，且不依赖任何其他 PM2IP 消息。CREDIT_RTN 消息本身不占用信用。"
        "CREDIT_RTN 用于初始化并更新双方的发送（Tx）信用，以便正确管理流控。PM 初始化期间首条 CREDIT_RTN 中，"
        "经 NUM_CREDITS 字段发送的信用表示 CREDIT_RTN 发起方能从对端接收多少依赖信用的 PM 消息。"
        "后续 CREDIT_RTN 中，NUM_CREDITS 表示自同方向上一条 CREDIT_RTN 以来释放的 PM 信用数。"
        "首条 CREDIT_RTN 亦由下游端口 PMU 用于向上游端口 PMU 分配 PM_AGENT_ID，通过 TARGET_AGENT_ID 字段传递。"
        "上游端口 PMU 必须等待来自下游端口 PMU 的 CREDIT_RTN 消息后，方可发起任何 IP2PM 消息。",
        S
    ))
    story.append(pair(
        "An Upstream Port PMU must support at least one credit, where a credit implies having sufficient buffering "
        "to sink a PM2IP message with 128 bits of payload.",
        "上游端口 PMU 必须至少支持一个信用；一个信用意味着具备足够缓冲以接收（sink）带有 128 比特载荷的 PM2IP 消息。",
        S
    ))

    story.append(Paragraph("Table 3-2. PMREQ Field Definitions ｜ 表 3-2. PMREQ 字段定义", S["h3"]))
    story.append(simple_table(
        ["Payload Bit Position 载荷位", "LTR Field LTR 字段"],
        [
            ["[31:24]", "Snoop Latency[7:0]"],
            ["[23:16]", "Snoop Latency[15:8]"],
            ["[15:8]", "No-Snoop Latency[7:0]"],
            ["[7:0]", "No-Snoop Latency[15:8]"],
        ],
        S,
        col_widths=[70 * mm, 106 * mm],
    ))
    story.append(figure_cap(
        "Figure 3-4. Power Management Credits and Initialization",
        "图 3-4. 电源管理信用与初始化",
        S
    ))

    story.append(pair(
        "After credit initialization, the Upstream Port PMU must wait for an AGENT_INFO message from the "
        "Downstream Port PMU. This message contains the CAPABILITY_VECTOR of the PM protocol of the Downstream "
        "Port PMU. Upstream Port PMU must send its CAPABILITY_VECTOR to the Downstream Port PMU in response to "
        "the AGENT_INFO Req from the Downstream Port PMU. When there is a mismatch, Downstream Port PMU may "
        "implement a compatibility mode to work with a less capable Upstream Port PMU. Alternatively, Downstream "
        "Port PMU may log the mismatch and report an error, if it does not know how to reliably function with a "
        "less capable Upstream Port PMU.",
        "信用初始化后，上游端口 PMU 必须等待来自下游端口 PMU 的 AGENT_INFO 消息。该消息包含下游端口 PMU 的 PM 协议 "
        "CAPABILITY_VECTOR。上游端口 PMU 必须响应该 AGENT_INFO 请求，将其 CAPABILITY_VECTOR 发送给下游端口 PMU。"
        "若能力不匹配，下游端口 PMU 可实现兼容模式以与能力较弱的上游端口 PMU 协作；或者，若无法可靠地与较弱上游端口 "
        "PMU 工作，则可记录不匹配并报告错误。",
        S
    ))
    story.append(pair(
        "There is an expectation from the Upstream Port PMU that it restores credits to the Downstream Port PMU "
        "as soon as a message is received. Downstream Port PMU can have multiple messages in flight, if it was "
        "provided with multiple credits. Releasing credits in a timely manner provides better performance for "
        "latency sensitive flows.",
        "期望上游端口 PMU 在收到消息后尽快向下游端口 PMU 归还信用。若下游端口 PMU 获分配多个信用，则可有多条消息在途。"
        "及时释放信用可为延迟敏感流提供更好性能。",
        S
    ))
    story.append(pair(
        "The following list summarizes the rules that must be followed by an Upstream Port PMU:",
        "以下列表汇总上游端口 PMU 必须遵循的规则：",
        S
    ))
    for en, zh in [
        ("Upstream Port PMU must wait to receive a PM2IP.CREDIT_RTN message before initiating any IP2PM messages.",
         "上游端口 PMU 必须先收到 PM2IP.CREDIT_RTN 消息，方可发起任何 IP2PM 消息。"),
        ("Upstream Port PMU must extract TARGET_AGENT_ID field from the first PM2IP message received from the "
         "Downstream Port PMU and use that as its PM_AGENT_ID in future messages.",
         "上游端口 PMU 必须从下游端口 PMU 收到的首条 PM2IP 消息中提取 TARGET_AGENT_ID，并在后续消息中用作其 PM_AGENT_ID。"),
        ("Upstream Port PMU must implement enough resources to sink and process any CREDIT_RTN messages without "
         "dependency on any other PM2IP or IP2PM messages or other message classes.",
         "上游端口 PMU 必须实现足够资源以接收并处理任何 CREDIT_RTN 消息，且不依赖其他 PM2IP/IP2PM 消息或其他消息类。"),
        ("Upstream Port PMU must implement at least one credit to sink a PM2IP message.",
         "上游端口 PMU 必须至少实现一个信用以接收 PM2IP 消息。"),
        ("Upstream Port PMU must return any credits to the Downstream Port PMU as soon as possible to prevent "
         "blocking of PM message communication over CXL Link.",
         "上游端口 PMU 必须尽快向下游端口 PMU 归还信用，以防阻塞 CXL 链路上的 PM 消息通信。"),
        ("Upstream Port PMU are recommended to not withhold a credit for longer than 10 us.",
         "建议上游端口 PMU 扣留信用不超过 10 μs。"),
    ]:
        story.append(bullet_pair(en, zh, S))

    story.append(heading(3, "3.1.3 CXL Error VDM Format", "3.1.3 CXL 错误 VDM 格式", S))
    story.append(pair(
        "The CXL Error Messages are sent as PCIe Vendor Defined Type 0 messages with no data payload. Presently, "
        "this class includes a single type of message, namely Event Firmware Notification (EFN). When EFN is "
        "utilized to report memory errors, it is referred to as Memory Error Firmware Notification (MEFN). "
        "Figure 3-5 and Figure 3-6 provide the format for EFN messages.",
        "CXL 错误消息以无数据载荷的 PCIe 厂商定义 Type 0 消息发送。目前该类仅包含一种消息：事件固件通知（EFN）。"
        "当 EFN 用于报告内存错误时，称为内存错误固件通知（MEFN）。图 3-5 与图 3-6 给出 EFN 消息格式。",
        S
    ))
    story.append(pair("The following are the characteristics of the EFN message:",
                      "EFN 消息的特征如下：", S))
    for en, zh in [
        ("Fmt and Type fields are set to indicate message with no data.",
         "Fmt 与 Type 字段设置为指示无数据消息。"),
        ("The message is sent using routing of “Routed to Root Complex.” It is always initiated by a device.",
         "消息使用“路由至根复合体（Routed to Root Complex）”路由，始终由设备发起。"),
        ("Message Code is set to Vendor Defined Type 0.",
         "Message Code 设为 Vendor Defined Type 0。"),
        ("Vendor ID field is set to 1E98h.",
         "Vendor ID 字段设为 1E98h。"),
        ("Byte 15 of the message header contains the VDM Code and is set to the value of “CXL Error Message” (00h).",
         "消息头第 15 字节含 VDM Code，设为“CXL Error Message”（00h）。"),
        ("Bytes 8, 9, 12, and 13 are cleared to all 0s.",
         "第 8、9、12、13 字节清零。"),
        ("Bits[7:4] of Byte 14 are cleared to 0h. Bits[3:0] of Byte 14 are used to communicate the Firmware "
         "Interrupt Vector (abbreviated as FW Interrupt Vector in Figure 3-5 and Figure 3-6).",
         "第 14 字节 Bits[7:4] 清为 0h；Bits[3:0] 用于传递固件中断向量（图 3-5/3-6 中缩写为 FW Interrupt Vector）。"),
    ]:
        story.append(bullet_pair(en, zh, S))
    story.append(pair(
        "Encoding of the FW Interrupt Vector field is Host specific and thus not defined by the CXL specification. "
        "A Host may support more than one type of Firmware environment and this field may be used to indicate to "
        "the Host which one of these environments is to process this message.",
        "FW Interrupt Vector 字段的编码为主机特定，故不由 CXL 规范定义。主机可能支持多种固件环境，该字段可用于指示"
        "应由哪一种环境处理本消息。",
        S
    ))
    story.append(figure_cap(
        "Figure 3-5 / 3-6. CXL EFN Messages Packet Format (Non-Flit / Flit Mode)",
        "图 3-5 / 3-6. CXL EFN 消息包格式（非 Flit / Flit 模式）",
        S
    ))

    story.append(heading(3, "3.1.4 Optional PCIe Features Required for CXL",
                         "3.1.4 CXL 所需的可选 PCIe 特性", S))
    story.append(pair(
        "Table 3-3 lists optional features per PCIe Base Specification that are required for CXL.",
        "表 3-3 列出按 PCIe 基础规范为可选、但对 CXL 为必需的特性。",
        S
    ))
    story.append(simple_table(
        ["Optional PCIe Feature 可选 PCIe 特性", "Notes 说明"],
        [
            ["Data Poisoning by transmitter\n发送方数据加毒", "—"],
            ["ATS", "仅当存在 CXL.cache 时需要（例如 Type 1/2 设备，而非 Type 3）"],
            ["Advanced Error Reporting (AER)\n高级错误报告", "—"],
        ],
        S,
        col_widths=[80 * mm, 96 * mm],
    ))

    story.append(heading(3, "3.1.5 Error Propagation", "3.1.5 错误传播", S))
    story.append(pair(
        "CXL.cache and CXL.mem errors detected by the device are propagated Upstream over the CXL.io traffic "
        "stream. These errors are logged as correctable and uncorrectable internal errors in the PCIe AER "
        "registers of the detecting component.",
        "设备检测到的 CXL.cache 与 CXL.mem 错误经 CXL.io 流量流向上游传播。这些错误在检测组件的 PCIe AER 寄存器中"
        "记录为可纠正与不可纠正内部错误。",
        S
    ))

    story.append(heading(3, "3.1.6 Memory Type Indication on ATS",
                         "3.1.6 ATS 上的内存类型指示", S))
    story.append(pair(
        "Requests to certain memory regions can only be issued on CXL.io and cannot be issued on CXL.cache. It is "
        "up to the host to decide what these memory regions are. For example, on x86 systems, the host may choose "
        "to restrict access only to Uncacheable (UC) type memory over CXL.io. The host indicates such regions by "
        "means of an indication on ATS completion to the device.",
        "对某些内存区域的请求只能在 CXL.io 上发出，不能在 CXL.cache 上发出。具体哪些区域由主机决定。"
        "例如在 x86 系统上，主机可选择仅允许经 CXL.io 访问不可缓存（UC）类型内存。主机通过 ATS 完成指示将该信息告知设备。",
        S
    ))
    story.append(pair(
        "All CXL functions that issue ATS requests must set the Page Aligned Request bit in the ATS Capability "
        "register to 1. In addition, ATS requests sourced from a CXL device must set the CXL Src bit.",
        "所有发出 ATS 请求的 CXL 功能必须将 ATS Capability 寄存器中的 Page Aligned Request 位置 1。"
        "此外，源自 CXL 设备的 ATS 请求必须置位 CXL Src 位。",
        S
    ))
    story.append(pair(
        "DWORD3, Byte 3, Bit 3 in ATS 64-bit request and ATS 32-bit request for both Flit Mode and Non-Flit Mode "
        "carries the CXL Src bit. Figure 3-7 shows the position of this bit in ATS 64-bit request (Non-Flit mode). "
        "See PCIe Base Specification for the format of the other request messages. The CXL Src bit is defined as follows:",
        "在 Flit 与非 Flit 模式下，ATS 64 位请求与 ATS 32 位请求的 DWORD3、Byte 3、Bit 3 携带 CXL Src 位。"
        "图 3-7 显示该位在 ATS 64 位请求（非 Flit 模式）中的位置。其他请求消息格式见 PCIe 基础规范。CXL Src 位定义如下：",
        S
    ))
    story.append(bullet_pair(
        "0 = Indicates request initiated by a Function that does not support CXL.io Indication on ATS.",
        "0 = 表示由不支持 ATS 上 CXL.io 指示的功能发起的请求。",
        S
    ))
    story.append(bullet_pair(
        "1 = Indicates request initiated by a Function that supports CXL.io Indication on ATS. All CXL Functions must set this bit.",
        "1 = 表示由支持 ATS 上 CXL.io 指示的功能发起的请求。所有 CXL 功能必须置该位。",
        S
    ))
    story.append(note_pair(
        "This bit is Reserved in the ATS request as defined by PCIe Base Specification.",
        "该位在 PCIe 基础规范定义的 ATS 请求中为保留位。",
        S
    ))
    story.append(pair(
        "ATS translation completion from the Host carries the CXL.io bit in the Translation Completion Data Entry. "
        "See PCIe Base Specification for the message formats. The CXL.io bit in the ATS Translation completion is "
        "valid when the CXL Src bit in the request is set. The CXL.io bit is as defined as follows:",
        "来自主机的 ATS 转换完成在转换完成数据项中携带 CXL.io 位。消息格式见 PCIe 基础规范。"
        "当请求中 CXL Src 位置位时，ATS 转换完成中的 CXL.io 位有效。定义如下：",
        S
    ))
    story.append(bullet_pair(
        "0 = Requests to the page can be issued on all CXL protocols.",
        "0 = 对该页的请求可在所有 CXL 协议上发出。",
        S
    ))
    story.append(bullet_pair(
        "1 = Requests to the page can be issued by the Function on CXL.io only. It is a violation to issue "
        "requests to the page using CXL.cache protocol.",
        "1 = 功能仅可在 CXL.io 上对该页发出请求。使用 CXL.cache 协议对该页发出请求属于违规。",
        S
    ))
    story.append(figure_cap(
        "Figure 3-7. ATS 64-bit Request with CXL Indication - Non-Flit Mode",
        "图 3-7. 带 CXL 指示的 ATS 64 位请求 — 非 Flit 模式",
        S
    ))

    story.append(heading(3, "3.1.7 Deferrable Writes", "3.1.7 可延迟写（Deferrable Writes）", S))
    story.append(pair(
        "Earlier revisions of this specification captured the “Deferrable Writes” extension to the CXL.io protocol, "
        "but this protocol has been adopted by PCIe Base Specification.",
        "本规范早期修订版收录了 CXL.io 协议的“可延迟写”扩展，但该协议已被 PCIe 基础规范采纳。",
        S
    ))

    story.append(heading(3, "3.1.8 PBR TLP Header (PTH)", "3.1.8 PBR TLP 头（PTH）", S))
    story.append(pair(
        "On PBR links in a PBR fabric, all .io TLPs, with exception of NOP-TLP, carry a fixed 1-DWORD header field "
        "called the PBR TLP header (PTH). PBR links are either Inter-Switch Links (ISL) or edge links from PBR "
        "switch to G-FAM. See Section 7.7.8 for details of where this header is inserted and deleted when the .io "
        "TLP traverses the PBR fabric from source to target.",
        "在 PBR 结构网络中的 PBR 链路上，除 NOP-TLP 外，所有 .io TLP 携带固定 1 DWORD 的头字段，称为 PBR TLP 头（PTH）。"
        "PBR 链路可以是交换机间链路（ISL），或从 PBR 交换机到 G-FAM 的边缘链路。.io TLP 从源到目标穿越 PBR 结构网络时"
        "该头的插入与删除位置详见第 7.7.8 节。",
        S
    ))
    story.append(pair(
        "NOP-TLPs are always transmitted without a preceding PTH. For Non-NOP-TLPs, PTH is always transmitted and "
        "it is transmitted on the immediate DWORD preceding the TLP Header base. Local-prefixes, if any, associated "
        "with a TLP are always transmitted before the PTH is transmitted. This is pictorially shown in Figure 3-8.",
        "NOP-TLP 始终不带前置 PTH。对于非 NOP-TLP，始终发送 PTH，且位于紧邻 TLP Header base 之前的 DWORD。"
        "与 TLP 关联的 Local-prefix（若有）始终在 PTH 之前发送。如图 3-8 所示。",
        S
    ))
    story.append(pair(
        "To assist the receiver on a PBR link from disambiguating PTH from an NOP-TLP/Local-Prefix, the PCIe flit "
        "mode TLP grammar is modified as follows. Bits[7:6] of the first byte of all DWORDs, from the 1st DWORD of "
        "a TLP until a PTH is detected, are encoded as follows:",
        "为帮助 PBR 链路上的接收方区分 PTH 与 NOP-TLP/Local-Prefix，对 PCIe flit 模式 TLP 语法作如下修改："
        "从 TLP 第 1 个 DWORD 起直至检测到 PTH，所有 DWORD 首字节的 Bits[7:6] 编码为：",
        S
    ))
    for en, zh in [
        ("00b = NOP-TLP", "00b = NOP-TLP"),
        ("01b = Rsvd（保留）", "01b = Rsvd（保留）"),
        ("10b = Local Prefix", "10b = Local Prefix（本地前缀）"),
        ("11b = PTH", "11b = PTH"),
    ]:
        story.append(bullet_pair(en, zh, S))
    story.append(pair(
        "After the receiver detects a PTH, PCIe TLP grammar rules are applied per PCIe Base Specification until "
        "the TLP ends, with the restriction that NOP-TLP and Local prefix cannot be transmitted in this region of the TLP.",
        "接收方检测到 PTH 后，按 PCIe 基础规范应用 PCIe TLP 语法规则直至 TLP 结束，并限制：在此区域不得发送 NOP-TLP 与 Local prefix。",
        S
    ))

    story.append(heading(3, "3.1.8.1 Transmitter Rules Summary", "3.1.8.1 发送方规则摘要", S))
    story.append(bullet_pair(
        "For NOP-TLP and Local-Prefix Type1 field encodings, no PTH is pre-pended",
        "对于 NOP-TLP 与 Local-Prefix 的 Type1 字段编码，不前置 PTH",
        S
    ))
    story.append(bullet_pair(
        "For all other Type1 field encodings, a PTH is pre-pended immediately ahead of the Header base",
        "对于所有其他 Type1 字段编码，在 Header base 紧前方前置 PTH",
        S
    ))

    story.append(heading(3, "3.1.8.2 Receiver Rules Summary", "3.1.8.2 接收方规则摘要", S))
    for en, zh in [
        ("For NOP-TLP, if bits[5:0] are not all 0s, the receiver treats it as a malformed packet and reports "
         "the error following the associated error reporting rules",
         "对于 NOP-TLP，若 bits[5:0] 不全为 0，接收方将其视为畸形包，并按相关错误报告规则报告错误"),
        ("For a Local Prefix, if bits[5:0] are not one of 00 1101b through 00 1111b, the receiver treats it as "
         "a malformed packet and reports the error following the associated error reporting rules",
         "对于 Local Prefix，若 bits[5:0] 不是 00 1101b 至 00 1111b 之一，接收方将其视为畸形包并按相关规则报告错误"),
        ("From beginning of a TLP to when a PTH is detected, receiver silently drops a DWORD if a reserved "
         "value of 01b is received for bits[7:6] in the DWORD",
         "从 TLP 开始到检测到 PTH 期间，若某 DWORD 的 bits[7:6] 收到保留值 01b，接收方静默丢弃该 DWORD"),
        ("If an NOP-TLP or Local Prefix is received immediately after a PTH, the receiver treats it as a "
         "malformed packet and reports the error following the associated error reporting rules",
         "若在 PTH 之后立即收到 NOP-TLP 或 Local Prefix，接收方将其视为畸形包并按相关规则报告错误"),
    ]:
        story.append(bullet_pair(en, zh, S))
    story.append(note_pair(
        "Header queues in PBR switches/devices should be able to handle the additional DWORD of PTH that is "
        "needed to be carried between the source and target PBR links.",
        "PBR 交换机/设备中的头队列应能处理源与目标 PBR 链路之间需携带的额外 PTH DWORD。",
        S
    ))
    story.append(note_pair(
        "PTH is included as part of normal link level CRC/FEC calculations/checks on PBR links to ensure reliable "
        "PTH delivery over the PBR link. For details regarding the PIF, DSAR, and Hie bits, see Section 7.7.3.3, "
        "Section 7.7.7, and Section 7.7.6.2.",
        "PTH 包含在 PBR 链路正常的链路级 CRC/FEC 计算/校验中，以确保 PTH 可靠传递。关于 PIF、DSAR 与 Hie 位的细节，"
        "见第 7.7.3.3、7.7.7 与 7.7.6.2 节。",
        S
    ))
    story.append(pair(
        "On MLD links, in the egress direction, the SPID information in this header is used to generate the LD-ID "
        "information on VendPrefixL0 message as defined in Section 2.4. On MLD links, in the ingress direction, "
        "LD-ID in the VendPrefixL0 message is used to determine the DPID in the PBR packet.",
        "在 MLD 链路上，出站方向使用本头中的 SPID 信息生成 VendPrefixL0 消息上的 LD-ID 信息（见第 2.4 节）；"
        "入站方向使用 VendPrefixL0 中的 LD-ID 确定 PBR 包中的 DPID。",
        S
    ))

    story.append(Paragraph("Table 3-4. PBR TLP Header (PTH) Format ｜ 表 3-4. PBR TLP 头（PTH）格式", S["h3"]))
    story.append(pair(
        "Byte 0: Bits[7:6]=11b (PTH), Rsvd, Hie, DSAR, PIF; then SPID[11:0] and DPID[11:0].",
        "字节 0：Bits[7:6]=11b（PTH），随后为保留位、Hie、DSAR、PIF；然后是 SPID[11:0] 与 DPID[11:0]。",
        S
    ))
    story.append(Paragraph(
        "Table 3-5. NOP-TLP Header Format｜表 3-5：Byte0 Bits[7:6]=00b，其余按 PCIe 基础规范。"
        " Table 3-6. Local Prefix Header Format｜表 3-6：Byte0 Bits[7:6]=10b，后续字段按 PCIe 基础规范。",
        S["caption"]
    ))
    story.append(figure_cap(
        "Figure 3-8. Valid .io TLP Formats on PBR Links (Prefix→PTH→TLP)",
        "图 3-8. PBR 链路上有效的 .io TLP 格式（前缀→PTH→TLP）",
        S
    ))

    story.append(heading(3, "3.1.9 VendPrefixL0", "3.1.9 VendPrefixL0", S))
    story.append(pair(
        "Section 2.4.1.2 describes VendPrefixL0 usage on MLD links. For non-MLD HBR links, VendPrefixL0 carries "
        "the PBR-ID field to facilitate inter-domain communication between hosts and devices (e.g., GIM; see "
        "Section 7.7.3) and other vendor-proprietary usages (see Section 7.7.4). HBR links that use this form of "
        "the prefix must be directly attached to a PBR switch. On the switch ingress side, this prefix carries the "
        "DPID of the target edge link. On the egress side, this message carries the SPID of the source link that "
        "originated the TLP. The prefix format is shown in Table 3-7.",
        "第 2.4.1.2 节描述 MLD 链路上 VendPrefixL0 的用法。对于非 MLD 的 HBR 链路，VendPrefixL0 携带 PBR-ID 字段，"
        "以促进主机与设备间的跨域通信（例如 GIM，见第 7.7.3 节）及其他厂商专有用途（见第 7.7.4 节）。"
        "使用此形式前缀的 HBR 链路必须直接连接到 PBR 交换机。在交换机入站侧，此前缀携带目标边缘链路的 DPID；"
        "在出站侧，携带发起该 TLP 的源链路 SPID。前缀格式见表 3-7。",
        S
    ))
    story.append(pair(
        "On the switch side, handling of this prefix is disabled by default. The FM can enable this functionality "
        "on each edge USP and DSP, via CCI mailbox. The method that the FM uses to determine the set of USPs/DSPs "
        "that are capable and trustworthy of enabling this functionality is beyond the scope of this specification.",
        "在交换机侧，此前缀处理默认禁用。FM 可通过 CCI 邮箱在每个边缘 USP 与 DSP 上启用该功能。"
        "FM 如何判定哪些 USP/DSP 有能力且可信以启用此功能，超出本规范范围。",
        S
    ))
    story.append(note_pair(
        "Edge PCIe links are not precluded from using this prefix for the same purpose described above. However, "
        "such usages are beyond the scope of this specification.",
        "边缘 PCIe 链路不排除为上述相同目的使用此前缀；但此类用法超出本规范范围。",
        S
    ))
    story.append(pair(
        "See Section 7.7.3 and Section 7.7.4 for transaction flows that involve TLPs with this prefix.",
        "涉及带此前缀的 TLP 的事务流见第 7.7.3 与 7.7.4 节。",
        S
    ))

    story.append(heading(3, "3.1.10 CXL DevLoad (CDL) Field in UIO Completions",
                         "3.1.10 UIO 完成中的 CXL DevLoad（CDL）字段", S))
    story.append(pair(
        "To support QoS Telemetry (see Section 3.3.4) with UIO Direct P2P to HDM (see Section 7.7.9), UIO "
        "Completions contain the 2-bit CDL field, which carries the CXL DevLoad indication from HDM devices that "
        "support UIO Direct P2P. If an HDM device supports UIO Direct P2P to HDM, the HDM device shall populate "
        "the CDL field with values as defined in Table 3-51. The CDL field exists in UIOWrCpl, UIORdCpl, and "
        "UIORdCplD TLPs.",
        "为支持与 UIO Direct P2P to HDM（见第 7.7.9 节）配合的 QoS 遥测（见第 3.3.4 节），UIO 完成包含 2 比特 CDL 字段，"
        "携带支持 UIO Direct P2P 的 HDM 设备给出的 CXL DevLoad 指示。若 HDM 设备支持 UIO Direct P2P to HDM，"
        "则应按表 3-51 填充 CDL 字段。该字段存在于 UIOWrCpl、UIORdCpl 与 UIORdCplD TLP 中。",
        S
    ))

    story.append(heading(3, "3.1.11 CXL Fabric-related VDMs", "3.1.11 CXL 结构相关 VDM", S))
    story.append(pair(
        "In CXL Fabric (described in Section 7.7), there are many different uses for a CXL VDM. The uses fall into "
        "two categories: within a PBR Fabric, and outside a PBR Fabric.",
        "在 CXL Fabric（见第 7.7 节）中，CXL VDM 有多种用途，分为两类：PBR Fabric 之内，以及 PBR Fabric 之外。",
        S
    ))
    story.append(pair(
        "When a VDM has a CXL Vendor ID, bytes 14 and 15 in the VDM header distinguish the use case via a CXL VDM "
        "Code and whether the use is within a PBR fabric. If within a PBR fabric, there is also a PBR Opcode. "
        "Additionally for PBR Fabric CXL VDMs, many of the traditional PCIe-defined fields such as Requester ID "
        "have no meaning and thus are reserved or in some cases, repurposed. See Table 3-8 for a breakdown of the "
        "VDM header bytes for PBR Fabric VDMs.",
        "当 VDM 具有 CXL Vendor ID 时，VDM 头第 14、15 字节通过 CXL VDM Code 区分用例，并指示是否用于 PBR fabric。"
        "若在 PBR fabric 内，还有 PBR Opcode。此外，对 PBR Fabric CXL VDM，许多传统 PCIe 定义字段（如 Requester ID）"
        "无意义，因而保留或在某些情况下被重新用途。PBR Fabric VDM 头字节分解见表 3-8。",
        S
    ))
    story.append(pair(
        "Table 3-8 shows two Type encodings, a VDM without data and a VDM with data, both routed as “terminate at "
        "receiver”. If a payload is not needed, the VDM without data is used. If any payload is required, the VDM "
        "with data is used. Because the PBR VDMs use PTH to route, the ‘receiver’ is the end of the tunnel (i.e., "
        "the matching DPID). PBR VDMs with data can have at most 128B (=32 DWORDs) of payload. If the SeqLen is "
        "more than 32 DWORDs, multiple VDMs will be needed to convey the entire sequence of VDMs (for UCPull VDM).",
        "表 3-8 显示两种 Type 编码：无数据 VDM 与带数据 VDM，均按“在接收端终止”路由。若不需要载荷则用无数据 VDM；"
        "若需要任意载荷则用带数据 VDM。因 PBR VDM 使用 PTH 路由，“接收端”是隧道终点（即匹配的 DPID）。"
        "带数据的 PBR VDM 载荷最多 128B（=32 DWORD）。若 SeqLen 超过 32 DWORD，则需多个 VDM 传递整段序列（对 UCPull VDM）。",
        S
    ))
    story.append(pair(
        "Depending on the CXL VDM Code, other fields in the VDM header may have meaning. Use of these additional "
        "fields will be defined in the section covering that particular encoding. These fields include:",
        "视 CXL VDM Code 而定，VDM 头中其他字段可能有意义。这些附加字段的用法将在涵盖相应编码的章节中定义，包括：",
        S
    ))
    for en, zh in [
        ("PBR Opcode: Subclass of PBR Fabric VDMs",
         "PBR Opcode：PBR Fabric VDM 的子类"),
        ("CmdSeq: Sequence number of the Host management transaction flow",
         "CmdSeq：主机管理事务流的序号"),
        ("SeqLen: Length of the VDM sequence, applies to UCPull VDM",
         "SeqLen：VDM 序列长度，适用于 UCPull VDM"),
        ("SeqNum: Sequential VDM count with wrap if a message requires multiple sequential VDMs",
         "SeqNum：若消息需要多个连续 VDM，则为带回绕的顺序 VDM 计数"),
    ]:
        story.append(bullet_pair(en, zh, S))

    story.append(pair(
        "Table 3-9 summarizes the various CXL vendor defined messages, each with a CXL VDM code and PBR Opcode, "
        "a message destination, and a brief summary of the message’s use. The CXL VDM Code provides the category "
        "of VDM, while the PBR Opcode makes distinctions within that category. The remainder of this section deals "
        "with GFD management-related VDMs and Route Table Update related VDMs. For details of other VDMs, see "
        "Section 7.7.11.",
        "表 3-9 汇总各类 CXL 厂商定义消息，各有 CXL VDM code、PBR Opcode、消息目的地及简要用途说明。"
        "CXL VDM Code 提供 VDM 类别，PBR Opcode 在该类别内区分。本节其余部分讨论与 GFD 管理及路由表更新相关的 VDM。"
        "其他 VDM 细节见第 7.7.11 节。",
        S
    ))
    story.append(pair(
        "Although they exist outside the PBR Fabric, CXL VDM Codes 00h and 68h are listed to show the complete "
        "CXL VDM mapping. Their VDM Header is defined by PCI-SIG and thus does not match the fields provided for "
        "a PBR VDM header. These two VDMs will pass through the PBR Fabric using a hierarchical route and using "
        "the VDM Header originally defined in Section 3.1.2 for CXL PM and in Section 3.1.3 for CXL Error.",
        "尽管 CXL VDM Code 00h 与 68h 存在于 PBR Fabric 之外，仍列出以展示完整 CXL VDM 映射。"
        "其 VDM 头由 PCI-SIG 定义，故与 PBR VDM 头字段不一致。这两类 VDM 将使用层次化路由穿越 PBR Fabric，"
        "并使用第 3.1.2 节（CXL PM）与第 3.1.3 节（CXL Error）原先定义的 VDM 头。",
        S
    ))

    story.append(Paragraph(
        "Table 3-9. CXL Fabric Vendor Defined Messages ｜ 表 3-9. CXL Fabric 厂商定义消息",
        S["h3"]
    ))
    story.append(simple_table(
        ["Message 消息", "Code", "Opcode", "Dest 目的", "Comment 说明"],
        [
            ["Assert PERST#", "80h", "0h", "vUSP", "从 vDSP 向下传播基础复位"],
            ["Assert Reset", "80h", "1h", "vUSP", "从 vDSP 向下传播热复位"],
            ["Deassert Reset", "80h", "3h", "vUSP", "从 vDSP 向下传播复位解除"],
            ["Link Up", "80h", "4h", "vDSP", "向上发送至 vDSP，链路状态由 detect 变为 L0"],
            ["PBR Link Partner Info", "90h", "0h", "Link Partner", "带数据消息；数据保存在接收方"],
            ["DPCmd", "A0h", "0", "GFD", "来自 GAE 的下游代理命令"],
            ["UCPull", "A1h", "1", "Host ES", "来自 GFD 的上游命令拉取"],
            ["DCReq", "A0h", "2", "GFD", "来自 GAE 的下游命令请求（32 DWORD）"],
            ["DCReq-Last", "A0h", "3", "GFD", "最后一条 DCReq（1–32 DWORD）"],
            ["UCRsp", "A1h", "4", "Host ES", "来自 GFD 的上游完成响应（32 DWORD）"],
            ["UCRsp-Last", "A1h", "5", "Host ES", "最后一条 UCRsp（1–32 DWORD）"],
            ["UCRsp-Fail", "A1h", "6", "Host ES", "DCReq 接收失败"],
            ["GAM", "A1h", "7", "Host ES", "GFD 日志至主机（8 DWORD）"],
            ["DCReq-Fail", "A0h", "8", "GFD", "UCPull 响应失败"],
            ["RTUpdate", "A1h", "10h", "Host ES", "下游 ES 的 CacheID 总线更新"],
            ["RTUpdateAck", "A1h", "12h", "Downstream ES", "Host ES 对 RTUpdate 的确认"],
            ["RTUpdateNak", "A1h", "13h", "Downstream ES", "Host ES 对 RTUpdate 的否定应答"],
            ["CXL PM", "68h", "0", "Varies", "CXL 电源管理（4 DWORD）"],
            ["CXL Error", "00h", "0", "Host", "CXL 错误"],
        ],
        S,
        col_widths=[38 * mm, 18 * mm, 18 * mm, 32 * mm, 70 * mm],
    ))

    story.append(heading(3, "3.1.11.1 Host Management Transaction Flows of GFD",
                         "3.1.11.1 GFD 的主机管理事务流", S))
    story.append(pair(
        "Figure 3-9 summarizes the Host Management Transaction Flows of GFD. The Host ES has one GAE per host "
        "port. The GAE and GFD communicate via PID-routed VDMs.",
        "图 3-9 汇总 GFD 的主机管理事务流。Host ES 每个主机端口有一个 GAE。GAE 与 GFD 通过基于 PID 路由的 VDM 通信。",
        S
    ))
    story.append(pair(
        "Each GAE has an array of active messages, such that a host can communicate with multiple GFDs in parallel. "
        "Host software shall ensure that there is only one host-GFD management flow active per host-GFD pair.",
        "每个 GAE 有一组活动消息数组，使主机可并行与多个 GFD 通信。"
        "主机软件应确保每个 host–GFD 对仅有一条活动的管理流。",
        S
    ))
    story.append(pair(
        "The Host-to-GFD message flow consists of the following steps, after first storing the GFD command in host memory:",
        "在先将 GFD 命令存入主机内存后，主机到 GFD 的消息流包含以下步骤：",
        S
    ))
    story.append(figure_cap(
        "Figure 3-9. Host Management Transaction Flows of GFD",
        "图 3-9. GFD 的主机管理事务流",
        S
    ))

    steps = [
        ("1. Host writes to GAE.\n"
         "— Writes pointer to GFD command in host memory (for UCPull read)\n"
         "— Writes pointer to write responses from GFD in host memory (for UCRsp data)\n"
         "— Writes command length\n"
         "— Writes CmdSeq\n"
         "— Write a mailbox command doorbell register (see Section 8.2.9.4.4), which causes the GAE to start "
         "the host management flow with step 2",
         "1. 主机写入 GAE。\n"
         "— 写入主机内存中 GFD 命令的指针（供 UCPull 读取）\n"
         "— 写入主机内存中用于存放 GFD 写响应的指针（供 UCRsp 数据）\n"
         "— 写入命令长度\n"
         "— 写入 CmdSeq\n"
         "— 写入邮箱命令门铃寄存器（见第 8.2.9.4.4 节），促使 GAE 从步骤 2 开始主机管理流"),
        ("2. Host ES creates CXL PBR VDM “DPCmd” with command length that targets the GFD PID and CmdSeq to "
         "identify the current command sequence.\n"
         "— This is an unsolicited message from the GFD point of view, and the GFD must be able to sink one such "
         "message for any supported RPID and drop any message from an unsupported RPID",
         "2. Host ES 创建 CXL PBR VDM “DPCmd”，带命令长度，目标为 GFD PID，并用 CmdSeq 标识当前命令序列。\n"
         "— 从 GFD 角度看这是非请求消息；GFD 必须能对任何受支持的 RPID 接收一条此类消息，并丢弃来自不受支持 RPID 的消息"),
        ("3. GFD responds with a CXL PBR VDM “UCPull”, pulling the command for the indicated CmdSeq. The GFD "
         "response time may be delayed by responding to other doorbells from other RPIDs.",
         "3. GFD 以 CXL PBR VDM “UCPull” 响应，拉取所指 CmdSeq 的命令。GFD 响应时间可能因响应其他 RPID 的门铃而延迟。"),
        ("4. GAE converts CXL PBR VDM “UCPull” to one or more PCIe MRd TLPs.\n"
         "a. GAE sends a series of MRds to read the command, starting at the address pointer supplied to the GAE "
         "in the Proxy GFD Management Command input payload. Each MRd size is a maximum of 128B. A command larger "
         "than 128B shall require multiple MRd to gather the full command. A total of (Nx) 128B MRd (with N from "
         "0 to 7) and 1x (1B to 128B) MRd is needed to read any command of size up to 1024B.\n"
         "b. The host completes each MRd with one or two CplD TLPs.",
         "4. GAE 将 CXL PBR VDM “UCPull” 转换为一个或多个 PCIe MRd TLP。\n"
         "a. GAE 发送一系列 MRd 读取命令，起始地址为代理 GFD 管理命令输入载荷中提供给 GAE 的地址指针。"
         "每个 MRd 最大 128B。大于 128B 的命令须用多个 MRd 收集完整命令。"
         "读取最大 1024B 的命令共需 (N×) 128B MRd（N=0..7）外加 1×（1B 至 128B）MRd。\n"
         "b. 主机以一个或两个 CplD TLP 完成每个 MRd。"),
        ("5. GAE gathers the read completion data in step 4b, re-ordering and combining partial completions as "
         "needed, to create a VDM payload. The GAE sends a series of DCReq/DCReq-Last VDMs with the completion "
         "data as VDM payload in the order that matches the series of MRd in step 4. The maximum payload for PBR "
         "VDMs is 128B (= 32 DWORDs).\n"
         "— Each VDM header contains: an incrementing SeqNum (starting with 0) to detect missing messages; a "
         "CmdSeq to identify the current command for this Host–GFD thread\n"
         "— The last VDM in the sequence will be DCReq-Last; prior ones (if needed) will be DCReq\n"
         "— The first VDM shall start with a payload that matches the CCI Message header and payload as defined "
         "in Section 7.6.3; subsequent VDMs contain only the remaining payload portion\n"
         "— A failed command pull shall result in a DCReq-Fail VDM response instead of any DCReq and DCReq-Last",
         "5. GAE 收集步骤 4b 的读完成数据，按需重排并合并部分完成，以创建 VDM 载荷。GAE 按与步骤 4 中 MRd 系列匹配的顺序"
         "发送一系列 DCReq/DCReq-Last VDM，完成数据作为 VDM 载荷。PBR VDM 最大载荷为 128B（=32 DWORD）。\n"
         "— 每个 VDM 头包含：递增 SeqNum（从 0 起）以检测丢失消息；CmdSeq 以标识本 Host–GFD 线程的当前命令\n"
         "— 序列中最后一条为 DCReq-Last；之前的（如需要）为 DCReq\n"
         "— 首条 VDM 的载荷应以第 7.6.3 节定义的 CCI Message 头与载荷开始；后续 VDM 仅含剩余载荷部分\n"
         "— 命令拉取失败应返回 DCReq-Fail VDM，而非任何 DCReq/DCReq-Last"),
        ("6. GFD processes the command after it receives the last VDM (the “DCReq-Last”). The GFD shall send "
         "UCRsp/UCRsp-Last VDMs in response to the Host ES.\n"
         "— Each VDM header contains incrementing SeqNum (from 0) and CmdSeq\n"
         "— The last VDM in the sequence will be UCRsp-Last; prior ones (if needed) will be UCRsp",
         "6. GFD 在收到最后一条 VDM（“DCReq-Last”）后处理命令，并向 Host ES 发送 UCRsp/UCRsp-Last VDM。\n"
         "— 每个 VDM 头包含递增 SeqNum（从 0 起）与 CmdSeq\n"
         "— 序列中最后一条为 UCRsp-Last；之前的（如需要）为 UCRsp"),
    ]
    for en, zh in steps:
        story.append(pair(en, zh, S))

    # Closing
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph("— 译本结束 ｜ End of Bilingual Translation —", S["cover_meta"]))
    story.append(Paragraph(
        "原文为 Evaluation Copy，摘自 Compute Express Link Specification Revision 3.2, Version 1.0 "
        "(October 2, 2024)，对应原文页码约 81–100。图表位图未重绘，仅保留图题中英对照；"
        "复杂位级包格式图请对照原 PDF。",
        S["cover_meta"]
    ))
    return story


def main():
    S = styles()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for path in (OUT, OUT2):
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=18 * mm,
            bottomMargin=14 * mm,
            title="CXL Specification Rev 3.2 — 中英对照",
            author="Unofficial Bilingual Translation",
        )
        story = build_content(S)
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        print(f"Wrote {path} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
