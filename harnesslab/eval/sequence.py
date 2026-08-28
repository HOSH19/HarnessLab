"""Shared subsequence scoring helpers for evaluators."""


def subsequence_progress(expected: list[str], actual: list[str]) -> float:
    """Return fraction of expected items matched in order (1.0 when complete)."""
    if not expected:
        return 1.0

    index = 0
    for item in actual:
        if item == expected[index]:
            index += 1
            if index == len(expected):
                return 1.0
    return index / len(expected)


def is_subsequence(expected: list[str], actual: list[str]) -> bool:
    """Return True when expected items appear in order inside actual."""
    return subsequence_progress(expected, actual) == 1.0
