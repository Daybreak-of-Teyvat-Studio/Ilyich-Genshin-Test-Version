# -*- coding: utf-8 -*-
"""Minimal HOI4 .mesh writer.

Binary layout (verified against the vanilla factory.mesh):

    "@@b@"
    "!<len><name><type><count><data>"   property
    "[<depth><namelen><name>\x00"        object, depth leading '['

Types: i = int32, f = float32, s = string.
"""


def _str_data(s):
    """A string value is: 's' + count(4, always 1) + strlen(4) + bytes + NUL.

    The vanilla files store the length INCLUDING the trailing NUL that
    terminates the string, so we append it and count it.
    """
    b = s.encode('latin-1') + b'\x00'
    return b's' + (1).to_bytes(4, 'little') + len(b).to_bytes(4, 'little') + b


def _prop(name, values):
    nb = name.encode('ascii')
    out = b'!' + bytes([len(nb)]) + nb
    if isinstance(values, str):
        return out + _str_data(values)
    if isinstance(values, (list, tuple)) and values and isinstance(values[0], str):
        return out + _str_data(''.join(values))
    if isinstance(values, (list, tuple)) and values and isinstance(values[0], int):
        out += b'i' + len(values).to_bytes(4, 'little')
        out += b''.join(int(x).to_bytes(4, 'little', signed=True) for x in values)
        return out
    # default: float32
    import struct
    out += b'f' + len(values).to_bytes(4, 'little')
    out += struct.pack('<%df' % len(values), *[float(x) for x in values])
    return out


def _obj(name, depth):
    """Object record: one '[' per depth level, then the name, then NUL.

    NOTE: there is NO length byte before the name -- the depth brackets
    carry the structure. (Verified against the vanilla factory.mesh:
    b'[object\\x00[[polySurfaceShape1\\x00[[[mesh\\x00'.)
    """
    return b'[' * depth + name.encode('ascii') + b'\x00'


def write_mesh(path, verts, norms, tangents, uvs, tris,
               shader, diff, nrm, spec, locators=()):
    """verts/norms/tangents/uvs are flat float lists; tris a flat int list."""
    mn = [min(verts[i::3]) for i in range(3)]
    mx = [max(verts[i::3]) for i in range(3)]
    mid = [(mn[i] + mx[i]) / 2.0 for i in range(3)]

    b = b'@@b@'
    # pdxasset is an INT array [1, 0] in the vanilla files, not a string.
    b += _prop('pdxasset', [1, 0])

    b += _obj('object', 1)
    b += _obj('polySurfaceShape1', 2)
    b += _obj('mesh', 3)

    b += _prop('p', [float(x) for x in verts])
    b += _prop('n', [float(x) for x in norms])
    b += _prop('ta', [float(x) for x in tangents])
    b += _prop('u0', [float(x) for x in uvs])
    b += _prop('tri', [int(x) for x in tris])

    b += _obj('aabb', 4)
    b += _prop('min', mn)
    b += _prop('max', mx)

    b += _obj('material', 4)
    b += _prop('shader', shader)
    b += _prop('diff', diff)
    b += _prop('n', nrm)
    b += _prop('spec', spec)

    # Locators are siblings of <object>, directly under <File> -- same as the
    # vanilla factory.mesh. Each locator is its own object whose NAME is the
    # locator name (e.g. factorysmoke), carrying p (vec3) and q (quat vec4).
    for lname, lp, lq in locators:
        b += _obj('locator', 1)
        b += _obj(lname, 2)
        b += _prop('p', [float(x) for x in lp])
        b += _prop('q', [float(x) for x in lq])

    with open(path, 'wb') as f:
        f.write(b)
    return len(b)