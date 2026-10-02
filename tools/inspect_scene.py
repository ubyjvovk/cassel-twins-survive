"""Summarize an exported WolvenKit scene without modifying game resources."""
import argparse
import json
from pathlib import Path


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def summarize(path):
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    root = document["Data"]["RootChunk"]
    result = {"resource_type": root["$type"], "actors": [], "nodes": []}
    for actor in root.get("actors", []):
        result["actors"].append({"name": actor["actorName"], "id": actor["actorId"]["id"]})
    for node in walk(root):
        if "nodeId" not in node or "$type" not in node:
            continue
        references = sorted({item["$value"] for item in walk(node)
                             if isinstance(item.get("$value"), str)
                             and item["$value"] not in {"None", "In", "Out", "CutDestination"}})
        operations = sorted({item["$type"] for item in walk(node)
                             if item.get("$type", "").startswith("quest")})
        result["nodes"].append({"id": node["nodeId"], "type": node["$type"],
                                "operations": operations, "references": references})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--nodes", type=int, nargs="*")
    args = parser.parse_args()
    if args.nodes is not None:
        root = json.loads(args.scene.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
        nodes = [entry["Data"] for entry in root["sceneGraph"]["Data"]["graph"]]
        for node in nodes:
            if node["nodeId"]["id"] not in args.nodes:
                continue
            node = dict(node)
            node["outputSockets"] = [
                {"stamp": s["stamp"], "to": [(d["nodeId"]["id"], d["isockStamp"]) for d in s["destinations"]]}
                for s in node.get("outputSockets", [])]
            print(json.dumps(node, ensure_ascii=False))
    else:
        print(json.dumps(summarize(args.scene), indent=2, ensure_ascii=False))
