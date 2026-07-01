import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class RefResolver:
    def __init__(
        self,
        root_document: Mapping[str, Any],
        *,
        base_path: Path | None = None,
    ) -> None:
        self._root_document = root_document
        self._base_path = base_path
        self._cache: dict[Path, Mapping[str, Any]] = {}

    def resolve(self, schema: Mapping[str, Any]) -> Mapping[str, Any]:

        ref = schema.get("$ref")
        if ref is None:
            return schema

        if not isinstance(ref, str):
            raise TypeError("$ref must be a string")

        if ref.startswith("#"):
            return self._resolve_local(ref)

        return self._resolve_external(ref)

    def _resolve_local(self, ref: str) -> Mapping[str, Any]:

        node: Any = self._root_document

        path = ref[2:] if ref.startswith("#/") else ""

        if path == "":
            return self._root_document

        for part in path.split("/"):
            if not isinstance(node, Mapping):
                raise TypeError(f"Invalid $ref path: {ref}")

            if part not in node:
                raise ValueError(f"Unresolvable $ref: {ref}")

            node = node[part]

        if not isinstance(node, Mapping):
            raise TypeError(f"$ref must resolve to an object: {ref}")

        return node

    def _resolve_external(self, ref: str) -> Mapping[str, Any]:

        if "#" in ref:
            file_part, fragment = ref.split("#", 1)
            fragment = "#" + fragment
        else:
            file_part = ref
            fragment = ""

        if self._base_path is None:
            raise ValueError("Cannot resolve external $ref without base_path")

        file_path = (self._base_path / file_part).resolve()

        if file_path not in self._cache:
            with file_path.open() as f:
                self._cache[file_path] = json.load(f)

        document = self._cache[file_path]

        if fragment == "":
            return document

        return self._resolve_fragment(document, fragment)

    def _resolve_fragment(
        self,
        document: Mapping[str, Any],
        fragment: str,
    ) -> Mapping[str, Any]:

        node: Any = document

        path = fragment[2:] if fragment.startswith("#/") else ""

        if path == "":
            return document

        for part in path.split("/"):
            if not isinstance(node, Mapping):
                raise TypeError(f"Invalid fragment path: {fragment}")

            if part not in node:
                raise ValueError(f"Unresolvable fragment: {fragment}")

            node = node[part]

        if not isinstance(node, Mapping):
            raise TypeError(f"Fragment must resolve to an object: {fragment}")

        return node
