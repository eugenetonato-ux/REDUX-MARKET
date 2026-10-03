"""
Script Python pour compiler les fichiers .po en .mo sans GNU gettext.
Utilise la librairie Babel pour la compilation.
Usage: python compile_messages.py
"""
import os
from pathlib import Path

try:
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po
except ImportError:
    print("Babel non installé. Lancement de: pip install Babel")
    import subprocess
    subprocess.run(["pip", "install", "Babel"], check=True)
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po

BASE_DIR = Path(__file__).resolve().parent
LOCALE_DIR = BASE_DIR / "locale"


def compile_po_to_mo(po_path: Path):
    mo_path = po_path.with_suffix(".mo")
    with open(po_path, "rb") as f:
        catalog = read_po(f)
    with open(mo_path, "wb") as f:
        write_mo(f, catalog)
    print(f"  OK: {po_path.relative_to(BASE_DIR)} -> {mo_path.name}")


def main():
    print("Compilation des fichiers .po en .mo (via Babel)...")
    po_files = list(LOCALE_DIR.rglob("*.po"))
    if not po_files:
        print("WARN: Aucun fichier .po trouve dans locale/")
        return
    for po_file in po_files:
        try:
            compile_po_to_mo(po_file)
        except Exception as e:
            print(f"  ERREUR sur {po_file}: {e}")
    print(f"\nOK: {len(po_files)} fichier(s) compile(s) avec succes.")


if __name__ == "__main__":
    main()
