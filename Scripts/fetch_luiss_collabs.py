from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

from pyalex import Authors, config, Works

LUISS_INSTITUTION_ID = "i56441308"
config.email = "marcomalliani@gmail.com"

# the path finding solution is currently made in a very tricky way
# i'll do some research later to see if i can make this more straightforward

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BASE_DIR = PROJECT_ROOT / "Data"
RAW_DIR = BASE_DIR / "Raw"

AUTHORS_PATH = RAW_DIR / "luiss_authors.jsonl"
WORKS_PATH = RAW_DIR / "luiss_works.jsonl"

PER_PAGE = 200

def fetch_all_last_known_authors(institution_id: str, path: Path = AUTHORS_PATH):
    authors_query = (
        Authors()
        .filter(**{"last_known_institutions.id": institution_id})
        .select(["id", "display_name"])
    )

    save_data(authors_query, path)

def fetch_author_works(author_id: str):
    return (
        Works()
        .filter(**{"author.id": author_id})
        .select(["id", "display_name", "publication_year", "authorships"])
    )

def fetch_luiss_works(path: Path = WORKS_PATH):
    luiss_author_ids = get_existing_ids(AUTHORS_PATH)
    existing_work_ids = get_existing_ids(WORKS_PATH)

    for author_id in sorted(luiss_author_ids):
        author_works_query = fetch_author_works(author_id)
        save_data(author_works_query, path, existing_work_ids)

def save_data(query, out_path: Path, existing_ids: Set[str] = None):
    if existing_ids is None:
        existing_ids = get_existing_ids(out_path)

    for page in query.paginate(per_page=PER_PAGE, n_max=None):
        for entry in page:
            entry_id = entry.get("id")

            if not entry_id:
                continue

            if entry_id not in existing_ids:
                append_jsonl(out_path, entry)
                existing_ids.add(entry_id)

def get_existing_ids(path: Path, id_key: str = "id") -> Set[str]:
    if not path.exists():
        return set()

    ids: Set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            v = obj.get(id_key)
            if isinstance(v, str) and v:
                ids.add(v)
    return ids

def append_jsonl(path: Path, data: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    fetch_all_last_known_authors(LUISS_INSTITUTION_ID)
    fetch_luiss_works()
    print("Done")