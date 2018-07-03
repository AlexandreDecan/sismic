from collections import defaultdict


def sorted_groupby(iterable, key=None, reverse=False):
    """
    Return pairs (label, group) grouped and sorted by label = key(item).
    """
    groups = defaultdict(list)
    for value in iterable:
        groups[key(value)].append(value)
    sort_key = lambda e: e[0]
    return sorted(groups.items(), key=sort_key, reverse=reverse)