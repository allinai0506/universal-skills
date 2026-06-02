#!/usr/bin/env python3
"""
Minimal BM25 search engine for LLM-compiled wikis.
Usage: python3 tools/search.py --query "search terms" --wiki-path <path>
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from glob import glob


def tokenize(text):
    return re.findall(r'\w+', text.lower())


def load_documents(wiki_path):
    docs = []
    for fpath in sorted(glob(os.path.join(wiki_path, '**/*.md'), recursive=True)):
        relpath = os.path.relpath(fpath, wiki_path)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        docs.append({
            'path': relpath,
            'content': content,
            'tokens': tokenize(content),
        })
    return docs


def compute_idf(docs):
    n = len(docs)
    df = Counter()
    for doc in docs:
        unique_terms = set(doc['tokens'])
        for term in unique_terms:
            df[term] += 1
    return {term: math.log((n - freq + 0.5) / (freq + 0.5) + 1) for term, freq in df.items()}


def bm25_score(query_tokens, doc_tokens, idf, avg_len, k1=1.5, b=0.75):
    doc_len = len(doc_tokens)
    tf = Counter(doc_tokens)
    score = 0.0
    for term in query_tokens:
        if term not in idf:
            continue
        freq = tf.get(term, 0)
        score += idf[term] * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * doc_len / avg_len))
    return score


def search(wiki_path, query, top_k=10):
    docs = load_documents(wiki_path)
    if not docs:
        print("No markdown files found in", wiki_path)
        return
    avg_len = sum(len(d['tokens']) for d in docs) / len(docs)
    idf = compute_idf(docs)
    query_tokens = tokenize(query)
    results = []
    for doc in docs:
        score = bm25_score(query_tokens, doc['tokens'], idf, avg_len)
        if score > 0:
            results.append((score, doc))
    results.sort(key=lambda x: -x[0])
    print(f'Search results for: {query}')
    print(f'{"Score":>8}  {"Path":<60}  {"Snippet"}')
    print('-' * 100)
    for score, doc in results[:top_k]:
        snippet = doc['content'][:120].replace('\n', ' ')
        print(f'{score:>8.2f}  {doc["path"]:<60}  {snippet}')


def main():
    parser = argparse.ArgumentParser(description='Search an LLM-compiled wiki')
    parser.add_argument('--query', '-q', required=True, help='Search query')
    parser.add_argument('--wiki-path', '-w', default='wiki/', help='Path to wiki directory')
    parser.add_argument('--top-k', '-k', type=int, default=10, help='Number of results')
    args = parser.parse_args()
    search(args.wiki_path, args.query, args.top_k)


if __name__ == '__main__':
    main()
