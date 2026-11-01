# 跨海（海峡）连接 —— adjacencies.csv 生成记录

日期：2026-11-01
对象：`Daybreak of Teyvat Gamma Version/map/adjacencies.csv`
输入：`models/DOT MAP 3.0 海峡.bmp`（4096×2048，24bpp，与 `map/provinces.bmp` 同一坐标系）

## 1. 结论

- 原文件只有表头与结束行，**没有任何跨海连接**；本次依据图中的白色线段生成 **112 条 `sea` 型 adjacency**。
- 每条连接的两个端点都是**陆地省**，中间隔着海域省（`Through`），符合引擎对「两个陆地省互不直接相邻、需跨海通行」的要求。
- 文件保持原格式：UTF-8 **无 BOM**、CRLF、纯 ASCII、末行 `-1;-1;;-1;-1;-1;-1;-1;-1` 收尾。

## 2. 提取方法

1. 读 BMP 原始像素（24bpp、行自下而上、行尾 4 字节对齐），把 `R,G,B > 245` 的纯白像素当作海峡线段。
   全图共 7,475 个白像素，8 连通域分析得到 **114 条独立线段**（每条长 5～25 px，宽 3～6 px）。
2. 对每条线段做 PCA 求主轴，取两端极点 `e1 / e2`。
3. 以 `definition.csv` 的颜色→省号表把 `provinces.bmp` 转成省号图；在端点半径 7 px 内找**最近的陆地省**，作为该端所属省。
4. 用 `provinces.bmp` 的像素邻接（8 连通）自建省邻接图（23,822 对），用于：
   - 剔除「两端本来就相邻」的无效项；
   - 求两端共同的海域邻省作为 `Through`（共 103 条命中共同邻省）。
5. 端点非沿海、`Through` 非海域、重复对等做二次校验。

## 3. 结果

- 生成 **112 条**，按国家配对统计（同国为主，说明多数是本国岛链/半岛之间的联络；跨境的多为天然海峡）：

| 端点国家 | 条数 | 端点国家 | 条数 |
|---|---|---|---|
| LYY–LYY | 18 | NAT–NAT | 9 |
| FON–FON | 17 | INA–INA | 7 |
| SNE–SNE | 12 | SAN–SAN | 6 |
| NDK–NDK | 10 | ABY–ABY | 5 |

其余：PRI×4、HIL×4、GUN×2、DVA–LYY×2、ASA×2、MOT×1、SGS×1、NPS×1，以及 SNE–NDK、GUN–HIL、HIL–LYY、LYY–FON、LYY–SUM、DRA–LYY、NAT–NFF、NFF–NAT、SDH–NAT、NAT–SGD、NAT–NPS 各 1。

## 4. 跳过项（2 条）

| 线段 | 端点省 | 原因 |
|---|---|---|
| #83 | 1897 ↔ 4035 | 两省在 `provinces.bmp` 中本来就接壤，陆路已通，加 `sea` 型 adjacency 无意义且不合规 |
| #102 | 4559 ↔ 4582 | 同上（同属 INA / state 116） |

这两处白线是作者在 1～2 px 的水道上画的，但省图上两省已经贴合，引擎按普通陆路边境处理。

## 5. 校验

`tools/adj_final_check.py` 输出：

- 112 条，`Through` **同时邻接两端** 103 条，**仅邻接一端** 9 条（都是较宽水面的跨海，例如 1638↔3055、1983↔3092、907↔2043），**完全无邻接** 0 条；
- 重复省对 0；
- 端点非沿海 0；
- `tools/adj_check.py`：类型全为 `sea`、`Through` 全为海域、端点全为陆地且 `coastal = true`，问题 0。

宽水面那 9 条只是「敌方控制该海域会封断」的判定省，不影响通行本身。

## 6. 复现

```
python tools/strait_core.py        # 建立 definition/省份颜色映射（自检）
python tools/strait_final.py       # 白线段 → 端点省（输出 tools/strait_final.json）
python tools/strait_thru.py        # 求 Through 与共同邻接（输出 tools/_nb.json, tools/strait_thru.json）
python tools/gen_adjacencies.py    # 干跑，打印前若干行
python tools/gen_adjacencies.py --write   # 写盘
python tools/adj_check.py && python tools/adj_final_check.py   # 校验
```

`tools/strait_zoom2.py <线段编号...>` 可把指定线段渲染成字符图，人工核对两端省份；`tools/strait_overview.py` 生成 `docs/strait_overview.png`（灰=陆地、深蓝=海、红=海峡线）。

原始 `adjacencies.csv` 备份：`tools/.backups/adjacencies.csv.bak`。

## 7. 全量清单

| # | 端点省 A | 端点省 B | Through | A 所属 | B 所属 |
|---|---|---|---|---|---|
| 1 | 2552 | 2539 | 7240 | SNE (state 183) | SNE (state 179) |
| 2 | 438 | 1058 | 7573 | SNE (state 159) | SNE (state 218) |
| 3 | 2612 | 774 | 7109 | SNE (state 7) | SNE (state 7) |
| 4 | 2602 | 2642 | 6703 | SNE (state 218) | SNE (state 7) |
| 5 | 1669 | 1723 | 7399 | SNE (state 247) | SNE (state 247) |
| 6 | 2175 | 2884 | 5206 | SNE (state 1) | SNE (state 273) |
| 7 | 362 | 1028 | 7139 | SNE (state 317) | SNE (state 317) |
| 8 | 2977 | 2182 | 6741 | SNE (state 1) | SNE (state 149) |
| 9 | 1894 | 1295 | 6687 | SNE (state 199) | SNE (state 324) |
| 10 | 507 | 2986 | 6530 | SNE (state 5) | SNE (state 175) |
| 11 | 2990 | 2995 | 6574 | SNE (state 5) | SNE (state 149) |
| 12 | 4676 | 4677 | 7164 | SNE (state 325) | SNE (state 325) |
| 13 | 4676 | 1465 | 6563 | SNE (state 325) | NDK (state 327) |
| 14 | 3028 | 1648 | 6370 | NDK (state 20) | NDK (state 336) |
| 15 | 3036 | 3049 | 6662 | NDK (state 13) | NDK (state 328) |
| 16 | 1638 | 3055 | 6756 | NDK (state 18) | NDK (state 329) |
| 17 | 1580 | 2372 | 6388 | FON (state 58) | FON (state 370) |
| 18 | 3049 | 1867 | 4917 | NDK (state 328) | NDK (state 339) |
| 19 | 2372 | 3074 | 5317 | FON (state 370) | FON (state 348) |
| 20 | 1983 | 3092 | 7036 | PRI (state 338) | PRI (state 24) |
| 21 | 3059 | 3085 | 4992 | PRI (state 337) | PRI (state 23) |
| 22 | 2400 | 3102 | 6747 | NDK (state 30) | NDK (state 56) |
| 23 | 1659 | 3149 | 6279 | PRI (state 362) | PRI (state 27) |
| 24 | 1603 | 3172 | 6092 | PRI (state 363) | PRI (state 371) |
| 25 | 2261 | 838 | 6859 | FON (state 364) | FON (state 375) |
| 26 | 518 | 3177 | 7695 | FON (state 366) | FON (state 380) |
| 27 | 1779 | 3208 | 6394 | FON (state 57) | FON (state 40) |
| 28 | 782 | 1749 | 6645 | GUN (state 381) | GUN (state 382) |
| 29 | 907 | 2043 | 5689 | NDK (state 36) | NDK (state 33) |
| 30 | 907 | 1986 | 5931 | NDK (state 36) | NDK (state 405) |
| 31 | 3261 | 3307 | 6757 | FON (state 396) | FON (state 39) |
| 32 | 1505 | 3306 | 6512 | FON (state 40) | FON (state 38) |
| 33 | 2447 | 3288 | 7484 | NDK (state 34) | NDK (state 37) |
| 34 | 3266 | 4678 | 7730 | FON (state 31) | FON (state 372) |
| 35 | 3302 | 2095 | 7733 | GUN (state 400) | HIL (state 410) |
| 36 | 455 | 3324 | 6610 | FON (state 29) | FON (state 47) |
| 37 | 4678 | 1647 | 4916 | FON (state 372) | FON (state 426) |
| 38 | 2008 | 3352 | 7750 | NDK (state 415) | NDK (state 443) |
| 39 | 918 | 3354 | 6546 | GUN (state 416) | GUN (state 437) |
| 40 | 3344 | 2075 | 6090 | FON (state 38) | FON (state 45) |
| 41 | 3397 | 3400 | 7763 | HIL (state 436) | LYY (state 447) |
| 42 | 3413 | 3417 | 7137 | LYY (state 457) | FON (state 45) |
| 43 | 4679 | 3435 | 6886 | MOT (state 48) | MOT (state 466) |
| 44 | 510 | 3445 | 7768 | FON (state 22) | FON (state 43) |
| 45 | 3455 | 2257 | 6854 | FON (state 358) | FON (state 449) |
| 46 | 2334 | 2097 | 7423 | DVA (state 450) | LYY (state 468) |
| 47 | 3474 | 3488 | 7775 | FON (state 53) | FON (state 355) |
| 48 | 3499 | 3494 | 7135 | FON (state 59) | FON (state 42) |
| 49 | 2376 | 4680 | 6648 | FON (state 53) | FON (state 496) |
| 50 | 1461 | 3503 | 7423 | DVA (state 450) | LYY (state 473) |
| 51 | 3523 | 982 | 7423 | LYY (state 473) | LYY (state 468) |
| 52 | 3499 | 3520 | 7135 | FON (state 59) | FON (state 59) |
| 53 | 3522 | 653 | 7423 | LYY (state 485) | LYY (state 502) |
| 54 | 4681 | 2282 | 7788 | ABY (state 62) | ABY (state 64) |
| 55 | 1531 | 3544 | 7788 | ABY (state 64) | ABY (state 62) |
| 56 | 2234 | 3572 | 7787 | NDK (state 486) | NDK (state 414) |
| 57 | 3559 | 3600 | 7792 | LYY (state 502) | LYY (state 514) |
| 58 | 1428 | 3587 | 7792 | LYY (state 481) | LYY (state 514) |
| 59 | 4682 | 2282 | 6433 | ABY (state 62) | ABY (state 64) |
| 60 | 860 | 4683 | 6168 | ABY (state 64) | ABY (state 62) |
| 61 | 860 | 4684 | 6433 | ABY (state 64) | ABY (state 62) |
| 62 | 3592 | 461 | 6776 | LYY (state 514) | LYY (state 527) |
| 63 | 413 | 487 | 6584 | LYY (state 499) | LYY (state 68) |
| 64 | 255 | 3650 | 7798 | LYY (state 499) | LYY (state 544) |
| 65 | 1230 | 3663 | 5175 | LYY (state 529) | LYY (state 544) |
| 66 | 1663 | 4685 | 6802 | SGS (state 543) | SGS (state 503) |
| 67 | 3650 | 1130 | 7295 | LYY (state 544) | LYY (state 541) |
| 68 | 3674 | 3654 | 6006 | HIL (state 70) | HIL (state 526) |
| 69 | 3663 | 640 | 6023 | LYY (state 544) | LYY (state 536) |
| 70 | 1640 | 3703 | 6954 | HIL (state 81) | HIL (state 550) |
| 71 | 1640 | 3691 | 7388 | HIL (state 81) | HIL (state 558) |
| 72 | 3708 | 1507 | 7816 | LYY (state 73) | LYY (state 544) |
| 73 | 3693 | 3714 | 7818 | HIL (state 70) | HIL (state 550) |
| 74 | 2364 | 2099 | 6846 | LYY (state 74) | SUM (state 560) |
| 75 | 3748 | 3749 | 6787 | LYY (state 553) | LYY (state 78) |
| 76 | 1223 | 688 | 6774 | DRA (state 547) | LYY (state 77) |
| 77 | 3824 | 3838 | 7834 | LYY (state 77) | LYY (state 597) |
| 78 | 3858 | 3905 | 5736 | NAT (state 79) | NAT (state 605) |
| 79 | 1802 | 977 | 6843 | NAT (state 88) | NAT (state 85) |
| 80 | 3910 | 3901 | 7841 | LYY (state 83) | LYY (state 84) |
| 81 | 3954 | 855 | 6531 | LYY (state 623) | LYY (state 634) |
| 82 | 3939 | 3947 | 7360 | NAT (state 87) | NAT (state 622) |
| 83 | 222 | 4689 | 7854 | LYY (state 86) | LYY (state 86) |
| 84 | 2405 | 2455 | 5862 | NAT (state 605) | NAT (state 91) |
| 85 | 984 | 3 | 7360 | NAT (state 93) | NAT (state 622) |
| 86 | 4689 | 4690 | 7854 | LYY (state 86) | LYY (state 86) |
| 87 | 4035 | 1828 | 7119 | LYY (state 658) | LYY (state 571) |
| 88 | 4072 | 4053 | 6159 | NAT (state 488) | NAT (state 662) |
| 89 | 512 | 4085 | 7214 | NAT (state 662) | NFF (state 460) |
| 90 | 821 | 4095 | 6989 | NFF (state 568) | NAT (state 666) |
| 91 | 476 | 2435 | 7455 | SDH (state 532) | NAT (state 307) |
| 92 | 2435 | 1804 | 6932 | NAT (state 307) | SGD (state 289) |
| 93 | 2289 | 1140 | 6806 | NAT (state 96) | NAT (state 298) |
| 94 | 1439 | 4691 | 5482 | NAT (state 298) | NAT (state 98) |
| 95 | 1701 | 607 | 7892 | INA (state 111) | INA (state 203) |
| 96 | 820 | 236 | 5911 | NAT (state 100) | NAT (state 216) |
| 97 | 4692 | 4403 | 6888 | INA (state 115) | INA (state 109) |
| 98 | 4379 | 4435 | 5261 | INA (state 103) | INA (state 99) |
| 99 | 2381 | 4446 | 7918 | NPS (state 105) | NPS (state 112) |
| 100 | 1998 | 429 | 5549 | NAT (state 164) | NPS (state 158) |
| 101 | 1488 | 4693 | 7937 | INA (state 110) | INA (state 113) |
| 102 | 4559 | 4571 | 6081 | INA (state 116) | INA (state 116) |
| 103 | 4580 | 2220 | 6927 | SAN (state 121) | SAN (state 118) |
| 104 | 4580 | 4694 | 6183 | SAN (state 121) | SAN (state 121) |
| 105 | 2220 | 4695 | 7949 | SAN (state 118) | SAN (state 121) |
| 106 | 4696 | 4600 | 6386 | INA (state 126) | INA (state 135) |
| 107 | 4695 | 4694 | 7949 | SAN (state 121) | SAN (state 121) |
| 108 | 920 | 4622 | 6728 | SAN (state 124) | SAN (state 128) |
| 109 | 2406 | 2081 | 5456 | SAN (state 117) | SAN (state 254) |
| 110 | 4647 | 4643 | 7980 | ASA (state 574) | ASA (state 130) |
| 111 | 4697 | 4646 | 7976 | ASA (state 565) | ASA (state 574) |
| 112 | 492 | 4698 | 7982 | INA (state 102) | INA (state 102) |

---

## 8. 追加：两条红线跨海（2026-11-01 晚）

作者在 `models/DOT MAP 3.0 海峡.bmp` 上又手绘了 **2 条红色线段**，按同一套流程解析并追加。

### 8.1 红线识别

- 红色像素判定：`R > 150 且 R-G > 70 且 R-B > 70`。全图 295 个红点，8 连通域得到 **2 条独立线段**（无碎片）。
- 两条线段粗 3～6 px，长度 23 / 33 px，都落在省对之间较窄的水道上，与白线同类。

### 8.2 解析结果

| # | 线段中心 | 端点外推处 | 起点省 | 终点省 | 中段海域 | 说明 |
|---|---|---|---|---|---|---|
| 113 | (2046, 1051) | (2039,1033) / (2052,1070) | **1940**（FON, state 16） | **2387**（FON, state 441） | 6907 | 枫丹近岸南北向海峡 |
| 114 | (2087, 1055) | (2102,1053) / (2073,1058) | **3324**（FON, state 47） | **3327**（FON, state 441） | 6321 | 枫丹东南东西向海峡 |

- 端点省用「端点沿主轴外推 3 px，再取 7×7 窗口内陆地省的多数票」，避免 `provinces.bmp` 海岸线的 1 px 抗锯齿杂点（该处确有 6763/6907 等海域单像素噪点）导致误判。
- 中段海域用线段 35%/50%/65% 三点处、7×7 窗口内海域省的多数票，两条均为单值（6907 / 6321，无歧义）。

### 8.3 校验

- 两对端点省**在 `provinces.bmp` 中互不直接相邻**（1940-2387、3324-3327 均为 False），符合 `sea` 型 adjacency 的前提。
- 端点省均为陆地且 `coastal = true`；Through 均为 `sea` 型。
- 两条与已有 112 条无重复省对。
- `tools/adj_check.py` → 114 条、问题 0；`tools/adj_final_check.py` → 重复 0、端点非沿海 0、Through 完全不邻接 0（同时邻接两端 103 条，仅邻接一端 11 条，新增的这 2 条属于后者：都是较宽水面，Through 取「线段实际穿过的海域」，只作敌方舰队封断判定）。

### 8.4 写入结果

文件由 114 行变为 **116 行**（表头 + 114 条 + 结束行），仍为 UTF-8 无 BOM、CRLF、纯 ASCII：

```
1940;2387;sea;6907;-1;-1;-1;-1;;DOT strait 113
3324;3327;sea;6321;-1;-1;-1;-1;;DOT strait 114
-1;-1;;-1;-1;-1;-1;-1;-1
```

核对图：`docs/red_strait_crop.png`（灰=陆地、深蓝=海、红=作者手绘线、字=省号）。

备份：`tools/.backups/adjacencies.before_red.csv`（追加前 112 条）。脚本：`tools/red_resolve2.py`（红线解析）、`tools/add_red_adj.py`（追加，默认干跑）、`tools/red_render.py`（出核对图）。
