from __future__ import annotations

import json

from pathlib import Path
from typing import Callable, Set
from itertools import islice

from pyalex import Authors, config, Works
from utils.project_paths import get_paths # now acts as a single source of truth for paths

LUISS_INSTITUTION_ID = "i56441308"

# all files-navigation logic moved to project_paths.py
P = get_paths()
RAW_DIR = P.RAW_DIR

AUTHORS_PATH = P.RAW_AUTHORS
WORKS_PATH = P.RAW_WORKS

PER_PAGE = 200    # recommended by the documentation
BATCH_SIZE = 100  # OpenAlex recommends batching lists of known IDs,
                  # 100 is the max allowed by the API
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

    base_query = (
        Works()
        .filter(**{"authorships.author.id": or_value})
        .select(["id", "publication_year", "authorships", "topics", "keywords"])
    )

    def compact_work(entry):
        return {
            "id": entry.get("id"),
            "publication_year": entry.get("publication_year"),
            "authorships": [
                {
                    "author": {
                        "id": (a.get("author") or {}).get("id"),
                        "display_name": (a.get("author") or {}).get("display_name"),
                    }
                }
                for a in entry.get("authorships", [])
                if (a.get("author") or {}).get("id")
            ],
            "topics": [
                {
                    "id": t.get("id"),
                    "display_name": t.get("display_name"),
                    "domain": {
                        "display_name": (t.get("domain") or {}).get("display_name")
                    },
                }
                for t in entry.get("topics", [])
                if t.get("id")
            ],
            "keywords": [
                {"display_name": k.get("display_name")}
                for k in entry.get("keywords", [])
                if k.get("display_name")
            ],
        }

    class _CompactQuery:
        def paginate(self, per_page=200, n_max=None):
            for page in base_query.paginate(per_page=per_page, n_max=n_max):
                yield [compact_work(entry) for entry in page]

    return _CompactQuery()

def fetch_institution_works(path: Path = WORKS_PATH):
    author_ids = get_existing_ids(AUTHORS_PATH)
    existing_work_ids = get_existing_ids(path)

    author_ids = sorted(author_ids)

    for author_id_batch in batched(author_ids, BATCH_SIZE):
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

def reset_raw_data_cache(paths: tuple[Path, ...] = (AUTHORS_PATH, WORKS_PATH)) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

def fetch_raw_data_from_api(
    pipeline_config,
    on_status: Callable[[str], None] | None = None,
    reset_raw_data: bool = True,
):
    if pipeline_config.api_email:
        config.email = pipeline_config.api_email
    if pipeline_config.api_key:
        config.api_key = pipeline_config.api_key

    institution_id = (pipeline_config.institution_id or "").strip() or LUISS_INSTITUTION_ID
    if reset_raw_data:
        reset_raw_data_cache()

    if on_status is not None:
        on_status("Fetching authors")
    fetch_all_last_known_authors(institution_id=institution_id)

    if on_status is not None:
        on_status("Fetching works")
    fetch_institution_works()
    print("Fetching done.")

#if __name__ == "__main__":
