#!/usr/bin/env python3
"""Valida la estructura del addon Berrocal.

Comprueba:
  * que todos los JSON se puedan leer;
  * que los UUID de los manifiestos sean únicos y las dependencias existan;
  * que cada bloque/objeto tenga textura declarada y el PNG exista;
  * que las claves de idioma cubran todos los bloques y objetos;
  * que las recetas apunten a objetos existentes.

Uso:
    python3 tools/validate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / "Berrocal_BP"
RP = ROOT / "Berrocal_RP"

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"JSON inválido en {path.relative_to(ROOT)}: {exc}")
        return None


def check_manifests() -> tuple[set[str], dict[str, dict]]:
    uuids: set[str] = set()
    manifests: dict[str, dict] = {}
    for pack in (BP, RP):
        path = pack / "manifest.json"
        data = load_json(path)
        if data is None:
            continue
        manifests[pack.name] = data
        for key in ("header",):
            uuid = data[key].get("uuid")
            if not uuid:
                fail(f"{path.relative_to(ROOT)}: falta header.uuid")
            elif uuid in uuids:
                fail(f"UUID duplicado: {uuid}")
            else:
                uuids.add(uuid)
        for module in data.get("modules", []):
            uuid = module.get("uuid")
            if not uuid:
                fail(f"{path.relative_to(ROOT)}: módulo sin uuid")
            elif uuid in uuids:
                fail(f"UUID duplicado: {uuid}")
            else:
                uuids.add(uuid)
        if not data.get("modules"):
            fail(f"{path.relative_to(ROOT)}: sin módulos")

    deps = manifests.get(BP.name, {}).get("dependencies", [])
    for dep in deps:
        if dep.get("uuid") not in uuids:
            fail(f"El behavior pack depende de un UUID desconocido: {dep.get('uuid')}")
    return uuids, manifests


def collect_files(kind: str) -> dict[str, dict]:
    """Devuelve {identifier: datos} para blocks o items del behavior pack."""
    result: dict[str, dict] = {}
    for path in sorted((BP / kind).glob("*.json")):
        data = load_json(path)
        if not data:
            continue
        key = "minecraft:block" if kind == "blocks" else "minecraft:item"
        section = data.get(key)
        if not section:
            fail(f"{path.relative_to(ROOT)}: no contiene '{key}'")
            continue
        identifier = section.get("description", {}).get("identifier")
        if not identifier:
            fail(f"{path.relative_to(ROOT)}: sin identifier")
            continue
        if not identifier.startswith("berrocal:"):
            fail(f"{path.relative_to(ROOT)}: el identificador debe usar el namespace berrocal: ({identifier})")
        if identifier in result:
            fail(f"Identificador duplicado: {identifier}")
        result[identifier] = section
    return result


def check_textures(blocks: dict[str, dict], items: dict[str, dict]) -> None:
    terrain = load_json(RP / "textures" / "terrain_texture.json") or {}
    items_atlas = load_json(RP / "textures" / "item_texture.json") or {}
    terrain_data = terrain.get("texture_data", {})
    item_data = items_atlas.get("texture_data", {})

    for identifier, block in blocks.items():
        components = block.get("components", {})
        instances = components.get("minecraft:material_instances")
        if not instances:
            fail(f"{identifier}: falta minecraft:material_instances")
            continue
        for face, instance in instances.items():
            texture = instance.get("texture") if isinstance(instance, dict) else None
            if not texture:
                fail(f"{identifier}: la cara '{face}' no tiene textura")
                continue
            if texture not in terrain_data:
                fail(f"{identifier}: la textura '{texture}' no está en terrain_texture.json")
                continue
            rel = terrain_data[texture]["textures"] + ".png"
            if not (RP / rel).is_file():
                fail(f"{identifier}: falta el archivo {rel}")

    for identifier, item in items.items():
        icon = item.get("components", {}).get("minecraft:icon")
        if isinstance(icon, dict):
            icon = icon.get("textures", {}).get("default")
        if not icon:
            fail(f"{identifier}: falta minecraft:icon")
            continue
        if icon not in item_data:
            fail(f"{identifier}: el icono '{icon}' no está en item_texture.json")
            continue
        rel = item_data[icon]["textures"] + ".png"
        if not (RP / rel).is_file():
            fail(f"{identifier}: falta el archivo {rel}")


def check_lang(blocks: dict[str, dict], items: dict[str, dict]) -> None:
    for lang in ("en_US", "es_ES", "es_MX"):
        path = RP / "texts" / f"{lang}.lang"
        if not path.is_file():
            fail(f"Falta el archivo de idioma {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for identifier in blocks:
            if f"tile.{identifier}.name=" not in text:
                fail(f"{lang}: falta la traducción de tile.{identifier}.name")
        for identifier in items:
            if f"item.{identifier}.name=" not in text:
                fail(f"{lang}: falta la traducción de item.{identifier}.name")


def check_recipes(blocks: dict[str, dict], items: dict[str, dict]) -> None:
    known = set(blocks) | set(items)
    known.add("minecraft:stick")
    known.add("minecraft:vine")
    for path in sorted((BP / "recipes").glob("*.json")):
        data = load_json(path)
        if not data:
            continue
        body = next((v for k, v in data.items() if k.startswith("minecraft:recipe")), None)
        if body is None:
            fail(f"{path.relative_to(ROOT)}: no contiene una receta válida")
            continue
        refs: list[str] = []
        for value in body.get("key", {}).values():
            refs.append(value.get("item"))
        for value in body.get("ingredients", []):
            refs.append(value.get("item"))
        if "input" in body:
            refs.append(body["input"].get("item"))
        refs.append(body.get("result", {}).get("item"))
        for ref in refs:
            if ref and ref not in known:
                fail(f"{path.relative_to(ROOT)}: referencia desconocida '{ref}'")


def main() -> int:
    check_manifests()
    blocks = collect_files("blocks")
    items = collect_files("items")
    check_textures(blocks, items)
    check_lang(blocks, items)
    check_recipes(blocks, items)

    print(f"Bloques: {len(blocks)} · Objetos: {len(items)}")
    if errors:
        print(f"\n{len(errors)} problema(s):")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    print("✓ Todo correcto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
