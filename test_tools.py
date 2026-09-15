import sys, os, pathlib, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOTES_DIR = pathlib.Path("notes").resolve()

def _list_note_files():
    if not NOTES_DIR.exists():
        return []
    return sorted(f.name for f in NOTES_DIR.iterdir() if f.suffix in (".md", ".txt") and f.is_file())

def _read_note_file(filename):
    safe_name = pathlib.Path(filename).name
    full_path = NOTES_DIR / safe_name
    if not full_path.exists():
        raise FileNotFoundError(f"Note not found: {safe_name}")
    return full_path.read_text(encoding="utf-8")

def _score_relevance(text, query):
    words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 2]
    lower = text.lower()
    return sum(1 for w in words if w in lower)

def _search_notes(query, max_results=5):
    results = []
    for filename in _list_note_files():
        content = _read_note_file(filename)
        lines = content.splitlines()
        best_score = 0
        best_snippet = ""
        for i in range(len(lines)):
            window = " ".join(lines[i:i+3])
            score = _score_relevance(window, query)
            if score > best_score:
                best_score = score
                start = max(0, i-1)
                end = min(len(lines), i+5)
                best_snippet = "\n".join(lines[start:end]).strip()
        total_score = best_score + _score_relevance(filename, query)
        if total_score > 0:
            results.append({"file": filename, "score": total_score, "snippet": best_snippet})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]

print("=== TEST 1: search_notes('derivative') ===")
matches = _search_notes("derivative")
for m in matches:
    print("  " + m["file"] + " (score=" + str(m["score"]) + "): " + m["snippet"].splitlines()[0])

print()
print("=== TEST 2: search_notes('Newton second law F=ma') ===")
matches = _search_notes("Newton second law F=ma")
for m in matches:
    print("  " + m["file"] + " (score=" + str(m["score"]) + "): " + m["snippet"].splitlines()[0])

print()
print("=== TEST 3: read_note('calculus.md') - first 3 lines ===")
content = _read_note_file("calculus.md")
for line in content.splitlines()[:3]:
    print("  " + line)

print()
print("=== TEST 4: search_notes('hash table big-o complexity') ===")
matches = _search_notes("hash table big-o complexity")
for m in matches:
    print("  " + m["file"] + " (score=" + str(m["score"]) + "): " + m["snippet"].splitlines()[0])

print()
print("=== Available notes ===")
for f in _list_note_files():
    print("  " + f)
