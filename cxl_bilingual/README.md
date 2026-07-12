# CXL Specification Rev 3.2 — 中英对照译本

非官方中英对照 PDF，基于 Evaluation Copy 摘录（原文约第 81–100 页）。

## 输出文件

- `CXL_Specification_Rev3.2_Bilingual_ZH_EN.pdf` — 左右对照（左 EN / 右 中文）
- 同步副本：`/opt/cursor/artifacts/CXL_Specification_Rev3.2_Bilingual_ZH_EN.pdf`

## 重新生成

```bash
python3 generate_bilingual_pdf.py
```

依赖：`reportlab`、系统中文字体（文泉驿微米黑或 DroidSansFallback）。

## 覆盖范围

- §2.5 Multi-Headed Device — §2.9 Manageability Overview
- §3.0–§3.1.11.1 CXL Transaction Layer（含 PM VDM、PTH、Fabric VDM、GFD 主机管理流）
