#!/usr/bin/env python3
"""Empaqueta el addon Berrocal.

Genera en dist/:
  Berrocal.mcaddon            -> instala comportamiento + recursos de una vez
  Berrocal_BP.mcpack          -> solo el behavior pack
  Berrocal_RP.mcpack          -> solo el resource pack

Uso:
    python3 tools/build.py
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BP = ROOT / "Berrocal_BP"
RP = ROOT / "Berrocal_RP"

# Carpetas/ficheros que nunca deben acabar dentro del paquete.
IGNORED = {".DS_Store", "Thumbs.db", "__pycache__", ".gitkeep"}


def add_pack(zf: zipfile.ZipFile, pack_dir: Path, prefix: str) -> int:
    """Añade una carpeta de pack al zip con el prefijo indicado."""
    count = 0
    for path in sorted(pack_dir.rglob("*")):
        if path.is_dir() or path.name in IGNORED:
            continue
        zf.write(path, f"{prefix}/{path.relative_to(pack_dir).as_posix()}")
        count += 1
    return count


def read_version() -> str:
    manifest = json.loads((BP / "manifest.json").read_text(encoding="utf-8"))
    return ".".join(str(v) for v in manifest["header"]["version"])


def build() -> None:
    DIST.mkdir(exist_ok=True)
    version = read_version()

    # Limpia builds anteriores.
    for old in DIST.glob("*.mc*"):
        old.unlink()

    # .mcaddon con ambos packs.
    mcaddon = DIST / "Berrocal.mcaddon"
    with zipfile.ZipFile(mcaddon, "w", zipfile.ZIP_DEFLATED) as zf:
        bp_files = add_pack(zf, BP, BP.name)
        rp_files = add_pack(zf, RP, RP.name)

    # Packs sueltos, por si alguien solo quiere uno.
    for pack, name in ((BP, "Berrocal_BP.mcpack"), (RP, "Berrocal_RP.mcpack")):
        with zipfile.ZipFile(DIST / name, "w", zipfile.ZIP_DEFLATED) as zf:
            add_pack(zf, pack, "")

    size_kb = mcaddon.stat().st_size / 1024
    print(f"Berrocal v{version}")
    print(f"  {mcaddon.name}: {bp_files} archivos de BP + {rp_files} de RP ({size_kb:.1f} KB)")
    print("  Berrocal_BP.mcpack  (solo comportamiento)")
    print("  Berrocal_RP.mcpack  (solo recursos)")


if __name__ == "__main__":
    build()
