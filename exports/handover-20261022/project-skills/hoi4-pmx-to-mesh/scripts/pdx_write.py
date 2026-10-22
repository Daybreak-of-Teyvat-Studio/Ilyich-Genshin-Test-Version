# -*- coding: utf-8 -*-
"""PDX (Clausewitz) .mesh 写出器 —— 纯 numpy，二进制与 pdx_data.write_meshfile 一致。

    from pdx_write import write_tree
    write_tree(path, root_element)     # root_element 与 pdx_data.read_meshfile 产出的同构

属性编码： b'!' + u8(名长) + 名 + 类型字符 + i32(数量) + 数据
  类型 'i' -> int32[]，'f' -> float32[]，'s' -> i32(串长) + 串 + '\0'
对象：     b'[' * depth + 名 + b'\0'

写出顺序完全沿用 pdx_data.write_meshfile（引擎对顺序敏感）。
"""
import numpy as np

MAGIC = b"@@b@"

MESH_PROPS = ["p", "n", "ta", "u0", "u1", "u2", "u3", "tri", "boundingsphere"]


# ---------------------------------------------------------------- 基础写单元
def _obj(name, depth):
    nb = name.encode("latin-1")
    if len(nb) >= 64:
        raise ValueError("对象名过长: %r" % name)
    return b"[" * depth + nb + b"\x00"


def _prop(name, kind, payload, count):
    nb = name.encode("latin-1")
    return b"!" + bytes([len(nb)]) + nb + kind.encode() + np.int32(count).tobytes() + payload


def p_int(name, values):
    a = np.asarray(values, dtype=np.int32)
    return _prop(name, "i", a.tobytes(), a.size)


def p_float(name, values):
    a = np.asarray(values, dtype=np.float32)
    return _prop(name, "f", a.tobytes(), a.size)


def p_str(name, value):
    b = value.encode("latin-1")
    payload = np.int32(len(b) + 1).tobytes() + b + b"\x00"
    return _prop(name, "s", payload, 1)


def write_prop(name, values):
    """按 Python 值类型自动选 int/float/str。values 可为标量或序列。"""
    if isinstance(values, str):
        return p_str(name, values)
    if isinstance(values, (int, np.integer)):
        return p_int(name, [int(values)])
    if isinstance(values, (float, np.floating)):
        return p_float(name, [float(values)])
    seq = list(values)
    if not seq:
        return b""
    if all(isinstance(v, (int, np.integer)) for v in seq):
        return p_int(name, [int(v) for v in seq])
    if all(isinstance(v, (float, np.floating)) for v in seq):
        return p_float(name, [float(v) for v in seq])
    if all(isinstance(v, str) for v in seq):
        return p_str(name, seq[0])
    raise NotImplementedError("混合类型属性 %s: %r" % (name, values[:3]))


# ---------------------------------------------------------------- 通用树写出
def write_tree(path, root, _return=False):
    out = bytearray()
    out += MAGIC
    if root.tag != "File":
        raise NotImplementedError("根节点须为 File，得到 %s" % root.tag)
    pdx = root.get("pdxasset")
    if pdx is None:
        pdx = [1, 0]
    out += write_prop("pdxasset", pdx)

    for object_xml in root.findall("object"):
        out += _obj(object_xml.tag, 1)
        for shape_xml in object_xml:
            out += _obj(shape_xml.tag, 2)

            for prop in ["lod"]:
                v = shape_xml.get(prop)
                if v is not None:
                    out += write_prop(prop, v)

            for child_xml in shape_xml:
                out += _obj(child_xml.tag, 3)

                if child_xml.tag == "mesh":
                    for prop in MESH_PROPS:
                        v = child_xml.get(prop)
                        if v is not None:
                            out += write_prop(prop, v)

                    aabb = child_xml.find("aabb")
                    if aabb is not None:
                        out += _obj("aabb", 4)
                        for prop in ["min", "max"]:
                            v = aabb.get(prop)
                            if v is not None:
                                out += write_prop(prop, v)

                    mate = child_xml.find("material")
                    if mate is not None:
                        out += _obj("material", 4)
                        for prop in ["shader", "diff", "n", "spec"]:
                            v = mate.get(prop)
                            if v is not None:
                                out += write_prop(prop, v)

                    skin = child_xml.find("skin")
                    if skin is not None:
                        out += _obj("skin", 4)
                        for prop in ["bones", "ix", "w"]:
                            v = skin.get(prop)
                            if v is not None:
                                out += write_prop(prop, v)

                elif child_xml.tag == "skeleton":
                    for bone_xml in child_xml:
                        out += _obj(bone_xml.tag, 4)
                        for prop in ["ix", "pa", "tx"]:
                            v = bone_xml.get(prop)
                            if v is not None:
                                out += write_prop(prop, v)

    for locator_xml in root.findall("locator"):
        out += _obj(locator_xml.tag, 1)
        for node_xml in locator_xml:
            out += _obj(node_xml.tag, 2)
            for prop in ["p", "q", "pa", "tx"]:
                v = node_xml.get(prop)
                if v is not None:
                    out += write_prop(prop, v)

    data = bytes(out)
    if not _return:
        with open(path, "wb") as f:
            f.write(data)
    return data


# ---------------------------------------------------------------- 切线
def tangents(positions, normals, uvs, tris):
    """按 UV 导数算逐顶点切线（第 4 分量存手性）。"""
    P = np.asarray(positions, dtype=np.float64)
    N = np.asarray(normals, dtype=np.float64)
    UV = np.asarray(uvs, dtype=np.float64)
    T = np.asarray(tris, dtype=np.int64).reshape(-1, 3)

    v0, v1, v2 = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    w0, w1, w2 = UV[T[:, 0]], UV[T[:, 1]], UV[T[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    d1, d2 = w1 - w0, w2 - w0
    r = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    r = np.where(np.abs(r) < 1e-12, 1e-12, r)
    f = (1.0 / r)[:, None]
    tan = (e1 * d2[:, 1, None] - e2 * d1[:, 1, None]) * f
    bit = (e1 * d2[:, 0, None] - e2 * d1[:, 0, None]) * f

    acc = np.zeros_like(P)
    accb = np.zeros_like(P)
    for k in range(3):
        np.add.at(acc, T[:, k], tan)
        np.add.at(accb, T[:, k], bit)

    dot = (N * acc).sum(1, keepdims=True)
    t = acc - N * dot
    ln = np.linalg.norm(t, axis=1, keepdims=True)
    bad = ln[:, 0] < 1e-9
    if bad.any():
        up = np.zeros_like(N)
        up[:, 1] = 1.0
        alt = np.cross(N, up)
        altn = np.linalg.norm(alt, axis=1, keepdims=True)
        alt2 = np.cross(N, np.array([1.0, 0.0, 0.0]))
        alt = np.where(altn > 1e-6, alt, alt2)
        alt = alt / np.maximum(np.linalg.norm(alt, axis=1, keepdims=True), 1e-12)
        t = np.where(bad[:, None], alt, t)
        ln = np.linalg.norm(t, axis=1, keepdims=True)
    t = t / np.maximum(ln, 1e-12)

    sign = np.sign((np.cross(N, t) * accb).sum(1))
    sign[sign == 0] = 1.0
    return np.concatenate([t, sign[:, None]], axis=1)
