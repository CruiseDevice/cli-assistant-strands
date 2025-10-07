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
