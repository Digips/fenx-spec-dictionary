from __future__ import annotations


def _decode_json_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve an internal JSON pointer reference from an OpenAPI/Swagger spec."""
    if not isinstance(ref, str) or not ref:
        raise ValueError(f"Malformed ref: {ref!r}")

    if not ref.startswith("#/"):
        raise ValueError(f"Only internal refs are supported. Got: {ref}")

    if "://" in ref or ref.startswith("http"):
        raise ValueError(f"External refs are not supported. Got: {ref}")

    parts = ref[2:].split("/")
    if any(part == "" for part in parts):
        raise ValueError(f"Malformed ref path: {ref}")

    current: object = spec
    walked: list[str] = ["#"]

    for raw_part in parts:
        part = _decode_json_pointer_token(raw_part)
        walked.append(part)

        if not isinstance(current, dict):
            pointer = "/".join(walked[:-1])
            raise KeyError(
                f"Reference path is invalid at '{part}' (parent is not an object) in ref: {ref}; reached: {pointer}"
            )

        if part not in current:
            pointer = "/".join(walked[:-1])
            raise KeyError(
                f"Reference path segment '{part}' not found in ref: {ref}; checked: {pointer}"
            )

        current = current[part]

    if not isinstance(current, dict):
        raise KeyError(f"Reference does not point to an object node: {ref}")

    return current


def dereference(spec: dict, node: dict) -> dict:
    """Return the referenced object when node contains $ref, else return node unchanged."""
    if not isinstance(node, dict):
        return node

    ref = node.get("$ref")
    if isinstance(ref, str):
        return resolve_ref(spec, ref)

    return node
