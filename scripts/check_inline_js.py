"""Vérifie la syntaxe JavaScript inline des cinq pages HTML avec Node."""
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "salaires.html", "exigences.html", "recruteurs.html", "mouvement.html"]

def main():
    erreurs = []
    for page in PAGES:
        html = (ROOT / page).read_text(encoding="utf-8")
        blocs = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.I | re.S)
        for i, bloc in enumerate(blocs, 1):
            with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as f:
                f.write(bloc)
                path = f.name
            r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
            if r.returncode:
                erreurs.append(f"{page} bloc {i}:\n{r.stderr}")
    if erreurs:
        raise SystemExit("\n".join(erreurs))
    print("JavaScript inline OK :", ", ".join(PAGES))

if __name__ == "__main__":
    main()
