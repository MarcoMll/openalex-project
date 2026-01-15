# scripts/fetch_luiss_collabs.py

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Set

from pyalex import config, Institutions, Authors, Works

LUISS_INSTITUTION_ID = "i56441308"
BASE_DIR = Path("Data")
RAW_DIR = BASE_DIR / "Raw"
DERIVED_DIR = BASE_DIR / "Derived"
AUTHORS_PATH = RAW_DIR / "luiss_authors.jsonl"

config.email = "marcomalliani@gmail.com"

institution_obj = Institutions().search("LUISS").get(per_page=3)[0] # looking up Luiss university
#print(institution_obj["authors_count"])
#print(sorted(institution_obj.keys()))

luiss_associated_authors = (
    Authors()
    .filter(**{"last_known_institutions.id": LUISS_INSTITUTION_ID})
    .select(["id", "display_name", "last_known_institutions"])
    .get(per_page=5)
)

def get_author_works(author_id):
    works = (
        Works()
        .filter(**{"author.id": author_id})
        .select(["id", "display_name", "publication_year", "authorships"])
        .get(per_page=3)
    )
    return works

test_author = luiss_associated_authors[0]

author_works = get_author_works(test_author["id"])
test_work = author_works[0]

print(f"Found {len(luiss_associated_authors)} authors")
print(f"Currently fetching author with id: {test_author["id"]}")
print("----------------------")
print("\nWork title:", test_work.get("display_name"))
print("Work id:", test_work.get("id"))
print("Year:", test_work.get("publication_year"))