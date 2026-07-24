"""Ponto de entrada único para gerar o banco de dados de exemplo.

Uso: python scripts/setup_dados.py [caminho-do-banco]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bi_toolkit.etl.carregar import criar_banco  # noqa: E402


def main() -> None:
    destino = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "BI_TOOLKIT_DB_PATH", "data/bi_toolkit.db"
    )
    criar_banco(destino)
    print(f"Dados de exemplo gerados em: {destino}")


if __name__ == "__main__":
    main()
