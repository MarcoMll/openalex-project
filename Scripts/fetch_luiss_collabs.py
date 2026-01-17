from __future__ import annotations

import json

from pathlib import Path
from typing import Any, Dict, Set, TextIO
from itertools import islice

from pyalex import Authors, config, Works

LUISS_INSTITUTION_ID = "i56441308"
config.email = "marcomalliani@gmail.com" # apparently by adding email it raises our per-second request limit
                                         # by 10 times (from 1 to 10)

# the path finding solution is currently made in a very tricky way
# I'll do some research later to see if i can make this more straightforward

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BASE_DIR = PROJECT_ROOT / "Data"
RAW_DIR = BASE_DIR / "Raw"

AUTHORS_PATH = RAW_DIR / "luiss_authors.jsonl"
WORKS_PATH = RAW_DIR / "luiss_works.jsonl"

PER_PAGE = 200   # recommended by the documentation
BATCH_SIZE = 50  # OpenAlex recommends batching lists of known IDs,
                 # 50 is the max allowed by the API
                 # (source: https://docs.openalex.org/api-guide-for-llms#id-2.-use-batch-id-lookups)

def batched(iterable, batch_size=BATCH_SIZE): # batching to reduce the amount of API requests
    iterator = iter(iterable)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            break
        yield batch

def fetch_all_last_known_authors(institution_id: str = LUISS_INSTITUTION_ID, path: Path = AUTHORS_PATH):
    authors_query = (
        Authors()
        .filter(**{"last_known_institutions.id": institution_id})
        .select(["id", "display_name"])
    )

    save_data(authors_query, path)

def fetch_authors_batch_works(batch):
    or_value = "|".join(batch)
    return (
        Works()
        .filter(**{"author.id": or_value})
        .select(["id", "display_name", "publication_year"])
    )

def fetch_luiss_works(path: Path = WORKS_PATH):
    luiss_author_ids = get_existing_ids(AUTHORS_PATH)
    existing_work_ids = get_existing_ids(path)

    luiss_author_ids = sorted(luiss_author_ids)

    for author_id_batch in batched(luiss_author_ids, BATCH_SIZE):
        authors_works_batch_query = fetch_authors_batch_works(author_id_batch)
        save_data(authors_works_batch_query, path, existing_work_ids)

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

# IMPORTANT: redundant as we are not writing entries line by line, but rather
# multiple lines at once

# now append_jsonl() method is only responsible for writing stuff into the file.
# file opening/closing is moved to save_data

#def append_jsonl(f: TextIO, data: Dict[str, Any]):
#    f.write(json.dumps(data, ensure_ascii=False) + "\n")

def save_data(query, out_path: Path, existing_ids: Set[str] = None):
    if existing_ids is None:
        existing_ids = get_existing_ids(out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("a", encoding="utf-8") as file:
        for page in query.paginate(per_page=PER_PAGE, n_max=None):
            lines = []

            for entry in page:
                entry_id = entry.get("id")
                if not entry_id or entry_id in existing_ids:
                    continue

                existing_ids.add(entry_id)
                lines.append(json.dumps(entry, ensure_ascii=False))

            if lines:
                file.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    fetch_all_last_known_authors()
    fetch_luiss_works()
    print("Done")