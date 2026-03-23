"""Braille encoding module with ASCII art display."""

# Braille patterns for letters a-z
# Dots are numbered:
# 1 4
# 2 5
# 3 6
# We store which dots are raised for each letter
BRAILLE_PATTERNS: dict[str, tuple[int, ...]] = {
    "A": (1,),
    "B": (1, 2),
    "C": (1, 4),
    "D": (1, 4, 5),
    "E": (1, 5),
    "F": (1, 2, 4),
    "G": (1, 2, 4, 5),
    "H": (1, 2, 5),
    "I": (2, 4),
    "J": (2, 4, 5),
    "K": (1, 3),
    "L": (1, 2, 3),
    "M": (1, 3, 4),
    "N": (1, 3, 4, 5),
    "O": (1, 3, 5),
    "P": (1, 2, 3, 4),
    "Q": (1, 2, 3, 4, 5),
    "R": (1, 2, 3, 5),
    "S": (2, 3, 4),
    "T": (2, 3, 4, 5),
    "U": (1, 3, 6),
    "V": (1, 2, 3, 6),
    "W": (2, 4, 5, 6),
    "X": (1, 3, 4, 6),
    "Y": (1, 3, 4, 5, 6),
    "Z": (1, 3, 5, 6),
}

# Grade 2: strong group-sign contractions (can appear anywhere within a word,
# subject to syllable-boundary rules)
GRADE2_GROUP_CONTRACTIONS: dict[str, tuple[int, ...]] = {
    "CH": (1, 6),
    "GH": (1, 2, 6),
    "SH": (1, 4, 6),
    "TH": (1, 4, 5, 6),
    "WH": (1, 5, 6),
    "ED": (1, 2, 4, 6),
    "ER": (1, 2, 4, 5, 6),
    "OU": (1, 2, 5, 6),
    "OW": (2, 4, 6),
    "AR": (3, 4, 5),
    "ST": (3, 4),
    "ING": (3, 4, 6),
}

# Grade 2: word-sign contractions.  These represent fixed meaningful units and
# may appear anywhere in a word (the, and, for, of, with) — e.g. [the]n,
# h[and], ro[of], [for]e[st] — without syllable-boundary checking.
GRADE2_WORD_CONTRACTIONS: dict[str, tuple[int, ...]] = {
    "AND": (1, 2, 3, 4, 6),
    "FOR": (1, 2, 3, 4, 5, 6),
    "OF": (1, 2, 3, 5, 6),
    "THE": (2, 3, 4, 6),
    "WITH": (2, 3, 4, 5, 6),
}

# Filled and unfilled circles for display
FILLED = "●"
UNFILLED = "○"

# ---------------------------------------------------------------------------
# Syllabification helpers (used by Grade 2 contraction logic)
# ---------------------------------------------------------------------------

_VOWELS = frozenset("aeiou")

# Valid English syllable onsets.  A consonant cluster is split so that the
# longest suffix that forms a valid onset goes to the second syllable
# (Maximum Onset Principle).  Note: "gh" is NOT a valid modern-English onset,
# which is why the -gh- in "Shanghai" (Shang|hai) stays blocked.
_VALID_ONSETS = frozenset(
    {
        # Single consonants
        "b", "c", "d", "f", "g", "h", "j", "k", "l", "m",
        "n", "p", "q", "r", "s", "t", "v", "w", "x", "y", "z",
        # Two-consonant clusters
        "bl", "br", "cl", "cr", "dr", "dw", "fl", "fr", "gl", "gr",
        "kl", "kn", "kw", "pl", "pr", "sc", "sk", "sl", "sm", "sn",
        "sp", "sq", "st", "sw", "tr", "tw",
        "ch", "ph", "sh", "th", "wh",
        # Three-consonant clusters
        "scr", "spl", "spr", "str", "squ", "thr",
    }
)


def _get_syllable_breaks(word: str) -> frozenset[int]:
    """Return the set of positions where syllable breaks occur.

    A value *b* in the returned set means there is a syllable boundary
    immediately **before** index *b* (i.e. letters at indices < b belong to
    an earlier syllable than letters at indices >= b).

    The algorithm uses the Maximum Onset Principle: given the consonant
    cluster between two vowels, assign the longest suffix that is a valid
    English onset to the second syllable; the rest stays as the coda of the
    first syllable.

    A leading 'w' or 'y' immediately after a vowel is treated as part of a
    diphthong (e.g. "ow" in "show", "ay" in "say") and is not considered a
    syllable-separating consonant for the purpose of this algorithm.
    """
    w = word.lower()
    vowels = [i for i, c in enumerate(w) if c in _VOWELS]
    breaks: set[int] = set()
    for k in range(len(vowels) - 1):
        v1, v2 = vowels[k], vowels[k + 1]
        cluster = w[v1 + 1 : v2]
        if not cluster:
            continue  # adjacent vowels — treat as diphthong, no break

        # A 'w' or 'y' immediately after a vowel is a diphthong glide; skip it
        # when looking for the consonant cluster that determines the split.
        glide_end = 0
        while glide_end < len(cluster) and cluster[glide_end] in "wy":
            glide_end += 1
        remaining = cluster[glide_end:]

        if not remaining:
            continue  # only glides between vowels — no break

        # Find the leftmost position in `remaining` whose suffix is a valid
        # onset (Maximum Onset Principle: maximise the onset of the 2nd syllable).
        for start in range(len(remaining) + 1):
            candidate = remaining[start:]
            if not candidate or candidate in _VALID_ONSETS:
                break_pos = v1 + 1 + glide_end + start
                if break_pos < v2:
                    breaks.add(break_pos)
                break

    return frozenset(breaks)


def _spans_break(start: int, end: int, breaks: frozenset[int]) -> bool:
    """Return True if the half-open range (start, end) contains a syllable break.

    A break at *b* lies between letter at index b-1 and letter at index b.
    The contraction covers indices [start, end).  It *spans* a break when
    some break b satisfies  start < b < end  (strictly inside the range).
    """
    return any(start < b < end for b in breaks)


# ---------------------------------------------------------------------------
# Grade 2 contraction engine
# ---------------------------------------------------------------------------

# Pre-sorted list for _apply_grade2: (seq, dots, needs_syllable_break_check).
# Word contractions are tried without break-checking (they represent fixed
# meaningful units); group contractions require the break check.
# Sorted longest-first so longer sequences win greedily.
_SORTED_CONTRACTIONS: list[tuple[str, tuple[int, ...], bool]] = sorted(
    [(s, d, False) for s, d in GRADE2_WORD_CONTRACTIONS.items()]
    + [(s, d, True) for s, d in GRADE2_GROUP_CONTRACTIONS.items()],
    key=lambda x: -len(x[0]),
)


def _apply_grade2(word: str) -> list[tuple[str, tuple[int, ...]]]:
    """Decompose *word* into Grade 2 Braille cells.

    Returns a list of (label, dots) pairs where *label* is the original
    letters for that cell and *dots* is the dot pattern.

    Word contractions (AND, FOR, OF, THE, WITH) may appear anywhere in a word
    without syllable-boundary checking.  Group contractions (CH, GH, TH, ER,
    ST, …) are applied greedily left-to-right, longest first, but are rejected
    when the letters would span a syllable boundary.
    """
    w = word.upper()
    breaks = _get_syllable_breaks(word)
    result: list[tuple[str, tuple[int, ...]]] = []
    i = 0
    while i < len(w):
        matched = False
        for seq, dots, check_break in _SORTED_CONTRACTIONS:
            end = i + len(seq)
            if w[i:end] == seq and (not check_break or not _spans_break(i, end, breaks)):
                result.append((seq, dots))
                i = end
                matched = True
                break
        if not matched:
            char = w[i]
            if char in BRAILLE_PATTERNS:
                result.append((char, BRAILLE_PATTERNS[char]))
            i += 1
    return result


# ---------------------------------------------------------------------------
# Cell rendering
# ---------------------------------------------------------------------------


def _dots_to_cell(dots: tuple[int, ...]) -> list[str]:
    """Render a dot pattern as a 3-row ASCII-art Braille cell."""
    dot_set = set(dots)
    rows = []
    for left_dot, right_dot in [(1, 4), (2, 5), (3, 6)]:
        left = FILLED if left_dot in dot_set else UNFILLED
        right = FILLED if right_dot in dot_set else UNFILLED
        rows.append(f"{left} {right}")
    return rows


# ---------------------------------------------------------------------------
# Public API (Grade 1, unchanged interface)
# ---------------------------------------------------------------------------


def encode_char(char: str) -> list[str]:
    """Encode a single character to Braille ASCII art.

    Args:
        char: A single character to encode.

    Returns:
        A list of 3 strings representing the 3 rows of the Braille cell.
    """
    upper = char.upper()
    if upper not in BRAILLE_PATTERNS:
        return ["   ", "   ", "   "]
    return _dots_to_cell(BRAILLE_PATTERNS[upper])


def encode_word(word: str) -> list[list[str]]:
    """Encode a word to Braille ASCII art.

    Args:
        word: The word to encode.

    Returns:
        A list of character encodings, each being a list of 3 row strings.
    """
    return [encode_char(c) for c in word if c.upper() in BRAILLE_PATTERNS]


def get_display_lines(word: str, grade: int = 1) -> list[str]:
    """Get the display lines for a word in Braille.

    Args:
        word: The word to encode.
        grade: Braille grade (1 or 2).  Grade 2 applies contractions and
               appends an annotation line showing the contracted segments.

    Returns:
        For grade 1: 5 strings (3 rows with blank spacer lines).
        For grade 2: 6 strings (same 5 plus one annotation line).
    """
    if grade == 2:
        return _get_display_lines_grade2(word)

    # Grade 1 (original behaviour)
    chars = encode_word(word)
    if not chars:
        return ["", "", "", "", ""]

    lines = []
    for row in range(3):
        line = "   ".join(char[row] for char in chars)
        lines.append(line)
        if row < 2:
            lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Grade 2 display
# ---------------------------------------------------------------------------


def _get_display_lines_grade2(word: str) -> list[str]:
    """Build Grade 2 display lines for *word* (called by get_display_lines)."""
    segments = _apply_grade2(word)
    if not segments:
        return ["", "", "", "", "", ""]

    cells = [_dots_to_cell(dots) for _, dots in segments]
    lines: list[str] = []
    for row in range(3):
        lines.append("   ".join(cell[row] for cell in cells))
        if row < 2:
            lines.append("")

    # Annotation: show contracted segments separated by middle-dot
    seg_labels = [label for label, _ in segments]
    has_contraction = any(len(lbl) > 1 for lbl in seg_labels)
    lines.append("GR2: " + "\u00b7".join(seg_labels) if has_contraction else "")
    return lines
