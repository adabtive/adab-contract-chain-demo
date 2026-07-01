import base64
import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

from contract_engine.application.interfaces.contract_parser import ContractParser
from contract_engine.domain.contract import Contract

logger = logging.getLogger(__name__)


class ContractLoaderService:
    def __init__(self, parser: ContractParser) -> None:
        self._parser = parser

    def load(
        self,
        source: str | dict[str, Any],
        *,
        base_path: Path | None = None,
    ) -> Contract:

        resolved_path: Path | None = None

        if isinstance(source, str) and not source.startswith(("http://", "https://")):
            path = Path(source)
            if path.exists():
                resolved_path = path

        schema = self._resolve_source(source)

        if base_path is None and resolved_path is not None:
            base_path = resolved_path.parent

        return self._parser.parse(schema, base_path=base_path)

    def _resolve_source(self, source: str | dict[str, Any]) -> dict[str, Any]:

        if isinstance(source, dict):
            return source

        if source.startswith(("http://", "https://")):
            data = self._load_url(source)

        elif Path(source).exists():
            data = self._load_file(Path(source))

        else:
            try:
                data = json.loads(source)
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid JSON contract source") from exc

        if not isinstance(data, dict):
            raise TypeError("Contract schema must be a JSON object (top-level JSON must be an object)")

        return data

    def _load_file(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in contract file: {path}") from exc

    def _maybe_convert_azure_devops_url(self, url: str) -> str:
        """
        Converts Azure DevOps UI URLs to API URLs automatically.
        """

        if "_git" not in url or "dev.azure.com" not in url:
            return url

        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        path = query.get("path", [None])[0]
        version = query.get("version", [None])[0]

        if not path:
            return url  # can't convert

        # Extract parts from path: /{org}/{project}/_git/{repo}
        parts = parsed.path.strip("/").split("/")

        try:
            org = parts[0]
            project = parts[1]
            repo = parts[3]  # after "_git"
        except IndexError:
            return url  # fallback safely

        api_url = (
            f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items"
            f"?path={path}&includeContent=true&api-version=7.0"
        )

        if version:
            api_url += f"&versionDescriptor.version={version.replace('GB', '')}"

        return api_url

    def _load_url(self, url: str) -> Any:
        url = self._maybe_convert_azure_devops_url(url)
        headers = self._build_headers(url)

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Handle Azure DevOps-style responses where content is wrapped
        if isinstance(data, dict) and "content" in data:
            try:
                return json.loads(data["content"])
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Failed to parse 'content' field as JSON from URL response",
                    exc_info=exc,
                )

        return data

    def _build_headers(self, url: str) -> dict[str, str]:
        """
        Generic authentication mechanism for HTTP contract loading.

        Uses environment variables:
        - CONTRACT_AUTH_TOKEN
        - CONTRACT_AUTH_TYPE (bearer | basic, default: bearer)

        Works for Azure DevOps, GitHub, and other providers.
        """

        # Only attach auth to HTTPS requests (avoid leaking tokens)
        if not url.startswith("https://"):
            return {}

        token = os.getenv("CONTRACT_AUTH_TOKEN")
        if not token:
            return {}

        auth_type = os.getenv("CONTRACT_AUTH_TYPE", "bearer").lower()

        if auth_type == "basic":
            encoded = base64.b64encode(f":{token}".encode()).decode()
            return {"Authorization": f"Basic {encoded}"}

        return {"Authorization": f"Bearer {token}"}
