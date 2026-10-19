"""Font-fallback check (kit v3): every visible non-ASCII character in the built HTML must exist in the Poppins woff2
files that page declares, otherwise Chrome draws it in a system font (found 2026-10-17: the rupee sign in 5 chapters and
arrows in 10 chapters of Industrialization, arrows in the rupee Short). jg.symbolize() turns arrows into SVG; the
Devanagari face covers the rupee sign. Runs on the phone (light) and in CI. Exit 1 when something falls back.
Usage: python3 glyph_audit.py DIR [DIR...]   (scans DIR/**/index.html)"""
import glob, html as H, os, re, shutil, struct, subprocess, sys, tempfile
from collections import defaultdict

TAGS = ["cmap", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post", "cvt ", "fpgm", "glyf", "loca", "prep", "CFF ", "VORG", "EBDT",
        "EBLC", "gasp", "hdmx", "kern", "LTSH", "PCLT", "VDMX", "vhea", "vmtx", "BASE", "GDEF", "GPOS", "GSUB", "EBSC", "JSTF", "MATH",
        "CBDT", "CBLC", "COLR", "CPAL", "SVG ", "sbix", "acnt", "avar", "bdat", "bloc", "bsln", "cvar", "fdsc", "feat", "fmtx", "fvar",
        "gvar", "hsty", "just", "lcar", "mort", "morx", "opbd", "prop", "trak", "Zapf", "Silf", "Glat", "Gloc", "Feat", "Sill"]

def _unbrotli(b):
    try:
        import brotli
        return brotli.decompress(b)
    except ImportError:
        exe = shutil.which("brotli") or "/data/data/com.termux/files/usr/bin/brotli"
        with tempfile.NamedTemporaryFile(suffix=".br", delete=False) as f: f.write(b)
        try: return subprocess.run([exe, "-d", "-c", f.name], capture_output=True, check=True).stdout
        finally: os.unlink(f.name)

def _b128(d, i):
    v = 0
    for _ in range(5):
        c = d[i]; i += 1; v = (v << 7) | (c & 0x7F)
        if not c & 0x80: return v, i
    raise ValueError("bad UIntBase128")

def codepoints(path):
    """Unicode code points in a WOFF2 font's cmap (the cmap table is never transformed in WOFF2)."""
    d = open(path, "rb").read()
    if d[:4] != b"wOF2": raise ValueError(f"{path}: not WOFF2")
    n = struct.unpack(">H", d[12:14])[0]; comp = struct.unpack(">I", d[20:24])[0]; i = 48; ents = []
    for _ in range(n):
        fl = d[i]; i += 1; idx = fl & 63; ver = fl >> 6
        if idx == 63: tag = d[i:i + 4].decode("latin1"); i += 4
        else: tag = TAGS[idx]
        ol, i = _b128(d, i); tl = ol
        if ((ver != 3) if tag in ("glyf", "loca") else (ver != 0)): tl, i = _b128(d, i)
        ents.append((tag, tl))
    raw = _unbrotli(d[i:i + comp]); off = 0; cm = None
    for tag, ln in ents:
        if tag == "cmap": cm = raw[off:off + ln]; break
        off += ln
    out = set(); nt = struct.unpack(">H", cm[2:4])[0]
    for k in range(nt):
        _, _, so = struct.unpack(">HHI", cm[4 + 8 * k:12 + 8 * k]); fmt = struct.unpack(">H", cm[so:so + 2])[0]
        if fmt == 4:
            sc = struct.unpack(">H", cm[so + 6:so + 8])[0] // 2; e = so + 14
            ends = struct.unpack(f">{sc}H", cm[e:e + 2 * sc]); st = struct.unpack(f">{sc}H", cm[e + 2 * sc + 2:e + 4 * sc + 2])
            for a, b in zip(st, ends):
                if a != 0xFFFF: out.update(range(a, b + 1))
        elif fmt == 12:
            for g in range(struct.unpack(">I", cm[so + 12:so + 16])[0]):
                a, b, _ = struct.unpack(">III", cm[so + 16 + 12 * g:so + 28 + 12 * g]); out.update(range(a, b + 1))
    return out

_cache = {}
def audit(dirs):
    miss = defaultdict(set); pages = 0
    for root in dirs:
        for f in sorted(glob.glob(os.path.join(root, "**/index.html"), recursive=True)):
            pages += 1; d = os.path.dirname(f); src = open(f, encoding="utf-8").read(); fam = defaultdict(set)
            for m in re.finditer(r'@font-face\s*\{[^}]*?font-family:\s*"?(\w+)"?[^}]*?url\("(assets/fonts/[^"]+\.woff2)"\)', src):
                fp = os.path.join(d, m.group(2))
                if os.path.exists(fp):
                    if fp not in _cache: _cache[fp] = codepoints(fp)
                    fam[m.group(1)] |= _cache[fp]
                else: miss[("font file missing: " + m.group(2), "")].add(os.path.relpath(d, root))
            body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", src, flags=re.S)
            js = " ".join(re.findall(r"<script>(.*?)</script>", src, flags=re.S))
            text = H.unescape(re.sub(r"<[^>]+>", " ", body)) + " " + " ".join(re.findall(r"textContent = '([^']*)'", js))
            for ch in set(text):
                o = ord(ch)
                if o > 126 and o != 0xA0 and not ch.isspace() and not 0xE000 <= o <= 0xF8FF and o not in fam["Poppins"]:
                    miss[(f"U+{o:04X} {ch}", "only in Inter" if o in fam["Inter"] else "in no page font")].add(os.path.relpath(d, root))
    return pages, miss

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    pages, miss = audit(sys.argv[1:])
    for (what, note), where in sorted(miss.items()):
        print(f"FALLBACK {what} ({note}) in {len(where)} page(s): {', '.join(sorted(where))[:150]}")
    print(f"glyph audit: {pages} page(s), {len(miss)} problem(s)")
    sys.exit(1 if miss else 0)
