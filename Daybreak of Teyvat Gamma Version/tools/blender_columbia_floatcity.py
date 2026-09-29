"""
提瓦特黎明 — 天空城（哥伦比亚）浮空城改造脚本

把 Big Ben 钟楼改造成浮空城结构：
  1. 整座塔沿 Z 轴抬升 LIFT 高度（悬空）
  2. 底部基座（Z < BASE_HEIGHT）向中心轴收拢成倒锥岩石（浮岛底）

运行：脚本编辑器打开本文件 → 点 Run Script（或 Alt+P）。
所有输出会同时写入 tools\\blender_log.txt，报错时打开该文件即可看到原因。
"""
import bpy
import bmesh
import os
import sys
import traceback

# ================= 参数 =================
BASE_HEIGHT = 4.0   # 基座高度（Z < 此值视为底部基座，收锥）
LIFT = 3.0          # 整体抬升量（让锥尖离地，悬空高度）
SHRINK = 0.95       # 底部收拢程度 0~1（1 = 完全收到中心点，形成尖锥）
# =======================================

MESH_PATH = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version\gfx\models\buildings\landmarks\landmark_columbia.mesh"
LOG_PATH = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version\tools\blender_log.txt"
EXPORT_PATH = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version\gfx\models\buildings\landmarks\landmark_columbia_float.mesh"

DO_EXPORT = "--export" in sys.argv
if "--" in sys.argv:
    i = sys.argv.index("--") + 1
    if i < len(sys.argv):
        MESH_PATH = sys.argv[i]


# print 同时输出到控制台和日志文件
class Tee:
    def __init__(self, path):
        self.file = open(path, "w", encoding="utf-8")
    def write(self, s):
        self.file.write(s)
        sys.__stdout__.write(s)
    def flush(self):
        self.file.flush()
        sys.__stdout__.flush()

sys.stdout = Tee(LOG_PATH)
sys.stderr = sys.stdout


def main():
    print("=" * 70)
    print(f"参数: BASE_HEIGHT={BASE_HEIGHT} LIFT={LIFT} SHRINK={SHRINK}")
    print("mesh 文件:", MESH_PATH)

    # 清理场景（直接 API，不依赖 context）
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    from bl_ext.user_default.io_pdx_mesh.pdx_blender import blender_import_export as pdxi
    pdxi.import_meshfile(MESH_PATH)

    import mathutils

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    main_obj = max(meshes, key=lambda o: len(o.data.vertices))
    collision_objs = [o for o in meshes if o is not main_obj]

    print(f"主塔对象: {main_obj.name} ({len(main_obj.data.vertices)} 顶点)")

    def bbox_z(obj):
        mw = obj.matrix_world
        zs = [(mw @ v.co).z for v in obj.data.vertices]
        return min(zs), max(zs)

    zmin0, zmax0 = bbox_z(main_obj)
    print(f"改造前主塔 Z 范围: [{zmin0:.3f}, {zmax0:.3f}]")

    # 改造：抬升 + 收锥
    mesh = main_obj.data
    for v in mesh.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        z_new = z + LIFT
        if z < BASE_HEIGHT:
            t = 1.0 - (z / BASE_HEIGHT)
            factor = 1.0 - t * SHRINK
            x_new = x * factor
            y_new = y * factor
        else:
            x_new, y_new = x, y
        v.co = (x_new, y_new, z_new)
    mesh.update()

    # 重算法线
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # 碰撞体抬升
    for c in collision_objs:
        for v in c.data.vertices:
            v.co = (v.co.x, v.co.y, v.co.z + LIFT)
        c.data.update()

    zmin1, zmax1 = bbox_z(main_obj)
    print(f"改造后主塔 Z 范围: [{zmin1:.3f}, {zmax1:.3f}]  (悬空 {zmin1:.3f} 单位)")

    # 选中主塔并设为 active，方便聚焦查看
    bpy.context.view_layer.objects.active = main_obj
    main_obj.select_set(True)

    if DO_EXPORT:
        print("导出 ->", EXPORT_PATH)
        pdxi.export_meshfile(EXPORT_PATH)
        print("导出完成")
    else:
        print("改造完成。回 Layout 工作区，按数字键盘 . 聚焦查看。")
    print("=" * 70)


try:
    main()
except Exception:
    print("!! 脚本报错：")
    traceback.print_exc()
    print("请把 tools\\blender_log.txt 的内容发给我。")
