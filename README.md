# CXL Specification Rev 3.2 — 按章中英对照

将仓库中的 `CXL-Specification_rev3p2_ver1p0_2024October2_evalcopy.pdf`（1233 页）按章节拆分，并为**每一章**生成中英对照 PDF。

## 交付格式

每个章节的中英对照 PDF 采用：

1. 封面（章节标题中英对照）
2. **英文原页**（完整保留图、表、版式）
3. **中文译文页**（该页正文的中文翻译）

依次循环，直至该章结束。

## 章节列表

| ID | 章节 | 源页码 |
|----|------|--------|
| 00_cover | 封面与声明 | 1–2 |
| 00_contents | 目录 / 图目录 / 表目录 | 3–43 |
| 00_revision_history | 修订历史 | 44–49 |
| 01_Introduction | 1.0 导论 | 50–70 |
| 02_CXL_System_Architecture | 2.0 CXL 系统架构 | 71–84 |
| 03_CXL_Transaction_Layer | 3.0 CXL 事务层 | 85–190 |
| 04_CXL_Link_Layers | 4.0 CXL 链路层 | 191–261 |
| 05_CXL_ARB_MUX | 5.0 CXL ARB/MUX | 262–286 |
| 06_Flex_Bus_Physical_Layer | 6.0 Flex Bus 物理层 | 287–318 |
| 07_Switching | 7.0 交换 | 319–498 |
| 08_Control_and_Status_Registers | 8.0 控制与状态寄存器 | 499–798 |
| 09_Reset_Initialization_Configuration_and_Manageability | 9.0 复位/初始化/配置/可管理性 | 799–878 |
| 10_Power_Management | 10.0 电源管理 | 879–891 |
| 11_CXL_Security | 11.0 CXL 安全 | 892–997 |
| 12_Reliability_Availability_and_Serviceability | 12.0 RAS | 998–1010 |
| 13_Performance_Considerations | 13.0 性能考虑 | 1011–1019 |
| 14_CXL_Compliance_Testing | 14.0 合规测试 | 1020–1211 |
| AppA_Taxonomy | 附录 A 分类法 | 1212–1215 |
| AppB_UIO_P2P_HDM_DB | 附录 B UIO P2P | 1216 |
| AppC_Memory_Protocol_Tables | 附录 C 内存协议表 | 1217–1233 |

生成结果位于 `output/chapters_bilingual/`（亦同步到 Cloud Agent artifacts）。

## 重新生成

```bash
pip install -r requirements.txt
sudo apt-get install -y fonts-wqy-microhei poppler-utils
# 全部章节
python3 scripts/build_all_bilingual_chapters.py
# 或指定章节 ID
python3 scripts/build_all_bilingual_chapters.py 01_Introduction 02_CXL_System_Architecture
```

## 说明

- 非官方、机器辅助翻译，仅供学习参考；与正式规范冲突时以原文为准。
- 图、表以英文原页为准；译文页主要覆盖可提取正文。
