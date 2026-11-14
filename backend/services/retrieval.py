import math
import re
from collections import Counter


def terms(text):
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return re.findall(r"[a-z0-9]+", text.lower())


def lexical_rank(chunks, question):
    query = set(terms(question))
    counts = [Counter(terms(f"{c['source']} {c['symbol']} {c['text']}")) for c in chunks]
    frequencies = Counter(term for row in counts for term in query.intersection(row))
    scores = [
        sum(
            math.log1p(len(counts) / frequencies[term]) * count / (count + 1)
            for term in query.intersection(row)
            if (count := row[term])
        ) / math.sqrt(max(1, sum(row.values())))
        for row in counts
    ]
    return [i for i in sorted(range(len(scores)), key=lambda i: (-scores[i], i)) if scores[i] > 0]


def fuse_rankings(*rankings):
    scores = Counter()
    for ranking in rankings:
        for rank, index in enumerate(ranking, start=1):
            scores[index] += 1 / (60 + rank)
    return sorted(scores, key=lambda index: (-scores[index], index))
