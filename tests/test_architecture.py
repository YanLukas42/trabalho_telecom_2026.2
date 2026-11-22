"""Regras de arquitetura verificadas por teste (ver docs/arquitetura/README.md).

Regra que ninguém verifica apodrece. Aqui só entra o que dá para checar com a biblioteca padrão.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "telecom"

# Camadas: um pacote só importa de camadas com número MENOR (ou dele mesmo). Irmãos não se importam.
LAYER = {
    "__init__": 0, "settings": 0, "timefmt": 0, "reporting": 0,
    "audio": 1, "asr": 1, "metrics": 1,
    "experiments": 2,
    "diarization": 3, "benchmark": 3,
    "lessons": 4,
    "web": 5,
    "cli": 6,
}

# Pontos únicos de contato com o mundo externo.
SINGLE_CONTACT = {
    "subprocess": "telecom/audio/ffmpeg.py",
    "google": "telecom/asr/gemini.py",
}

MAX_PY_LINES = 400
# Dívida registrada: o limite só pode diminuir. Ao quebrar o arquivo, reduza ou remova a entrada.
MAX_LINES_EXCEPTIONS = {"telecom/web/static/app.js": 950}
MAX_JS_LINES = 400

FORBIDDEN_JS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function(")


def python_files() -> list[Path]:
    return sorted(path for path in PACKAGE.rglob("*.py") if "__pycache__" not in path.parts)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def imported_modules(path: Path) -> list[str]:
    """Nomes absolutos importados por um arquivo, inclusive importações tardias dentro de funções."""
    modules: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module == "telecom":
                modules += [f"telecom.{alias.name}" for alias in node.names]
            else:
                modules.append(node.module)
    return modules


def own_package(path: Path) -> str:
    parts = path.relative_to(PACKAGE).parts
    return parts[0].removesuffix(".py")


@pytest.mark.parametrize("path", python_files(), ids=relative)
def test_dependencies_point_downward(path):
    source = own_package(path)
    if source not in LAYER:
        pytest.fail(f"Pacote novo sem camada definida: {source}. Adicione-o a LAYER em tests/test_architecture.py.")
    for module in imported_modules(path):
        if not module.startswith("telecom."):
            continue
        target = module.split(".")[1]
        if target == source:
            continue
        assert target in LAYER, f"{relative(path)} importa {module}, de um pacote sem camada definida."
        assert LAYER[target] < LAYER[source], (
            f"{relative(path)} ({source}, camada {LAYER[source]}) importa {module} ({target}, camada {LAYER[target]}). "
            "Um módulo de nível baixo não pode conhecer um de nível alto."
        )


@pytest.mark.parametrize("path", python_files(), ids=relative)
def test_external_systems_have_a_single_contact_point(path):
    for module in imported_modules(path):
        top = module.split(".")[0]
        if top in SINGLE_CONTACT:
            assert relative(path) == SINGLE_CONTACT[top], (
                f"{relative(path)} importa {module}. Só {SINGLE_CONTACT[top]} pode falar com isso."
            )


def test_no_print_or_path_hacks_outside_the_cli():
    offenders = []
    for path in python_files():
        if own_package(path) == "cli":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            is_print = isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
            is_path_hack = isinstance(node, ast.Attribute) and node.attr == "path" and getattr(node.value, "id", "") == "sys"
            if is_print or is_path_hack:
                offenders.append(f"{relative(path)}:{node.lineno}")
    assert not offenders, f"Use logging em vez de print e imports absolutos em vez de sys.path: {offenders}"


@pytest.mark.parametrize("path", python_files() + sorted((PACKAGE / "web" / "static").glob("*.js")), ids=relative)
def test_files_stay_small_enough_to_read(path):
    limit = MAX_LINES_EXCEPTIONS.get(relative(path), MAX_PY_LINES if path.suffix == ".py" else MAX_JS_LINES)
    lines = len(path.read_text(encoding="utf-8").splitlines())
    assert lines <= limit, f"{relative(path)} tem {lines} linhas (limite {limit}). Divida o módulo em partes coesas."


@pytest.mark.parametrize("path", sorted((PACKAGE / "web" / "static").glob("*.js")), ids=relative)
def test_front_end_never_injects_markup(path):
    """O texto vem de transcrição e de IA: sempre createTextNode/textContent, nunca HTML montado."""
    text = path.read_text(encoding="utf-8")
    found = [token for token in FORBIDDEN_JS if token in text]
    assert not found, f"{relative(path)} usa {found}. Isso abre XSS a partir de texto de aluno ou da IA."
