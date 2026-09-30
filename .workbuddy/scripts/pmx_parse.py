# -*- coding: utf-8 -*-
"""PMX 2.0 解析器：抽取顶点/面/材质/骨骼，供 HOI4 mesh 转换使用。"""
import os
import struct
import sys

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
OUT = os.path.join(ROOT, ".workbuddy", "report_pmx_dump.txt")


class Reader:
    def __init__(self, data):
        self.d = data
        self.p = 0

    def u8(self):
        v = struct.unpack_from("<B", self.d, self.p)[0]
        self.p += 1
        return v

    def i32(self):
        v = struct.unpack_from("<i", self.d, self.p)[0]
        self.p += 4
        return v

    def u32(self):
        v = struct.unpack_from("<I", self.d, self.p)[0]
        self.p += 4
        return v

    def f32(self):
        v = struct.unpack_from("<f", self.d, self.p)[0]
        self.p += 4
        return v

    def u16(self):
        v = struct.unpack_from("<H", self.d, self.p)[0]
        self.p += 2
        return v

    def vec(self, n):
        v = struct.unpack_from("<" + "f" * n, self.d, self.p)
        self.p += 4 * n
        return list(v)

    def raw(self, n):
        v = self.d[self.p:self.p + n]
        self.p += n
        return v


class PMX:
    def __init__(self, path):
        self.path = path
        data = open(path, "rb").read()
        self.r = Reader(data)
        r = self.r
        magic = r.raw(4)
        if magic != b"PMX ":
            raise ValueError(f"bad magic {magic!r}")
        self.version = r.f32()
        gcount = r.u8()
        self.g = list(r.raw(gcount))
        self.encoding = self.g[0]
        self.add_uv = self.g[1]
        self.vidx = self.g[2]
        self.tidx = self.g[3]
        self.midx = self.g[4]
        self.bidx = self.g[5]
        self.moidx = self.g[6]
        self.ridx = self.g[7]
        self.name = self.text()
        self.name_en = self.text()
        self.comment = self.text()
        self.comment_en = self.text()
        self._read_vertices()
        self._read_faces()
        self._read_textures()
        self._read_materials()
        self._read_bones()

    def text(self):
        n = self.r.i32()
        raw = self.r.raw(n)
        enc = "utf-16-le" if self.encoding == 0 else "utf-8"
        return raw.decode(enc, "replace")

    def idx(self, size):
        """有符号索引：-1 表示无。"""
        if size == 1:
            v = struct.unpack_from("<b", self.r.d, self.r.p)[0]
            self.r.p += 1
            return v
        if size == 2:
            v = struct.unpack_from("<h", self.r.d, self.r.p)[0]
            self.r.p += 2
            return v
        v = struct.unpack_from("<i", self.r.d, self.r.p)[0]
        self.r.p += 4
        return v

    def uidx(self, size):
        """无符号索引（顶点/材质/形变用）。"""
        if size == 1:
            v = struct.unpack_from("<B", self.r.d, self.r.p)[0]
            self.r.p += 1
            return v
        if size == 2:
            v = struct.unpack_from("<H", self.r.d, self.r.p)[0]
            self.r.p += 2
            return v
        v = struct.unpack_from("<I", self.r.d, self.r.p)[0]
        self.r.p += 4
        return v

    def _read_vertices(self):
        r = self.r
        n = r.i32()
        self.vcount = n
        pos, nrm, uv, wt, wb, ww, es = [], [], [], [], [], [], []
        for _ in range(n):
            pos.append(r.vec(3))
            nrm.append(r.vec(3))
            uv.append(r.vec(2))
            if self.add_uv:
                r.raw(4 * 4 * self.add_uv)
            t = r.u8()
            wt.append(t)
            if t == 0:      # BDEF1
                wb.append((self.idx(self.bidx), 0, 0, 0))
                ww.append((1.0, 0.0, 0.0, 0.0))
            elif t == 1:    # BDEF2
                b0 = self.idx(self.bidx)
                b1 = self.idx(self.bidx)
                w0 = r.f32()
                wb.append((b0, b1, 0, 0))
                ww.append((w0, 1.0 - w0, 0.0, 0.0))
            elif t in (2, 4):   # BDEF4 / QDEF
                b0 = self.idx(self.bidx)
                b1 = self.idx(self.bidx)
                b2 = self.idx(self.bidx)
                b3 = self.idx(self.bidx)
                w0, w1, w2, w3 = r.f32(), r.f32(), r.f32(), r.f32()
                wb.append((b0, b1, b2, b3))
                ww.append((w0, w1, w2, w3))
            elif t == 3:    # SDEF
                b0 = self.idx(self.bidx)
                b1 = self.idx(self.bidx)
                w0 = r.f32()
                r.raw(4 * 9)
                wb.append((b0, b1, 0, 0))
                ww.append((w0, 1.0 - w0, 0.0, 0.0))
            else:
                raise ValueError(f"unknown weight type {t}")
            es.append(r.f32())
        self.v_pos, self.v_nrm, self.v_uv = pos, nrm, uv
        self.v_wtype, self.v_wbone, self.v_wweight = wt, wb, ww

    def _read_faces(self):
        r = self.r
        n = r.i32()
        self.face_index_count = n
        self.faces = [self.uidx(self.vidx) for _ in range(n)]

    def _read_textures(self):
        r = self.r
        n = r.i32()
        self.textures = [self.text() for _ in range(n)]

    def _read_materials(self):
        r = self.r
        n = r.i32()
        self.materials = []
        for _ in range(n):
            m = {}
            m["name"] = self.text()
            m["name_en"] = self.text()
            m["diffuse"] = r.vec(4)
            m["specular"] = r.vec(3)
            m["shininess"] = r.f32()
            m["ambient"] = r.vec(3)
            m["draw_flag"] = r.u8()
            m["edge_color"] = r.vec(4)
            m["edge_size"] = r.f32()
            m["tex"] = self.idx(self.tidx)
            m["sphere_tex"] = self.idx(self.tidx)
            m["sphere_mode"] = r.u8()
            m["toon_flag"] = r.u8()
            if m["toon_flag"] == 0:
                m["toon"] = self.idx(self.tidx)
            else:
                m["toon"] = r.u8()
            m["memo"] = self.text()
            m["face_count"] = r.i32()
            self.materials.append(m)

    def _read_bones(self):
        r = self.r
        n = r.i32()
        self.bones = []
        for _ in range(n):
            b = {}
            b["name"] = self.text()
            b["name_en"] = self.text()
            b["pos"] = r.vec(3)
            b["parent"] = self.idx(self.bidx)
            b["layer"] = r.i32()
            flag = r.u16()
            b["flag"] = flag
            if flag & 0x0001:
                b["tail_bone"] = self.idx(self.bidx)
            else:
                b["tail_offset"] = r.vec(3)
            if flag & (0x0100 | 0x0200):
                b["inherit_parent"] = self.idx(self.bidx)
                b["inherit_weight"] = r.f32()
            if flag & 0x0400:
                b["fixed_axis"] = r.vec(3)
            if flag & 0x0800:
                b["local_x"] = r.vec(3)
                b["local_z"] = r.vec(3)
            if flag & 0x2000:
                b["ext_key"] = r.i32()
            if flag & 0x0020:
                self.idx(self.bidx)       # ik target
                r.i32()                   # loop count
                r.f32()                   # limit angle
                lc = r.i32()
                for _ in range(lc):
                    self.idx(self.bidx)
                    if r.u8() == 1:
                        r.raw(4 * 6)
            self.bones.append(b)


L = []
def P(s=""):
    L.append(str(s))


def main():
    p = os.path.join(ROOT, ".workbuddy", "vysna_work", "薇斯纳", "薇斯纳.pmx")
    P("=" * 78)
    P(f"### 薇斯纳.pmx   ({os.path.getsize(p):,} bytes)")
    P("=" * 78)
    m = PMX(p)
    P(f"版本          : {m.version}")
    P(f"名称          : {m.name!r} / {m.name_en!r}")
    P(f"编码          : {'UTF-16LE' if m.encoding == 0 else 'UTF-8'}")
    P(f"附加UV        : {m.add_uv}")
    P(f"索引宽度      : v={m.vidx} tex={m.tidx} mat={m.midx} bone={m.bidx} morph={m.moidx} rb={m.ridx}")
    P(f"顶点          : {m.vcount:,}")
    P(f"面索引数      : {m.face_index_count:,}  (= {m.face_index_count // 3:,} 三角形)")
    P(f"贴图          : {len(m.textures)}")
    P(f"材质          : {len(m.materials)}")
    P(f"骨骼          : {len(m.bones)}")
    P("")
    P("=" * 78)
    P("权重类型分布")
    P("=" * 78)
    from collections import Counter
    names = {0: "BDEF1", 1: "BDEF2", 2: "BDEF4", 3: "SDEF", 4: "QDEF"}
    c = Counter(m.v_wtype)
    for k, v in sorted(c.items()):
        P(f"  {names.get(k, k):<6}: {v:,}")
    P("")
    P("顶点包围盒 (PMX 原始坐标)")
    P("=" * 78)
    xs = [v[0] for v in m.v_pos]
    ys = [v[1] for v in m.v_pos]
    zs = [v[2] for v in m.v_pos]
    P(f"  X: [{min(xs):.3f}, {max(xs):.3f}]  跨度 {max(xs)-min(xs):.3f}")
    P(f"  Y: [{min(ys):.3f}, {max(ys):.3f}]  跨度 {max(ys)-min(ys):.3f}")
    P(f"  Z: [{min(zs):.3f}, {max(zs):.3f}]  跨度 {max(zs)-min(zs):.3f}")
    P("")
    P("=" * 78)
    P("贴图列表")
    P("=" * 78)
    for i, t in enumerate(m.textures):
        P(f"  [{i:>2}] {t}")
    P("")
    P("=" * 78)
    P("材质列表（含面数，用于筛选主体/翅膀）")
    P("=" * 78)
    P(f"  {'#':>3} {'名称':<28} {'面索引数':>9} {'三角形':>8} {'贴图':>5} {'球贴图':>6}  memo")
    acc = 0
    for i, mt in enumerate(m.materials):
        tex = m.textures[mt["tex"]] if 0 <= mt["tex"] < len(m.textures) else "<无>"
        sph = m.textures[mt["sphere_tex"]] if 0 <= mt["sphere_tex"] < len(m.textures) else "-"
        P(f"  {i:>3} {mt['name'][:28]:<28} {mt['face_count']:>9,} {mt['face_count']//3:>8,} "
          f"{tex[:22]:>22} {str(sph)[:20]:>20}  {mt['memo'][:20]}")
        acc += mt["face_count"]
    P(f"  --- 材质面数合计 {acc:,} / 顶点索引总数 {m.face_index_count:,} ---")
    P("")
    P("=" * 78)
    P("骨骼列表")
    P("=" * 78)
    for i, b in enumerate(m.bones):
        pn = m.bones[b["parent"]]["name"] if 0 <= b["parent"] < len(m.bones) else f"<{b['parent']}>"
        P(f"  [{i:>3}] {b['name']:<24} en={b['name_en'][:18]:<18} parent={pn[:20]:<20} "
          f"pos=({b['pos'][0]:7.3f},{b['pos'][1]:7.3f},{b['pos'][2]:7.3f}) flag=0x{b['flag']:04x}")

    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("OK ->", OUT, len(L), "lines")


if __name__ == "__main__":
    main()
