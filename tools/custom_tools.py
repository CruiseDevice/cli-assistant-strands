import psutil
from pathlib import Path
from datetime import datetime
from strands import tool


@tool
def get_system_info():
    """
    Get current system information (CPU, memory, disk usage)
    """
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'timestamp': datetime.now().isoformat()
    }


@tool
def save_note(title, content):
    """
    Save a not to local storage
    """
    notes_dir = Path('notes')
    notes_dir.mkdir(exist_ok=True)

    # sanitize filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
    filename = notes_dir / f"{safe_title}.txt"

    with open(filename, 'w') as f:
        f.write(f"Title: {title}\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"\n{content}\n")

    return f"Note saved: {filename}"


@tool
def list_notes() -> str:
    """
    List all saved notes
    """
    notes_dir = Path('notes')
    if not notes_dir.exists():
        return "No notes found."

    notes = []
    for note_file in notes_dir.glob('*.txt'):
        with open(note_file, 'r') as f:
            lines = f.readlines()
            title = lines[0].replace('Title: ', '').strip() if lines else note_file.stem
            date = lines[1].replace('Date: ', '').strip() if len(lines) > 1 else 'Unknown'
            notes.append(f"- {title} ({date})")

    return "\n".join(notes) if notes else "No notes found."


@tool
def search_web(query: str, max_results: int = 3) -> str:
    """
    Search the web for information using DuckDuckGo
    """

    try:
        from ddgs import DDGS

        # extract relevant information
        results = []

        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results)
            for result in search_results:
                title = result.get('title', '')
                body = result.get('body', '')
                href = result.get('href', '')
                results.append(f"**{title}**\n{body}\nSource: {href}\n")

        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"


@tool
def estimate_cost(input_text: str, output_words: int = 100) -> str:
    """
    Estimate the cost of a potential agent interaction.
    """
    # rough estimation: 1 token ≈ 0.75 words
    input_tokens = int(len(input_text.split()) * 1.3)
    output_tokens = int(output_words * 1.3)

    # Claude 3.5 Haiku pricing
    input_cost = (input_tokens / 1_000_000) * 0.80
    output_cost = (output_tokens / 1_000_000) * 4.00
    total_cost = input_cost + output_cost

    return f"""Cost Estimate:
- Input: {input_tokens} tokens → ${input_cost:.6f}
- Output: ~{output_tokens} tokens → ${output_cost:.6f}
- Total: ${total_cost:.6f}

For Claude 4 Sonnet, multiply by ~4x
"""
