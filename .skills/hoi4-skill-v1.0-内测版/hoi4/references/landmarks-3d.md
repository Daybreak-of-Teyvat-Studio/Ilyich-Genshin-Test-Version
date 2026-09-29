# 3D 地标模型流水线（building entity）

建筑类型 `landmark_<name>` → 引擎找实体 `building_landmark_<name>` → pdxmesh → `.mesh` 文件。

| 层 | 文件 | 格式 |
|----|------|------|
| 建筑定义 | `common/buildings/*.txt` | `landmark_X = { spawn_point = landmark_spawn ... }` |
| 实体定义 | `gfx/entities/*.asset` | `entity = { name = "building_landmark_X" pdxmesh = "landmark_X_mesh" }` |
| mesh 注册 | `gfx/entities/*.gfx` | `pdxmesh = { name = "landmark_X_mesh" file = "..." meshsettings = {...} }` |
| mesh 文件 | `gfx/models/buildings/landmarks/landmark_X.mesh` | 二进制 Paradox mesh |
| 纹理 | 同目录 | `*_diffuse.dds`、`*_normal.dds`、`*_specular.dds` |
| 图标注册 | `interface/buildings/*.gfx` | `spriteType = { name = "GFX_X_icon" }` |
| 图标文件 | `gfx/interface/buildings/historical_buildings/large/X_icon.dds` | 48×28 DDS |

## Blender + io_pdx_mesh 工具链

- Blender 5.2：`D:\Program Files\Blender Foundation\Blender 5.2\blender.exe`（不在 PATH）。
- 命令行后台运行（输出直达终端，便于验证）：
  ```
  & "D:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "tools\xxx.py"
  ```

**插件（extension 形式，Blender 4.2+）**：装在 `C:\Users\LR\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\io_pdx_mesh`，Python 命名空间 `bl_ext.user_default.io_pdx_mesh`。

正确导入导出（直接函数，不是 `import_mesh.pdx_mesh`）：

```python
from bl_ext.user_default.io_pdx_mesh.pdx_blender import blender_import_export as pdxi
pdxi.import_meshfile(meshpath)   # 导入 .mesh
pdxi.export_meshfile(meshpath)   # 导出 .mesh
```

operator 名是 `io_pdx_mesh.import_mesh` / `io_pdx_mesh.export_mesh`（`bpy.ops.io_pdx_mesh` 命名空间）。

**常见坑**：
- Blender 4.1+ 移除 `mesh.use_auto_smooth`。重算法线用 bmesh：`bmesh.ops.recalc_face_normals(bm, faces=bm.faces)`，顶点移动后必须重算（旧自定义法线会错）。
- GUI 脚本编辑器运行脚本时 `print`/报错显示在 System Console（Window > Toggle System Console），用户看不到，表现为"点了没动静"。对策：输出写日志文件（print 重定向 Tee）+ 用直接 API（`bpy.data.objects.remove`）替代 context 敏感的 operator（`bpy.ops.object.delete`）。
- 坐标：PDX 引擎 Y-up，Blender Z-up，插件 `swap_coord_space` 导入时自动转换。改造脚本直接改顶点即可，无需手动换轴。
