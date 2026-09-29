"""
提瓦特黎明 — 天空城（哥伦比亚）landmark mesh 分析脚本 v2

直接调用 io_pdx_mesh 的 import_meshfile() 函数导入 mesh，
输出对象结构 / 包围盒 / 材质 / 骨骼，供后续编写改造逻辑使用。

运行方式（推荐命令行，输出直接可见）：
  "D:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "tools\blender_columbia_analyze.py"

也可在 Blender 脚本编辑器里运行（先 Window > Toggle System Console 看输出）。
"""
import bpy
import os
import sys
import traceback

MESH_PATH = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version\gfx\models\buildings\landmarks\landmark_columbia.mesh"

if "--" in sys.argv:
    i = sys.argv.index("--") + 1
    if i < len(sys.argv):
        MESH_PATH = sys.argv[i]

print("=" * 70)
if not os.path.exists(MESH_PATH):
    print("!! 找不到 mesh 文件:", MESH_PATH)
    raise SystemExit(1)
print("mesh 文件:", MESH_PATH)
print("大小:", os.path.getsize(MESH_PATH), "字节")

# 清理场景
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# 加载插件模块（extension 命名空间）
try:
    from bl_ext.user_default.io_pdx_mesh.pdx_blender import blender_import_export as pdxi
    print("已加载 io_pdx_mesh 导入导出模块")
except Exception:
    print("!! 加载 io_pdx_mesh 模块失败：")
    traceback.print_exc()
    raise SystemExit(1)

# 导入 mesh
try:
    pdxi.import_meshfile(MESH_PATH)
    print("导入完成")
except Exception:
    print("!! 导入失败：")
    traceback.print_exc()
    raise SystemExit(1)

import mathutils

print("\n===== 场景对象 =====")
for obj in bpy.data.objects:
    extra = ""
    if obj.type == "MESH":
        extra = f"  顶点={len(obj.data.vertices)} 面={len(obj.data.polygons)}"
    elif obj.type == "ARMATURE":
        extra = f"  骨骼={len(obj.data.bones)}"
    print(f"[{obj.type}] {obj.name}{extra}")

def mesh_info(obj):
    d = obj.data
    xs, ys, zs = [], [], []
    for c in obj.bound_box:
        w = obj.matrix_world @ mathutils.Vector(c)
        xs.append(w.x)
        ys.append(w.y)
        zs.append(w.z)
    print(f"\n--- MESH: {obj.name} ---")
    print(f"  顶点: {len(d.vertices)}  面: {len(d.polygons)}")
    print(f"  世界包围盒 X: [{min(xs):.3f}, {max(xs):.3f}]")
    print(f"  世界包围盒 Y: [{min(ys):.3f}, {max(ys):.3f}]")
    print(f"  世界包围盒 Z: [{min(zs):.3f}, {max(zs):.3f}]")
    sx = max(xs) - min(xs)
    sy = max(ys) - min(ys)
    sz = max(zs) - min(zs)
    print(f"  尺寸: {sx:.3f} x {sy:.3f} x {sz:.3f}")
    print(f"  中心: ({(min(xs)+max(xs))/2:.3f}, {(min(ys)+max(ys))/2:.3f}, {(min(zs)+max(zs))/2:.3f})")
    if d.materials:
        print("  材质槽:")
        for i, m in enumerate(d.materials):
            shader = ""
            if m:
                shader = m.get("shader", "") if isinstance(m, bpy.types.Material) else ""
            print(f"    [{i}] {m.name if m else 'None'}  shader={shader}")
    if obj.vertex_groups:
        print(f"  顶点组: {[g.name for g in obj.vertex_groups]}")
    # 修改器（骨骼蒙皮）
    if obj.modifiers:
        for mod in obj.modifiers:
            print(f"  修改器: {mod.type} '{mod.name}' object={getattr(mod, 'object', None)}")
    lx = [v.co.x for v in d.vertices]
    ly = [v.co.y for v in d.vertices]
    lz = [v.co.z for v in d.vertices]
    print(f"  局部顶点范围 X: [{min(lx):.3f}, {max(lx):.3f}]")
    print(f"  局部顶点范围 Y: [{min(ly):.3f}, {max(ly):.3f}]")
    print(f"  局部顶点范围 Z: [{min(lz):.3f}, {max(lz):.3f}]")

def armature_info(obj):
    print(f"\n--- ARMATURE: {obj.name} ---")
    for b in obj.data.bones:
        head = obj.matrix_world @ b.head_local
        tail = obj.matrix_world @ b.tail_local
        parent = b.parent.name if b.parent else None
        print(f"  bone '{b.name}': head=({head.x:.3f},{head.y:.3f},{head.z:.3f}) tail=({tail.x:.3f},{tail.y:.3f},{tail.z:.3f}) parent={parent}")

def empty_info(obj):
    loc = obj.matrix_world.to_translation()
    print(f"  locator '{obj.name}': pos=({loc.x:.3f},{loc.y:.3f},{loc.z:.3f}) parent={obj.parent.name if obj.parent else None}")

for obj in bpy.data.objects:
    if obj.type == "MESH":
        mesh_info(obj)
    elif obj.type == "ARMATURE":
        armature_info(obj)
    elif obj.type == "EMPTY":
        empty_info(obj)

print("\n===== 分析完成 =====")
