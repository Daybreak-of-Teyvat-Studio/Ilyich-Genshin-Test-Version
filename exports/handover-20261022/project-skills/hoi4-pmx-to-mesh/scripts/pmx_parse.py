# -*- coding: utf-8 -*-
"""PMX 2.0 纯 Python 解析器（只解析转换所需的部分）。

用法：
    from pmx_parse import PMX
    pmx = PMX(path)
    pmx.v_pos      # list[(x,y,z)]
    pmx.v_nrm      # list[(x,y,z)]
    pmx.v_uv       # list[(u,v)]
    pmx.v_wtype    # list[int]      0=BDEF1 1=BDEF2 2=BDEF4 3=SDEF 4=QDEF
    pmx.v_wbone    # list[[4 int]]  不足补 -1
    pmx.v_wweight  # list[[4 float]] 不足补 0
    pmx.faces      # list[int]      每 3 个一组
    pmx.materials  # list[dict]
    pmx.textures   # list[str]
    pmx.bones      # list[dict]

参考：PMX 2.0 规格 http://blog.goo.ne.jp/utauuuta/e/...
"""
import struct

# PMX 顶点权重类型
BDEF1, BDEF2, BDEF4, SDEF, QDEF = 0, 1, 2, 3, 4


class Reader(object):
    def __init__(self, data):
        self.d = data
        self.p = 0

    def u8(self):
        v = self.d[self.p]
        self.p += 1
        return v

    def i8(self):
        v = struct.unpack_from("<b", self.d, self.p)[0]
        self.p += 1
        return v

    def u16(self):
        v = struct.unpack_from("<H", self.d, self.p)[0]
        self.p += 2
        return v

    def i16(self):
        v = struct.unpack_from("<h", self.d, self.p)[0]
        self.p += 2
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

    def _adv(self, n):
        out = struct.unpack_from("<%df" % n, self.d, self.p)
        self.p += 4 * n
        return list(out)

    def raw(self, n):
        v = self.d[self.p:self.p + n]
        self.p += n
        return v


class PMX(object):
    def __init__(self, path):
        with open(path, "rb") as f:
            raw = f.read()
        self.data = raw
        r = Reader(raw)

        magic = r.raw(4)
        if magic[:3] != b"PMX":
            raise ValueError("不是 PMX 文件: %r" % magic)
        self.version = r.f32()
        gcount = r.u8()
        g = [r.u8() for _ in range(gcount)]
        self.encoding = g[0]                       # 0=UTF-16LE 1=UTF-8
        self.add_uv = g[1]
        self.vidx = g[2]
        self.tidx = g[3]
        self.midx = g[4]
        self.bidx = g[5]
        self.moidx = g[6]
        self.ridx = g[7]
        self._r = r

        self.name = self.text(r)
        self.name_en = self.text(r)
        self.comment = self.text(r)
        self.comment_en = self.text(r)

        self._read_vertices(r)
        self._read_faces(r)
        self._read_textures(r)
        self._read_materials(r)
        self._read_bones(r)

    # ---------------------------------------------------------------- 基础读法
    def text(self, r):
        n = r.i32()
        b = r.raw(n)
        if self.encoding == 0:
            s = b.decode("utf-16-le", "replace")
        else:
            s = b.decode("utf-8", "replace")
        return s.rstrip("\x00")

    def idx(self, size):
        """有符号索引（可 -1）。"""
        r = self._r
        if size == 1:
            return r.i8()
        if size == 2:
            return r.i16()
        return r.i32()

    def uidx(self, size):
        r = self._r
        if size == 1:
            return r.u8()
        if size == 2:
            return r.u16()
        return r.u32()

    # ---------------------------------------------------------------- 顶点
    def _read_vertices(self, r):
        self._r = r
        n = r.i32()
        self.vcount = n
        pos = [None] * n
        nrm = [None] * n
        uv = [None] * n
        wt = [0] * n
        wb = [None] * n
        ww = [None] * n
        add = self.add_uv
        bs = self.bidx
        for i in range(n):
            pos[i] = r._adv(3)
            nrm[i] = r._adv(3)
            uv[i] = r._adv(2)
            for _ in range(add):
                r.raw(16)
            t = r.u8()
            wt[i] = t
            if t == BDEF1:
                b0 = self.idx(bs)
                wb[i] = [b0, -1, -1, -1]
                ww[i] = [1.0, 0.0, 0.0, 0.0]
            elif t == BDEF2:
                b0 = self.idx(bs)
                b1 = self.idx(bs)
                w0 = r.f32()
                wb[i] = [b0, b1, -1, -1]
                ww[i] = [w0, 1.0 - w0, 0.0, 0.0]
            elif t == BDEF4 or t == QDEF:
                b0 = self.idx(bs)
                b1 = self.idx(bs)
                b2 = self.idx(bs)
                b3 = self.idx(bs)
                w0 = r.f32()
                w1 = r.f32()
                w2 = r.f32()
                w3 = r.f32()
                wb[i] = [b0, b1, b2, b3]
                ww[i] = [w0, w1, w2, w3]
            elif t == SDEF:
                b0 = self.idx(bs)
                b1 = self.idx(bs)
                w0 = r.f32()
                r._adv(3)   # C
                r._adv(3)   # R0
                r._adv(3)   # R1
                wb[i] = [b0, b1, -1, -1]
                ww[i] = [w0, 1.0 - w0, 0.0, 0.0]
            else:
                raise ValueError("未知权重类型 %d @顶点%d" % (t, i))
            r.f32()   # edge scale
        self.v_pos = pos
        self.v_nrm = nrm
        self.v_uv = uv
        self.v_wtype = wt
        self.v_wbone = wb
        self.v_wweight = ww

    # ---------------------------------------------------------------- 面
    def _read_faces(self, r):
        n = r.i32()
        self.face_index_count = n
        vs = self.vidx
        self.faces = [self.uidx(vs) for _ in range(n)]

    # ---------------------------------------------------------------- 贴图
    def _read_textures(self, r):
        n = r.i32()
        self.textures = [self.text(r) for _ in range(n)]

    # ---------------------------------------------------------------- 材质
    def _read_materials(self, r):
        n = r.i32()
        ms = []
        for _ in range(n):
            m = {}
            m["name"] = self.text(r)
            m["name_en"] = self.text(r)
            m["diffuse"] = r._adv(4)
            m["specular"] = r._adv(3)
            m["shininess"] = r.f32()
            m["ambient"] = r._adv(3)
            m["draw_flag"] = r.u8()
            m["edge_color"] = r._adv(4)
            m["edge_size"] = r.f32()
            m["tex"] = self.idx(self.tidx)
            m["sphere"] = self.idx(self.tidx)
            m["sphere_mode"] = r.u8()
            shared = r.u8()
            m["toon_shared"] = shared
            if shared == 0:
                m["toon"] = self.idx(self.tidx)
            else:
                m["toon"] = r.u8()
            m["memo"] = self.text(r)
            m["face_count"] = r.i32()
            ms.append(m)
        self.materials = ms

    # ---------------------------------------------------------------- 骨骼
    def _read_bones(self, r):
        self._r = r
        n = r.i32()
        bones = []
        bs = self.bidx
        for bi in range(n):
            b = {"index": bi}
            b["name"] = self.text(r)
            b["name_en"] = self.text(r)
            b["pos"] = r._adv(3)
            b["parent"] = self.idx(bs)
            b["layer"] = r.i32()
            flag = r.u16()
            b["flag"] = flag
            if flag & 0x0001:
                b["tail_bone"] = self.idx(bs)
                b["tail_pos"] = None
            else:
                b["tail_bone"] = -1
                b["tail_pos"] = r._adv(3)
            if flag & (0x0100 | 0x0200):
                b["inherit_parent"] = self.idx(bs)
                b["inherit_weight"] = r.f32()
            if flag & 0x0400:
                b["fixed_axis"] = r._adv(3)
            if flag & 0x0800:
                b["local_x"] = r._adv(3)
                b["local_z"] = r._adv(3)
            if flag & 0x2000:
                b["ext_key"] = r.i32()
            if flag & 0x0020:
                b["ik_target"] = self.idx(bs)
                b["ik_loop"] = r.i32()
                b["ik_limit"] = r.f32()
                lc = r.i32()
                links = []
                for _ in range(lc):
                    # 每个 IK link 自带 1 字节 flag（1 = 带角度限制），
                    # 不是共用骨骼的 ik_limit —— 这是踩过的坑。
                    lk = {"bone": self.idx(bs)}
                    has_lim = r.u8()
                    if has_lim == 1:
                        lk["lo"] = r._adv(3)
                        lk["hi"] = r._adv(3)
                    links.append(lk)
                b["ik_links"] = links
            bones.append(b)
        self.bones = bones


if __name__ == "__main__":
    import sys
    p = PMX(sys.argv[1])
    print("PMX", p.version, "encoding", p.encoding, "name", p.name)
    print("顶点", p.vcount, "三角形", p.face_index_count // 3,
          "材质", len(p.materials), "骨骼", len(p.bones), "贴图", len(p.textures))
