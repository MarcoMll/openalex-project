import json
import csv
#dict subclass that calls a factory function to supply missing value
from collections import defaultdict
# generate all possible combinations of a specified length from a given iterable
from itertools import combinations
import os

#Configurations/Paths
#Input file paths
#Will add the path name once in the project
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed") #Will need to be changed once the data has been processed location wise
#The Following Might need to be changed based on the final data file names
LUISS_AUTHORS_FILE = os.path.join(DATA_DIR, "luiss_authors.csv") #Loading the set of LUISS author IDs
WORKS_FILE = os.path.join(DATA_DIR, "works_min.json") #Loading the works data file 

#Output file paths
#New JSON Lines file where each line is one hyperedge
HYPEREDGES_FILE = os.path.join(DATA_DIR, "hyperedges.jsonl") #Output file for hyperedges
#This is a CSV with columns author1, author2, weight
PAIRWISE_EDGES_FILE = os.path.join(DATA_DIR, "pairwise_edges.csv") #Output file for pairwise edges

