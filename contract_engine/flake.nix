{
  description = "Common Python library dev environment (Python + venv, CI-aligned)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python313;
      in {
        packages.default = pkgs.mkShell {
          buildInputs = [
            python
          ];

          shellHook = ''
            set -e

            VENV=".venv"
            PY_VERSION="$(${python}/bin/python --version)"
            HASH_FILE="$VENV/.deps-hash"

            # Collect dependency files that exist
            REQ_FILES=""
            [ -f pyproject.toml ] && REQ_FILES="$REQ_FILES pyproject.toml"

            if [ -n "$REQ_FILES" ]; then
              REQ_HASH="$(sha256sum $REQ_FILES | sha256sum | cut -d' ' -f1)"
            else
              REQ_HASH="no-requirements"
            fi

            ENV_HASH="$PY_VERSION-$REQ_HASH"

            rebuild_venv() {
              echo "🔄 Rebuilding virtualenv"
              rm -rf "$VENV"
              ${python}/bin/python -m venv "$VENV"
              source "$VENV/bin/activate"
              pip install --upgrade pip
              pip install -e ".[dev]"
              echo "$ENV_HASH" > "$HASH_FILE"
            }

            if [ ! -d "$VENV" ]; then
              rebuild_venv
            elif [ ! -f "$HASH_FILE" ]; then
              rebuild_venv
            elif [ "$(cat "$HASH_FILE")" != "$ENV_HASH" ]; then
              rebuild_venv
            else
              source "$VENV/bin/activate"
            fi

            echo "🐍 Python: $(python --version)"
            echo "📦 Venv: $VENV"
          '';
        };
      });
}
