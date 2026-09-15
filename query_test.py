"""
Live tool test — simulates exactly what Bob calls when you ask:
  "What are the time complexities of a hash table?"
Calls both ask_study_question and read_note (data-structures.md).
"""
import sys, pathlib, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOTES_DIR = pathlib.Path(__file__).resolve().parent / "notes"

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
        best_score, best_snippet = 0, ""
        for i in range(len(lines)):
            window = " ".join(lines[i:i+3])
            score = _score_relevance(window, query)
            if score > best_score:
                best_score = score
                start, end = max(0, i - 1), min(len(lines), i + 5)
                best_snippet = "\n".join(lines[start:end]).strip()
        total_score = best_score + _score_relevance(filename, query)
        if total_score > 0:
            results.append({"file": filename, "score": total_score, "snippet": best_snippet})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]

QUESTION = "What are the time complexities of a hash table?"

print("=" * 60)
print("TOOL CALL: ask_study_question")
print("QUESTION :", QUESTION)
print("=" * 60)

matches = _search_notes(QUESTION, max_results=3)
for i, m in enumerate(matches, 1):
    print(f"\n[Source {i}] {m['file']}  (relevance score: {m['score']})")
    print("-" * 40)
    print(m["snippet"])

print()
print("=" * 60)
print("TOOL CALL: read_note('data-structures.md')")
print("=" * 60)
print(_read_note_file("data-structures.md"))
