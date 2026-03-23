"""Tests for Braille encoding."""

from borse.braille import (
    FILLED,
    GRADE2_GROUP_CONTRACTIONS,
    GRADE2_WORD_CONTRACTIONS,
    UNFILLED,
    _apply_grade2,
    _get_syllable_breaks,
    _spans_break,
    encode_char,
    encode_word,
    get_display_lines,
)


class TestEncodeChar:
    """Tests for encode_char function."""

    def test_encode_a(self) -> None:
        """Test encoding 'A' (dot 1 only)."""
        result = encode_char("A")
        assert len(result) == 3
        assert result[0] == f"{FILLED} {UNFILLED}"  # Row 1: dot 1 raised
        assert result[1] == f"{UNFILLED} {UNFILLED}"  # Row 2: none
        assert result[2] == f"{UNFILLED} {UNFILLED}"  # Row 3: none

    def test_encode_lowercase(self) -> None:
        """Test encoding lowercase letters."""
        assert encode_char("a") == encode_char("A")

    def test_encode_b(self) -> None:
        """Test encoding 'B' (dots 1, 2)."""
        result = encode_char("B")
        assert result[0] == f"{FILLED} {UNFILLED}"  # dot 1
        assert result[1] == f"{FILLED} {UNFILLED}"  # dot 2
        assert result[2] == f"{UNFILLED} {UNFILLED}"

    def test_encode_c(self) -> None:
        """Test encoding 'C' (dots 1, 4)."""
        result = encode_char("C")
        assert result[0] == f"{FILLED} {FILLED}"  # dots 1 and 4
        assert result[1] == f"{UNFILLED} {UNFILLED}"
        assert result[2] == f"{UNFILLED} {UNFILLED}"

    def test_encode_invalid(self) -> None:
        """Test encoding invalid characters."""
        result = encode_char("!")
        assert result == ["   ", "   ", "   "]

    def test_encode_all_dots(self) -> None:
        """Test that letters with all 6 dots work."""
        # No standard letter uses all 6 dots, but let's check a full letter
        # Q uses dots 1,2,3,4,5
        result = encode_char("Q")
        assert result[0] == f"{FILLED} {FILLED}"  # dots 1,4
        assert result[1] == f"{FILLED} {FILLED}"  # dots 2,5
        assert result[2] == f"{FILLED} {UNFILLED}"  # dot 3


class TestEncodeWord:
    """Tests for encode_word function."""

    def test_encode_hi(self) -> None:
        """Test encoding 'HI'."""
        result = encode_word("HI")
        assert len(result) == 2  # Two characters
        assert all(len(char) == 3 for char in result)  # Each has 3 rows

    def test_encode_empty(self) -> None:
        """Test encoding empty string."""
        assert encode_word("") == []


class TestGetDisplayLines:
    """Tests for get_display_lines function."""

    def test_returns_five_lines(self) -> None:
        """Test that Braille returns 5 lines (3 rows + 2 blank for spacing)."""
        lines = get_display_lines("ABC")
        assert len(lines) == 5
        # Blank lines are at indices 1 and 3
        assert lines[1] == ""
        assert lines[3] == ""

    def test_lines_separated_by_spaces(self) -> None:
        """Test that characters are separated by spaces."""
        lines = get_display_lines("AB")
        # Check non-blank lines (indices 0, 2, 4)
        for i in [0, 2, 4]:
            assert "   " in lines[i]  # Three spaces between characters

    def test_empty_word(self) -> None:
        """Test empty word returns empty lines."""
        lines = get_display_lines("")
        assert lines == ["", "", "", "", ""]


class TestSyllableBreaks:
    """Tests for the syllabification helper used by Grade 2 contraction logic."""

    def test_freedom_break_before_d(self) -> None:
        # "freedom" = free|dom; break before 'd' at index 4
        breaks = _get_syllable_breaks("freedom")
        assert 4 in breaks

    def test_shanghai_break_before_h(self) -> None:
        # "Shanghai" = Shang|hai; break before 'h' at index 5
        breaks = _get_syllable_breaks("shanghai")
        assert 5 in breaks

    def test_other_break_before_t(self) -> None:
        # "other" = o|ther; break before 't' at index 1
        breaks = _get_syllable_breaks("other")
        assert 1 in breaks

    def test_shower_no_internal_ow_break(self) -> None:
        # "shower" = show|er; the 'ow' diphthong must NOT be split
        breaks = _get_syllable_breaks("shower")
        # No break between 'o'(2) and 'w'(3): break should not be at 3
        assert 3 not in breaks

    def test_spans_break_basic(self) -> None:
        assert _spans_break(3, 5, frozenset({4})) is True
        assert _spans_break(1, 3, frozenset({1})) is False  # break at boundary, not inside
        assert _spans_break(4, 6, frozenset({4})) is False


class TestGrade2Contractions:
    """Tests for Grade 2 contraction application."""

    def test_dot_patterns_th(self) -> None:
        assert GRADE2_GROUP_CONTRACTIONS["TH"] == (1, 4, 5, 6)

    def test_dot_patterns_ch(self) -> None:
        assert GRADE2_GROUP_CONTRACTIONS["CH"] == (1, 6)

    def test_dot_patterns_sh(self) -> None:
        assert GRADE2_GROUP_CONTRACTIONS["SH"] == (1, 4, 6)

    def test_dot_patterns_er(self) -> None:
        assert GRADE2_GROUP_CONTRACTIONS["ER"] == (1, 2, 4, 5, 6)

    def test_dot_patterns_ing(self) -> None:
        assert GRADE2_GROUP_CONTRACTIONS["ING"] == (3, 4, 6)

    def test_dot_patterns_the_word(self) -> None:
        assert GRADE2_WORD_CONTRACTIONS["THE"] == (2, 3, 4, 6)

    def test_freedom_ed_not_contracted(self) -> None:
        # The -ed- in "freedom" (free|dom) spans a syllable break → no contraction
        segments = _apply_grade2("freedom")
        labels = [lbl for lbl, _ in segments]
        assert "ED" not in labels

    def test_shanghai_gh_not_contracted(self) -> None:
        # The -gh- in "Shanghai" (Shang|hai) spans a syllable break → no contraction
        segments = _apply_grade2("shanghai")
        labels = [lbl for lbl, _ in segments]
        assert "GH" not in labels

    def test_other_the_contracted(self) -> None:
        # "other" = o·[the]·r — THE (3-char) wins over TH (2-char) greedily
        segments = _apply_grade2("other")
        labels = [lbl for lbl, _ in segments]
        assert "THE" in labels

    def test_together_the_contracted(self) -> None:
        # "together" = t·o·g·e·[the]·r — THE wins greedily at position 4
        segments = _apply_grade2("together")
        labels = [lbl for lbl, _ in segments]
        assert "THE" in labels

    def test_shower_sh_ow_er_contracted(self) -> None:
        # "shower" = show|er; 'sh', 'ow', 'er' all valid
        segments = _apply_grade2("shower")
        labels = [lbl for lbl, _ in segments]
        assert "SH" in labels
        assert "OW" in labels
        assert "ER" in labels

    def test_whole_word_the(self) -> None:
        segments = _apply_grade2("the")
        assert len(segments) == 1
        assert segments[0] == ("THE", GRADE2_WORD_CONTRACTIONS["THE"])

    def test_whole_word_and(self) -> None:
        segments = _apply_grade2("and")
        assert len(segments) == 1
        assert segments[0] == ("AND", GRADE2_WORD_CONTRACTIONS["AND"])

    def test_dot_patterns_st(self) -> None:
        assert GRADE2_GROUP_CONTRACTIONS["ST"] == (3, 4)

    def test_word_contraction_in_substring_then(self) -> None:
        # [the]n — THE applies within "then"
        segments = _apply_grade2("then")
        labels = [lbl for lbl, _ in segments]
        assert "THE" in labels

    def test_word_contraction_in_substring_hand(self) -> None:
        # h[and] — AND applies within "hand"
        segments = _apply_grade2("hand")
        labels = [lbl for lbl, _ in segments]
        assert "AND" in labels

    def test_word_contraction_in_substring_roof(self) -> None:
        # ro[of] — OF applies within "roof"
        segments = _apply_grade2("roof")
        labels = [lbl for lbl, _ in segments]
        assert "OF" in labels

    def test_word_contraction_in_substring_forest(self) -> None:
        # [for]e[st] — FOR and ST both apply
        segments = _apply_grade2("forest")
        labels = [lbl for lbl, _ in segments]
        assert "FOR" in labels
        assert "ST" in labels


class TestGrade2DisplayLines:
    """Tests for get_display_lines with grade=2."""

    def test_returns_six_lines_for_word(self) -> None:
        lines = get_display_lines("other", grade=2)
        assert len(lines) == 6

    def test_grade1_still_five_lines(self) -> None:
        lines = get_display_lines("other", grade=1)
        assert len(lines) == 5

    def test_single_letter_no_annotation(self) -> None:
        # Single letters have no contraction, so annotation is empty
        lines = get_display_lines("b", grade=2)
        assert len(lines) == 6
        assert lines[5] == ""

    def test_annotation_shows_contractions(self) -> None:
        lines = get_display_lines("other", grade=2)
        # Annotation line should mention the TH contraction
        assert "TH" in lines[5]

    def test_annotation_empty_when_no_contractions(self) -> None:
        # A word with no applicable contractions gets an empty annotation
        lines = get_display_lines("big", grade=2)
        assert lines[5] == ""

    def test_fewer_cells_when_contracted(self) -> None:
        # "other" has 5 letters but "th" + "er" reduces cells
        lines_g1 = get_display_lines("other", grade=1)
        lines_g2 = get_display_lines("other", grade=2)
        # Grade 1: 5-letter cells separated by spaces → wider first row
        # Grade 2: 3 cells (o, th, er) → narrower first row
        assert len(lines_g2[0]) < len(lines_g1[0])
