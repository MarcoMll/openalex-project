from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Set, Dict, Any, List, Tuple
from itertools import combinations

from utils.project_paths import get_paths

P = get_paths()  # new centralised project paths

RAW_DIR = P.RAW_DIR
DERIVED_DIR = P.DERIVED_DIR

RAW_AUTHORS_PATH = P.RAW_AUTHORS
RAW_WORKS_PATH = P.RAW_WORKS

DERIVED_WORKS_PATH = P.DERIVED_WORKS
HYPEREDGES_PATH = P.HYPEREDGES
EDGES_CSV_PATH = P.EDGES_CSV

# reading a jsonl file line by line and turn each non-empty line into a dictionary, then
# we strip each line to avoid trailing newlines and skip over any blank lines.
def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def load_institution_author_ids(authors_path: Path = RAW_AUTHORS_PATH):
    ids: Set[str] = set()
    for author in read_jsonl(authors_path):
        author_id = author.get("id")
        if isinstance(author_id, str) and author_id:
            ids.add(author_id)
    return ids

# from raw works data we are going to keep only: work id, publication year, and authors
# in other words, we are getting rid of the big authorship objects and keeping only relevant info
def derive_raw_works(raw_works_path: Path = RAW_WORKS_PATH, derived_works_path: Path = DERIVED_WORKS_PATH):
    derived_works_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_works_path.open("r", encoding="utf-8") as fin, derived_works_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue

            work = json.loads(line)
            work_id = work.get("id")
            year = work.get("publication_year")
            authorships = work.get("authorships") or []

            author_ids_list = []
            for authorship in authorships:
                author = authorship.get("author") or {}
                aid = author.get("id")
                if isinstance(aid, str) and aid:
                    author_ids_list.append(aid)

            # dedupe preserving order
            seen = set()
            author_ids_list = [x for x in author_ids_list if not (x in seen or seen.add(x))]

            if not isinstance(work_id, str) or not work_id:
                continue

            out_obj = {
                "work_id": work_id,
                "authors": author_ids_list,
                "publication_year": year,
            }
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")

def derive_hyperedges(hyperedges_path: Path = HYPEREDGES_PATH, derived_data_path: Path = DERIVED_WORKS_PATH, institution_author_ids: Set[str] = None):
    if institution_author_ids is None:
        institution_author_ids = load_institution_author_ids()

    hyperedges_path.parent.mkdir(parents=True, exist_ok=True) # ensure output directory exists

    with derived_data_path.open("r", encoding="utf-8") as derived_works_jsonl, \
        hyperedges_path.open("w", encoding="utf-8") as hyperedges_jsonl:

        for line in derived_works_jsonl:
            line = line.strip()
            if not line:
                continue

            work: Dict[str, Any] = json.loads(line) # parse one work record

            work_id = work.get("work_id")
            author_ids = work.get("authors")
            publication_year = work.get("publication_year")

            if not isinstance(work_id, str) or not work_id: # basic validation
                continue
            if not isinstance(author_ids, list):
                continue

            # keepin only luiss authors on this work
            institution_authors_on_work: List[str] = []
            for author_id in author_ids:
                if isinstance(author_id, str) and author_id in institution_author_ids:
                    institution_authors_on_work.append(author_id)

            # removing duplicated while preserving order
            seen = set()
            unique_institution_authors_on_work: List[str] = []
            for author_id in institution_authors_on_work:
                if author_id not in seen:
                    seen.add(author_id)
                    unique_institution_authors_on_work.append(author_id)

            if len(unique_institution_authors_on_work) < 2: # if less than two luiss authors on work
                continue                                    # we skip it

            unique_institution_authors_on_work.sort()

            # building the hyperedge record we will write
            hyperedge_record = {
                "work_id": work_id,
                "institution_author_ids": unique_institution_authors_on_work,
                "institution_author_count": len(unique_institution_authors_on_work),
                "publication_year": publication_year,
            }

            hyperedges_jsonl.write(json.dumps(hyperedge_record, ensure_ascii=False) + "\n")

    print("derive_hyperedges")

def convert_hyperedges_to_pairwise_edges_csv(hyperedges_path: Path = HYPEREDGES_PATH, edges_csv_out_path: Path = EDGES_CSV_PATH):
    pair_weights: Dict[Tuple[str, str], int] = {} # creating a dictionary stores counts for each author pair, where:
                                                  # the key is a tuple with author ids pair: id_1, id_2
                                                  # the value is a number of shared works

    # read hyperedges line-by-line
    with hyperedges_path.open("r", encoding="utf-8") as input_file:
        for line in input_file:
            line = line.strip()
            if not line:
                continue

            hyperedge: Dict[str, Any] = json.loads(line)

            author_ids = hyperedge.get("institution_author_ids")
            if not isinstance(author_ids, list):
                continue

            cleaned_author_ids: List[str] = []
            seen = set()
            for author_id in author_ids:
                if isinstance(author_id, str) and author_id and author_id not in seen:
                    seen.add(author_id)
                    cleaned_author_ids.append(author_id)

            if len(cleaned_author_ids) < 2: # if fewer than 2 authors, there are no pairs to create
                continue

            # Sort for stable pair generation
            cleaned_author_ids.sort()

            # generate all pairs from this hyperedge and increment weights
            for id_1, id_2 in combinations(cleaned_author_ids, 2):
                key = (id_1, id_2)
                current = pair_weights.get(key, 0)
                pair_weights[key] = current + 1

    # checking whether the output directory exists
    edges_csv_out_path.parent.mkdir(parents=True, exist_ok=True)

    with edges_csv_out_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["author_id_1", "author_id_2", "weight"])

        for (id_1, id_2), weight in sorted(pair_weights.items()):
            writer.writerow([id_1, id_2, weight])

if __name__ == "__main__":
    derive_raw_works()
    derive_hyperedges(institution_author_ids=load_institution_author_ids())
    convert_hyperedges_to_pairwise_edges_csv()
    print(f"Derived: ", DERIVED_WORKS_PATH)