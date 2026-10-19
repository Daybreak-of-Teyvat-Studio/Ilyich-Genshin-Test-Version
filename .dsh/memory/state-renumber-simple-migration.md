---
name: state-renumber-simple-migration
description: 删州/合并后补号只准「简单迁移」（尾部补号）——严禁全量迁移级联重排；用户铁律，已写入 skill v2.00
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_3c421fb8-e84d-47d4-a44c-53452b380660
---

删州/合并州空出号位后，补号**只用「简单迁移」**：把号尾最后 k 个州搬进空出的号位，仅对这 k 个州做引用迁移（①loc 键 ②airports/rocketsites 键 ③state 文件 id/name 键 ④capital/脚本引用 ⑤buildings 行）。**严禁「全量迁移」**（级联重排几百个州号）。

**Why:** 用户两次明令，原话「不要全量迁移，你把最后的 706-709 改成 63,65,66,67 不就行了？」「和你说了多少次了」。2026-10-13 我交的全量迁移方案导致 debug 都进不去，用户找人修回；全量迁移牵动几百州的 loc/引用/首都，出错面大、无法逐条核对。

**How to apply:** 删除/合并州文件后立刻补号（合并与补号是连续两步）。实证案例：62+63+65+66+67→62 后尾部 703/704/705/706→63/65/66/67（10-14 本会话）；删 41 海州后 718→709（帮手）；707/708/709→89/90/94（帮手）。州文件 `# name="STATE_旧号"` 注释 = 迁移凭据。方法细节见 skill `hoi4-modder-cn` v2.00 的 gamma-pipeline.md「州号空洞与补号」。关联 [[gamma-mod-progress]]、[[hoi4-skill-structure]]。
