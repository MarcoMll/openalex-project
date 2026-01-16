from __future__ import annotations

import json
import time
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Set

from pyalex import Authors, config

LUISS_INSTITUTION_ID = "I56441308"
config.email = "marcomalliani@gmail.com"

BASE_DIR = Path("Data")
RAW_DIR = BASE_DIR / "Raw"
AUTHORS_PATH = RAW_DIR / "luiss_authors.jsonl"

PER_PAGE = 200

def find_all_last_known_authors(institution_id: str):
    query = (
        Authors()
        .filter(**{"last_known_institutions.id": institution_id})
        .select(["id", "display_name"])
    )
    return list(chain.from_iterable(query.paginate(per_page=200, n_max=None)))

def find_all_associated_works(author_id: str):
    query = (
        Works()
        .filter(**{"author.id": author_id})
        .select(["id", "display_name", "authorships"])
    )
    return list(chain.from_iterable(query.paginate(per_page=200, n_max=None)))

# TO REMEMBER: lists are fine for now but later we will have to
# implement JSONL saving as lists are expensive

luiss_authors = find_all_last_known_authors(LUISS_INSTITUTION_ID)
print(f"Found {len(luiss_authors)} authors \n")

if not luiss_authors:
    raise ValueError("No authors found")

author = random.choice(luiss_authors)
works = find_all_associated_works(author["id"])

print(f"Randomly selected author: {author['display_name']} ({author['id']})")
print(f"Author's works number: {len(works)} \n")

if not works:
    raise ValueError("No works found for selected author")

work = random.choice(works)
authorships = work.get("authorships", [])

# Extract coauthors excluding the chosen author
coauthor_names = [
    a["author"]["display_name"]
    for a in authorships
    if a.get("author") and a["author"].get("id") and a["author"]["id"] != author["id"]
]

print(f"Coauthors on selected work: {len(coauthor_names)}")

if coauthor_names:
    print("---------Co-authors---------")
    print("\n".join(coauthor_names))
else:
    print("No coauthors.")