"""Generate Claude context exclusively from dbt manifest/catalog artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"dbt artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_context(manifest_path: Path, catalog_path: Path) -> str:
    manifest = load_json(manifest_path)
    catalog = load_json(catalog_path)
    catalog_nodes = catalog.get("nodes", {})

    models: list[dict[str, Any]] = []
    for node_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") != "model":
            continue

        catalog_node = catalog_nodes.get(node_id, {})
        catalog_columns = catalog_node.get("columns", {})
        columns: list[dict[str, Any]] = []

        for name, col in node.get("columns", {}).items():
            catalog_col = catalog_columns.get(name, {})
            columns.append({
                "name": name,
                "description": col.get("description") or "",
                "data_type": catalog_col.get("type") or "unknown",
            })

        relation = {
            "database": node.get("database"),
            "schema": node.get("schema"),
            "identifier": node.get("alias") or node.get("name"),
        }

        models.append({
            "name": node.get("name"),
            "unique_id": node_id,
            "relation": relation,
            "materialization": node.get("config", {}).get("materialized"),
            "description": node.get("description") or "",
            "columns": columns,
        })

    models.sort(key=lambda model: model["name"] or "")

    payload = {
        "source": "dbt manifest.json + catalog.json",
        "dbt_version": manifest.get("metadata", {}).get("dbt_version"),
        "models": models,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build LLM metadata context from dbt artifacts.")
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
