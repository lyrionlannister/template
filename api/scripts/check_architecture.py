"""Fallback de architecture-guard si import-linter no esta disponible.

Heuristica sobre imports via ast: controller no importa repository/model
directo, model no importa de capas superiores, cruce entre dominios solo
via services. Ver .claude/skills/architecture-guard/SKILL.md.

Uso: uv run python scripts/check_architecture.py
"""

import ast
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent / "app"
LAYER_FORBIDDEN = {
    "controllers": {"repositories", "models"},
    "models": {"services", "repositories", "controllers"},
}
# Excepción legítima y documentada (code-distribution, 3.4 "Cableado global"):
# core/config/models_registry.py importa cada *_model.py de cada dominio a
# propósito, para que SQLAlchemy registre el mapeo en Base.metadata antes de
# que Alembic compare el esquema. No es un cruce de dominio sin pasar por
# services -- es infraestructura compartida que el propio proyecto pide.
EXCEPCIONES_CRUCE_DOMINIO = {"core/config/models_registry.py"}


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
    return mods


def check_file(path: Path, domains: list[str]) -> list[str]:
    rel = path.relative_to(APP_ROOT)
    if rel.as_posix() in EXCEPCIONES_CRUCE_DOMINIO:
        return []
    parts = rel.parts  # <dominio>/<capa>/archivo.py
    if len(parts) < 3:
        return []
    domain, layer = parts[0], parts[1]
    violations = []

    for mod in imported_modules(path):
        if not mod.startswith("app."):
            continue
        mod_parts = mod.split(".")
        if len(mod_parts) < 3:
            continue
        mod_domain, mod_layer = mod_parts[1], mod_parts[2]

        forbidden_layers = LAYER_FORBIDDEN.get(layer, set())
        if mod_domain == domain and mod_layer in forbidden_layers:
            violations.append(
                f"{rel}: {layer}/ importa {mod} (capa prohibida: {mod_layer})"
            )

        if (
            mod_domain != domain
            and mod_domain in domains
            and mod_layer in {"repositories", "models"}
        ):
            violations.append(
                f"{rel}: cruza a dominio '{mod_domain}' via {mod_layer} en vez de services"
            )

    return violations


def main() -> int:
    if not APP_ROOT.exists():
        print(f"No existe {APP_ROOT}")
        return 1

    domains = sorted(p.name for p in APP_ROOT.iterdir() if p.is_dir())
    violations = []
    for py_file in APP_ROOT.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        violations += check_file(py_file, domains)

    if violations:
        print("Violaciones de arquitectura encontradas:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print(f"Sin violaciones. {len(domains)} dominios revisados: {', '.join(domains)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
