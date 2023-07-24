import ast
from pathlib import Path


def symbols_from_module(module, path, root):
    for node in module.body:
        match node:
            case ast.Assign():
                for t in node.targets:
                    if name := getattr(t, 'id', False):
                        yield (name, path_to_mod(path, root))
            case ast.AnnAssign():
                yield (node.target.id, path_to_mod(path, root))  # type: ignore
            case ast.ImportFrom():
                for n in node.names:
                    yield (n.name, node.module)
            case ast.Import():
                continue
                for n in node.names:
                    yield (n.name, path_to_mod(path, root))
            case ast.FunctionDef() | ast.ClassDef() | ast.AsyncFunctionDef():
                yield (node.name, path_to_mod(path, root))
            case ast.Expr() | ast.For() | ast.Try() | ast.If() | ast.With() | ast.Delete() | ast.AugAssign() | ast.Raise() | ast.While() | ast.Assert():
                continue
            case _:
                print(f'Unidentified: {node} in {module}')


def symbols_from_file(path: Path, root: Path) -> list[str]:
    '''Parse a Python file and returns all importable symbols.'''

    try:
        text = path.read_text(encoding='utf8')
    except UnicodeDecodeError:
        print('Encoding error!')

    module = ast.parse(text)
    yield from symbols_from_module(module, path, root)


def path_to_mod(path: Path, root: Path) -> str:
    '''Convert a filepath to module dot notation.'''
    return '.'.join(path.with_suffix('').relative_to(root).parts)


def symbols_modules(root: Path):
    '''Recursively scan Python files and returns a dict of symbol->module.'''
    symbols: dict[str, list[str]] = {}
    if root.is_dir():
        for p in root.rglob('*.py'):
            for sym, mod in symbols_from_file(p, root):
                try:
                    symbols[sym].append(mod)
                except KeyError:
                    symbols[sym] = [mod]
    return symbols


def search_project_imports(project_dir, object_name):
    module = symbols_modules(project_dir).get(object_name)
    if not module:
        return None

    return f'from {sorted(module, key=len)[0]} import {object_name}'
