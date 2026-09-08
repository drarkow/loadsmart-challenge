"""Build the LLM schema context from dbt artifacts, never from raw table rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_context(manifest_path: Path, catalog_path: Path | None = None) -> str:
    manifest = load_json(manifest_path)
    catalog = load_json(catalog_path) if catalog_path and catalog_path.exists() else {}
    catalog_nodes = catalog.get("nodes", {})

    models: list[dict[str, Any]] = []
    for node_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") != "model":
            continue

        columns = []
        catalog_node = catalog_nodes.get(node_id, {})
        for name, col in node.get("columns", {}).items():
            catalog_col = catalog_node.get("columns", {}).get(name, {})
            columns.append({
                "name": name,
                "description": col.get("description", ""),
                "data_type": catalog_col.get("type", ""),
            })

        models.append({
            "name": node.get("name"),
            "relation": f"{node.get('schema')}.{node.get('alias') or node.get('name')}",
            "description": node.get("description", ""),
            "columns": columns,
        })

    models.sort(key=lambda x: x["name"])
    return json.dumps({"models": models}, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="dbt_loadsmart/target/manifest.json")
    parser.add_argument("--catalog", default="dbt_loadsmart/target/catalog.json")
    parser.add_argument("--output", default="analysis/dbt_semantic_context.json")
    args = parser.parse_args()

    context = build_context(Path(args.manifest), Path(args.catalog))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(context, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
