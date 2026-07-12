# CXL Specification — Chapter 1 中英对照

本仓库提供 **CXL Specification Revision 3.2, Version 1.0** 第 1 章（Introduction / 导论）的非官方中英对照译本。

## 交付物

- [`output/CXL_Spec_Rev3.2_Ch1_Introduction_中英对照.pdf`](output/CXL_Spec_Rev3.2_Ch1_Introduction_中英对照.pdf)：中英对照 PDF（约 32 页）
  - 正文段落：英文（EN）+ 中文对照
  - 表 1-1 术语表：术语 | 英文定义 | 中文定义（366 条）
  - 表 1-2 参考文档：中英对照
  - 插图保留英文原图并附中英图注

## 重新生成

```bash
pip install reportlab pymupdf fonttools
# 系统需安装 fonts-wqy-microhei（或等价含拉丁+CJK 的 TTF）
sudo apt-get install -y fonts-wqy-microhei poppler-utils
python3 scripts/generate_bilingual_pdf.py
```

## 说明

- 源文档为 Evaluation Copy，译本仅供学习参考；如与正式规范冲突，以原文为准。
- 专有缩写（CXL、HDM、ARB/MUX 等）在译文中保留英文形式。
