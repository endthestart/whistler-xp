"""Read bitmaps, icons, cursors and text resources from Windows PE files."""
import io
import struct

import pefile
from PIL import Image

MAGENTA = (255, 0, 255)


class PE:
    def __init__(self, path):
        self.pe = pefile.PE(path, fast_load=True)
        self.pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])

    def _type(self, typename):
        for t in getattr(self.pe, "DIRECTORY_ENTRY_RESOURCE", []).entries if hasattr(
                self.pe, "DIRECTORY_ENTRY_RESOURCE") else []:
            tn = str(t.name) if t.name else pefile.RESOURCE_TYPE.get(t.id, t.id)
            if tn == typename:
                return t
        return None

    def _data(self, entry):
        lang = entry.directory.entries[0]
        d = lang.data.struct
        return self.pe.get_data(d.OffsetToData, d.Size)

    def names(self, typename):
        t = self._type(typename)
        if t is None:
            return []
        return [str(e.name) if e.name else e.id for e in t.directory.entries]

    def raw(self, typename, name):
        t = self._type(typename)
        if t is None:
            return None
        for e in t.directory.entries:
            ename = str(e.name) if e.name else e.id
            if ename == name or (isinstance(name, str) and str(ename).upper() == name.upper()):
                return self._data(e)
        return None

    def text(self, typename, name):
        data = self.raw(typename, name)
        if data is None:
            return None
        if data[:2] == b"\xff\xfe":
            data = data[2:]
        try:
            return data.decode("utf-16-le")
        except UnicodeDecodeError:
            return data.decode("latin-1")

    def bitmap(self, name):
        dib = self.raw("RT_BITMAP", name)
        return dib_to_image(dib) if dib else None

    # ---------------------------------------------------------------- icons
    def icon_groups(self):
        return self.names("RT_GROUP_ICON")

    def icon(self, group):
        """Return {size: RGBA image} for an icon group (largest colour depth per size)."""
        data = self.raw("RT_GROUP_ICON", group)
        if not data:
            return {}
        _, _, count = struct.unpack("<HHH", data[:6])
        out = {}
        best_bpp = {}
        for i in range(count):
            w, h, colors, _, planes, bpp, size, rid = struct.unpack("<BBBBHHIH", data[6 + i * 14:20 + i * 14])
            w = w or 256
            h = h or 256
            raw = self.raw("RT_ICON", rid)
            if not raw:
                continue
            img = icon_entry_to_image(raw, w, h)
            if img is None:
                continue
            if w not in out or bpp > best_bpp[w]:
                out[w] = img
                best_bpp[w] = bpp
        return out

    def cursor(self, group):
        """Return (RGBA image, (hot_x, hot_y)) for a cursor group's best entry."""
        data = self.raw("RT_GROUP_CURSOR", group)
        if not data:
            return None
        _, _, count = struct.unpack("<HHH", data[:6])
        best = None
        for i in range(count):
            w, h2, planes, bpp, size, rid = struct.unpack("<HHHHIH", data[6 + i * 14:20 + i * 14])
            raw = self.raw("RT_CURSOR", rid)
            if not raw:
                continue
            hx, hy = struct.unpack("<HH", raw[:4])
            img = icon_entry_to_image(raw[4:], w, h2 // 2)
            if img is None:
                continue
            if best is None or (bpp, w) > best[0]:
                best = ((bpp, w), img, (hx, hy))
        return (best[1], best[2]) if best else None


def dib_to_image(dib):
    hsize, w, h, planes, bpp = struct.unpack("<IiiHH", dib[:16])
    compression = struct.unpack("<I", dib[16:20])[0]
    if bpp == 32 and compression in (0, 3):
        off = hsize + (12 if compression == 3 and hsize == 40 else 0)
        img = Image.frombuffer("RGBA", (w, abs(h)), dib[off:off + w * abs(h) * 4], "raw", "BGRA", 0,
                               -1 if h > 0 else 1)
        if img.getextrema()[3] == (0, 0):          # no alpha channel in use
            img = img.convert("RGB").convert("RGBA")
        return img.copy()
    clr = struct.unpack("<I", dib[32:36])[0]
    off = 14 + hsize + (4 * (clr or (1 << bpp)) if bpp <= 8 else 0)
    bmp = b"BM" + struct.pack("<IHHI", 14 + len(dib), 0, 0, off) + dib
    return Image.open(io.BytesIO(bmp)).convert("RGBA")


def icon_entry_to_image(raw, w=None, h=None):
    """Decode an icon/cursor image resource (DIB with AND mask, or PNG) to RGBA."""
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    try:
        hsize, bw, bh2, planes, bpp = struct.unpack("<IiiHH", raw[:16])
        clr = struct.unpack("<I", raw[32:36])[0]
        bh = bh2 // 2
        ncol = (clr or (1 << bpp)) if bpp <= 8 else 0
        pal_off = hsize
        palette = [raw[pal_off + 4 * i:pal_off + 4 * i + 3][::-1] for i in range(ncol)]
        xor_off = pal_off + 4 * ncol
        stride = ((bw * bpp + 31) // 32) * 4
        and_off = xor_off + stride * bh
        and_stride = ((bw + 31) // 32) * 4
        out = Image.new("RGBA", (bw, bh))
        px = out.load()
        has_alpha = False
        for y in range(bh):
            row = raw[xor_off + (bh - 1 - y) * stride: xor_off + (bh - y) * stride]
            arow = raw[and_off + (bh - 1 - y) * and_stride: and_off + (bh - y) * and_stride]
            for x in range(bw):
                masked = bool(arow and (arow[x >> 3] >> (7 - (x & 7))) & 1)
                if bpp == 32:
                    b, g, r, a = row[4 * x:4 * x + 4]
                    has_alpha = has_alpha or a != 0
                    px[x, y] = (r, g, b, a if a else (0 if masked else 255))
                elif bpp == 24:
                    b, g, r = row[3 * x:3 * x + 3]
                    px[x, y] = (r, g, b, 0 if masked else 255)
                else:
                    per = 8 // bpp
                    byte = row[x // per]
                    shift = (per - 1 - (x % per)) * bpp
                    idx = (byte >> shift) & ((1 << bpp) - 1)
                    r, g, b = palette[idx] if idx < len(palette) else (0, 0, 0)
                    if masked and (r, g, b) != (0, 0, 0):
                        # "invert screen" pixel (I-beam, crosshair): draw it black
                        px[x, y] = (0, 0, 0, 255)
                    else:
                        px[x, y] = (r, g, b, 0 if masked else 255)
        if bpp == 32 and not has_alpha:
            # old 32bpp icons without alpha: fall back to the AND mask
            for y in range(bh):
                arow = raw[and_off + (bh - 1 - y) * and_stride: and_off + (bh - y) * and_stride]
                for x in range(bw):
                    r, g, b, _ = px[x, y]
                    masked = bool(arow and (arow[x >> 3] >> (7 - (x & 7))) & 1)
                    px[x, y] = (r, g, b, 0 if masked else 255)
        return out
    except (struct.error, IndexError, ValueError):
        return None


def key_out(img, color=MAGENTA):
    """Make pixels of `color` transparent (used by 24-bit theme bitmaps)."""
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if (r, g, b) == color:
                px[x, y] = (0, 0, 0, 0)
    return img
