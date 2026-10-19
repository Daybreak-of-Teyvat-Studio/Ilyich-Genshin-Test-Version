---
name: mod-dual-copy-rule
description: 以后所有 mod 改动必须仓库与本地部署副本同时改（游戏加载的是本地目录）；改完做双副本核对
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_3c421fb8-e84d-47d4-a44c-53452b380660
---

用户指示（2026-10-17）：本地 mod 路径 = `C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version`；**以后所有改动两份同时改**（仓库 `...\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version` + 本地部署副本），改完核对两副本一致。

**Why:** 游戏实际加载的是本地部署目录；只改仓库不会生效，只改本地会在下次同步时丢失。

**How to apply:** 每个写文件的脚本都遍历两个根路径（或改完立即复制）；交付前跑全树对照（文件数/大小/同大小哈希）。2026-10-17 实检：17,203 个文件两副本完全一致（0 差异）。
