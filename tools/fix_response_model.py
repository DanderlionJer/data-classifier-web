from pathlib import Path

p = Path(__file__).resolve().parent.parent / "app" / "main.py"
t = p.read_text(encoding="utf-8")
old = '@app.post("/api/classify")\n'
new = '@app.post("/api/classify", response_model=None)\n'
if old not in t:
    raise SystemExit("pattern missing")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("ok")
