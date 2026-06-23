import importlib
import pkgutil
import pathlib

STRINGS = {}
module_dir = pathlib.Path(__file__).parent
for module_info in sorted(
    pkgutil.iter_modules([str(module_dir)]), key=lambda m: m.name
):
    if module_info.name == "__init__":
        continue
    mod = importlib.import_module(f".{module_info.name}", __package__)
    STRINGS.update(getattr(mod, "STRINGS", {}))
