#!/usr/bin/env python3
"""
AI College Study Assistant — MCP Server (Python)
Exposes three tools to Bob:
  • search_notes         — keyword search across all .md/.txt notes
  • read_note            — read the full content of one note file
  • ask_study_question   — semantic search + composed study response
"""

import os
import sys
import pathlib
import re
try:
    from mcp.server.fastmcp import FastMCP as MCPServer  # mcp < 2
except ModuleNotFoundError:
    from mcp.server.mcpserver import MCPServer  # mcp >= 2

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# NOTES_DIR can be overridden via environment variable; default is the
# "notes/" folder sibling to this script.
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
NOTES_DIR = pathlib.Path(os.environ.get("NOTES_DIR", _SCRIPT_DIR / "notes")).resolve()

mcp = MCPServer("study-assistant")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_note_files() -> list[str]:
    """Return sorted list of .md and .txt filenames in NOTES_DIR."""
    if not NOTES_DIR.exists():
        return []
    return sorted(
        f.name
        for f in NOTES_DIR.iterdir()
        if f.suffix in (".md", ".txt") and f.is_file()
    )


def _read_note_file(filename: str) -> str:
    """Read a note file safely (blocks path traversal)."""
    safe_name = pathlib.Path(filename).name  # strip any directory component
    full_path = NOTES_DIR / safe_name
    if not full_path.exists():
        raise FileNotFoundError(f"Note not found: {safe_name}")
    return full_path.read_text(encoding="utf-8")


def _score_relevance(text: str, query: str) -> int:
    """Count how many query words appear in text (case-insensitive)."""
    words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 2]
    lower = text.lower()
    return sum(1 for w in words if w in lower)


def _search_notes(query: str, max_results: int = 5) -> list[dict]:
    """Search all notes; return top matches sorted by relevance score."""
    results = []
    for filename in _list_note_files():
        try:
            content = _read_note_file(filename)
        except OSError:
            continue

        lines = content.splitlines()
        best_score = 0
        best_snippet = ""

        # Slide a 3-line window to find the most relevant excerpt
        for i in range(len(lines)):
            window = " ".join(lines[i : i + 3])
            score = _score_relevance(window, query)
            if score > best_score:
                best_score = score
                start = max(0, i - 1)
                end = min(len(lines), i + 5)
                best_snippet = "\n".join(lines[start:end]).strip()

        # Bonus score if the filename itself matches
        total_score = best_score + _score_relevance(filename, query)
        if total_score > 0:
            results.append(
                {"file": filename, "score": total_score, "snippet": best_snippet}
            )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


# ---------------------------------------------------------------------------
# Tool 1 — search_notes
# ---------------------------------------------------------------------------

@mcp.tool()
def search_notes(query: str, max_results: int = 5) -> str:
    """
    Search your local study notes by keyword or topic.
    Returns a list of matching note files with relevant excerpts.

    Args:
        query: The topic, keyword, or concept to search for.
        max_results: Maximum number of results to return (1-10, default 5).
    """
    max_results = max(1, min(10, max_results))
    matches = _search_notes(query, max_results)

    if not matches:
        available = _list_note_files()
        note_list = "\n".join(f"  • {f}" for f in available) or "  (no notes found — check NOTES_DIR)"
        return f'No notes found matching "{query}".\n\nAvailable note files:\n{note_list}'

    lines = [f'Found {len(matches)} note(s) matching "{query}":\n']
    for m in matches:
        first_line = m["snippet"].splitlines()[0] if m["snippet"] else ""
        lines.append(f'📄 **{m["file"]}** (relevance score: {m["score"]})\n> {first_line}\n')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2 — read_note
# ---------------------------------------------------------------------------

@mcp.tool()
def read_note(filename: str) -> str:
    """
    Read the full content of a specific study note file.

    Args:
        filename: The filename of the note to read (e.g. 'calculus.md').
    """
    try:
        content = _read_note_file(filename)
        return f"## {filename}\n\n{content}"
    except FileNotFoundError as exc:
        available = _list_note_files()
        note_list = "\n".join(f"  • {f}" for f in available) or "  (none)"
        return (
            f"Could not read \"{filename}\": {exc}\n\n"
            f"Available notes:\n{note_list}"
        )


# ---------------------------------------------------------------------------
# Tool 3 — ask_study_question
# ---------------------------------------------------------------------------

@mcp.tool()
def ask_study_question(question: str, include_examples: bool = True) -> str:
    """
    Ask a study question. Searches all local notes for relevant content and
    returns a composed study response with source excerpts and context.

    Args:
        question: The study question or concept to explain
                  (e.g. 'What is Newton's second law?').
        include_examples: If True, appends a prompt for a real-world example
                          (default True).
    """
    matches = _search_notes(question, max_results=3)

    if not matches:
        available = _list_note_files()
        note_list = "\n".join(f"  • {f}" for f in available) or "  (none)"
        return (
            f'No relevant notes found for: "{question}"\n\n'
            f"Available notes:\n{note_list}"
        )

    sections = []
    for i, m in enumerate(matches, 1):
        sections.append(
            f"### Source {i}: {m['file']} (relevance score: {m['score']})\n"
            f"```\n{m['snippet']}\n```"
        )

    example_prompt = (
        "\n\n*Please also provide a simple real-world example based on the notes above.*"
        if include_examples
        else ""
    )

    parts = [
        "## Study Assistant — Notes Search Results",
        f"**Question:** {question}",
        "",
        f"Found {len(matches)} relevant note(s):",
        "",
        *sections,
        "",
        "---",
        f"*These excerpts are from your local study notes in: {NOTES_DIR}*",
        example_prompt,
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[study-assistant] MCP server running — notes dir: {NOTES_DIR}", file=sys.stderr)
    mcp.run(transport="stdio")
