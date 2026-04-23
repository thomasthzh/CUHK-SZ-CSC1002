"""Black-box regression tests for CSC1002 A3 console editor.

Usage:
    python test.py
    python test.py /path/to/A3_SSE_125091035.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


HELP_TEXT = """? - display this help info
. - toggle row cursor on and off
h - move cursor left
l - move cursor right
^ - move cursor to beginning of the line
$ - move cursor to end of the line
w - move cursor to beginning of next word
b - move cursor to beginning of current or previous word
e - move cursor to end of the word
i - insert <text> before cursor
a - append <text> after cursor
I - insert <text> from beginning
A - append <text> at the end
x - delete character at cursor
X - delete character before cursor
dw - delete to start of next word
de - delete to end of next word
db - delete to start of current or previous word
dc - delete whitespaces or entire word at cursor
sw - swap word at cursor with next word
sb - swap word at cursor with previous word
; - toggle line cursor on and off
j - move cursor up
k - move cursor down
o - insert empty line below
O - insert empty line above
dd - delete line
J - move line up
K - move line down
Line_No. - jump to specific line, first character
v - view editor content
q - quit program"""


def resolve_target() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    return Path(__file__).with_name("A3_SSE_125091035.py").resolve()


def run_session(target: Path, commands: list[str]) -> str:
    session_commands = list(commands)
    if not session_commands or session_commands[-1] != "q":
        session_commands.append("q")
    payload = "\n".join(session_commands) + "\n"
    result = subprocess.run(
        [sys.executable, str(target)],
        input=payload.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Program exited with code {result.returncode}\n"
            f"stderr:\n{result.stderr.decode('utf-8', errors='replace')}"
        )
    text = result.stdout.decode("utf-8", errors="replace")
    return normalize_line_endings(text)


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def prompt_positions(output: str) -> list[int]:
    points = []
    for idx, char in enumerate(output):
        if char != ">":
            continue
        if idx == 0 or output[idx - 1] in "\n>":
            points.append(idx)
    return points


def split_segments(output: str, command_count: int) -> list[str]:
    points = prompt_positions(output)
    if len(points) < command_count:
        raise AssertionError(
            f"Expected at least {command_count} prompts, found {len(points)}\n"
            f"Raw output:\n{output!r}"
        )
    segments = []
    for idx in range(command_count):
        start = points[idx] + 1
        end = points[idx + 1] if idx + 1 < len(points) else len(output)
        segments.append(output[start:end])
    return segments


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def normalize_segment(text: str) -> str:
    return strip_ansi(normalize_line_endings(text))


def assert_equal(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name} failed\nactual: {actual!r}\nexpected: {expected!r}")


def first_diff_index(actual, expected):
    limit = min(len(actual), len(expected))
    for idx in range(limit):
        if actual[idx] != expected[idx]:
            return idx
    return None if len(actual) == len(expected) else limit


def build_case_failure(name: str, commands: list[str], actual: list[str], expected: list[str]) -> str:
    idx = first_diff_index(actual, expected)
    if idx is None:
        return f"{name} failed (unknown diff)"
    command = commands[idx] if idx < len(commands) else "<NO_COMMAND>"
    actual_seg = actual[idx] if idx < len(actual) else "<NO_SEGMENT>"
    expected_seg = expected[idx] if idx < len(expected) else "<NO_SEGMENT>"
    return (
        f"{name} failed at step {idx + 1}\n"
        f"command: {command!r}\n"
        f"actual_segment: {actual_seg!r}\n"
        f"expected_segment: {expected_seg!r}"
    )


def run_case(target: Path, name: str, commands: list[str], expected: list[str]) -> None:
    if len(commands) != len(expected):
        raise AssertionError(
            f"{name} invalid case shape\n"
            f"commands={len(commands)}, expected={len(expected)}"
        )
    output = run_session(target, commands)
    actual = split_segments(output, len(commands))
    actual = [normalize_segment(item) for item in actual]
    expected = [normalize_segment(item) for item in expected]
    if actual != expected:
        raise AssertionError(build_case_failure(name, commands, actual, expected))
    print(f"[PASS] {name}")


def test_invalid_input_prompt_only(target: Path) -> None:
    commands = ["   $", "?  ", "i", "a", "hx", "q"]
    expected = ["", "", "", "", "", ""]
    run_case(target, "invalid-input-prompt-only", commands, expected)


def test_help_output(target: Path) -> None:
    commands = ["?", "q"]
    expected = [HELP_TEXT + "\n", ""]
    run_case(target, "help-output", commands, expected)


def test_insert_and_append(target: Path) -> None:
    commands = [".", "iabc", "aw", "I_", "A_", "v", "q"]
    expected = ["\n", "abc\n", "awbc\n", "_awbc\n", "_awbc_\n", "_awbc_\n", ""]
    run_case(target, "insert-append", commands, expected)


def test_word_motion_and_delete(target: Path) -> None:
    commands = [".", "iab  cd ef", "w", "e", "b", "dw", "de", "db", "v", "q"]
    expected = [
        "\n",
        "ab  cd ef\n",
        "ab  cd ef\n",
        "ab  cd ef\n",
        "ab  cd ef\n",
        "ab  ef\n",
        "ab  \n",
        "\n",
        "\n",
        "",
    ]
    run_case(target, "word-motion-delete", commands, expected)


def test_b_repeat_from_word_start(target: Path) -> None:
    commands = [".", "i one two  ", "$", "b", "x", "v", "b", "x", "v", "q"]
    expected = [
        "\n",
        " one two  \n",
        " one two  \n",
        " one two  \n",
        " one wo  \n",
        " one wo  \n",
        " one wo  \n",
        " ne wo  \n",
        " ne wo  \n",
        "",
    ]
    run_case(target, "b-repeat-from-word-start", commands, expected)


def test_multiline_and_line_movement(target: Path) -> None:
    commands = [".", "iL1", "o", "iL2", "o", "iL3", "j", "1", "99", "J", "K", "dd", "v", "q"]
    expected = [
        "\n",
        "L1\n",
        "L1\n\n",
        "L1\nL2\n",
        "L1\nL2\n\n",
        "L1\nL2\nL3\n",
        "L1\nL2\nL3\n",
        "L1\nL2\nL3\n",
        "L1\nL2\nL3\n",
        "L1\nL3\nL2\n",
        "L1\nL2\nL3\n",
        "L1\nL2\n",
        "L1\nL2\n",
        "",
    ]
    run_case(target, "multiline-line-movement", commands, expected)


def test_line_cursor_render(target: Path) -> None:
    commands = [".", "iA", "o", "iB", ";", "v", "q"]
    expected = ["\n", "A\n", "A\n\n", "A\nB\n", " A\n*B\n", " A\n*B\n", ""]
    run_case(target, "line-cursor-render", commands, expected)


def ZZY_TP1(target: Path) -> None:
    commands = ["i12345", "o", "12345", ";", "O", "i12321", "i21312", "i3123", "i213213", "o", "i213123", ";", ";", "j", "l", "l", "l", "l", "l", "l", "l", "l", "l", "x", "3", "x", "1", "x", "q"]
    expected = [
        "12345\n", "12345\n\n", "12345\n\n", " 12345\n*\n", " 12345\n*\n \n",
        " 12345\n*12321\n \n", " 12345\n*2131212321\n \n", " 12345\n*31232131212321\n \n",
        " 12345\n*21321331232131212321\n \n", " 12345\n 21321331232131212321\n*\n \n",
        " 12345\n 21321331232131212321\n*213123\n \n", "12345\n21321331232131212321\n213123\n\n",
        " 12345\n 21321331232131212321\n*213123\n \n", " 12345\n*21321331232131212321\n 213123\n \n",
        " 12345\n*21321331232131212321\n 213123\n \n", " 12345\n*21321331232131212321\n 213123\n \n",
        " 12345\n*21321331232131212321\n 213123\n \n", " 12345\n*21321331232131212321\n 213123\n \n",
        " 12345\n*21321331232131212321\n 213123\n \n", " 12345\n*21321331232131212321\n 213123\n \n",
        " 12345\n*21321331232131212321\n 213123\n \n", " 12345\n*21321331232131212321\n 213123\n \n",
        " 12345\n*21321331232131212321\n 213123\n \n", " 12345\n*2132133122131212321\n 213123\n \n",
        " 12345\n 2132133122131212321\n*213123\n \n", " 12345\n 2132133122131212321\n*13123\n \n",
        "*12345\n 2132133122131212321\n 13123\n \n", "*2345\n 2132133122131212321\n 13123\n \n", "",
    ]
    run_case(target, "ZZY_TP1", commands, expected)


SAMPLE_CASES = {
    13: (
        ["a  one  two three", "^", "de", "l", "l", "l", "l", "de", "de", "^", "de"],
        [
            "  one  two three\n", "  one  two three\n", "  two three\n", "  two three\n",
            "  two three\n", "  two three\n", "  two three\n", "  tw\n",
            "  t\n", "  t\n", "\n",
        ],
    ),
    14: (
        ["a one two three", "db", "h", "h", "db", "h", "db", "db", "db"],
        [" one two three\n", " one two \n", " one two \n", " one two \n", " one o \n", " one o \n", " o \n", " \n", "\n"],
    ),
    15: (
        ["a  one  two  three", "dc", "h", "h", "dc", "b", "dc", "b", "l", "dc", "dc"],
        ["  one  two  three\n", "  one  two  \n", "  one  two  \n", "  one  two  \n", "  one    \n", "  one    \n", "      \n", "      \n", "      \n", "\n", "\n"],
    ),
    16: (
        ["ione", "$", "x", "x", "x"],
        ["one\n", "one\n", "on\n", "o\n", "\n"],
    ),
    17: (
        ["athree", "X", "X", "X", "X", "X", "X"],
        ["three\n", "thre\n", "the\n", "te\n", "e\n", "e\n", "e\n"],
    ),
    18: (
        ["ione two three", "sw", "sw", "sw", "v", "w", "h", "sw"],
        ["one two three\n", "two one three\n", "two three one\n", "two three one\n", "two three one\n", "two three one\n", "two three one\n", "two three one\n"],
    ),
    19: (
        ["ione two three", "sw", "sw", "sb", "sb", "sb", "v", "w", "h", "sb"],
        ["one two three\n", "two one three\n", "two three one\n", "two one three\n", "one two three\n", "one two three\n", "one two three\n", "one two three\n", "one two three\n", "one two three\n"],
    ),
    20: (
        ["ihello", ";", "v", ";", "ione two three", "o"],
        ["hello\n", "*hello\n", "*hello\n", "hello\n", "one two threehello\n", "one two threehello\n\n"],
    ),
    21: (
        ["ihello world", "$", "j", ";", "O", "k", "j", "j"],
        ["hello world\n", "hello world\n", "hello world\n", "*hello world\n", "*\n hello world\n", " \n*hello world\n", "*\n hello world\n", "*\n hello world\n"],
    ),
    22: (
        ["ione two three", "o", "j", "O", "aone", "o", "aone two", "o"],
        ["one two three\n", "one two three\n\n", "one two three\n\n", "\none two three\n\n", "one\none two three\n\n", "one\n\none two three\n\n", "one\none two\none two three\n\n", "one\none two\n\none two three\n\n"],
    ),
    23: (
        [";", "ihello world", "o", "aone two three", "dd", "dd", "dd", ";", "ione two three", "O", "ihello world", "dd"],
        ["*\n", "*hello world\n", " hello world\n*\n", " hello world\n*one two three\n", "*hello world\n", "*\n", "*\n", "\n", "one two three\n", "\none two three\n", "hello world\none two three\n", "one two three\n"],
    ),
    24: (
        ["v", "99", "1", "v", "2", "3", "4"],
        ["\n", "\n", "\n", "\n", "\n", "\n", "\n"],
    ),
    25: (
        ["ione", "O", "J", "K", "K", "v", "K", "K", "K", "v", "J", "J", "J"],
        ["one\n", "\none\n", "\none\n", "one\n\n", "one\n\n", "one\n\n", "one\n\n", "one\n\n", "one\n\n", "one\n\n", "\none\n", "\none\n", "\none\n"],
    ),
}

    
A2HW_CASES = {
    'a00': (
        ['?', '.', '.', ';', ';', 'a', 'i', 'A', 'I', '^', '$', 'h', 'j', 'k', 'l', 'w', 'b', 'e', 'dw', 'de', 'db', 'dc', 'ds', 'yw', 'ye', 'yb', 'yc', 'ys', 'sw', 'sb', 'cr', 'cl', 'p', 'P', 's', 'm', 'J', 'K', 'p', 'P', 'hello from kinley', 'o ', 'O ', 'yy ', 's ', 'm ', '666 ', 'v', '.', 'ipassed', 'q'],
        'passed',
    ),
    'a01': (
        ['ia b c', 'w', 'w', 'w', 'w', 'x', 'x', '.', 'q'],
        'a b',
    ),
    'a02': (
        ['ia b c', 'e', 'e', 'e', 'e', 'x', 'x', '.', 'q'],
        'a b',
    ),
    'a03': (
        ['ia ', 'w', 'x', '.', 'q'],
        'a',
    ),
    'a04': (
        ['i   a ', 'e', 'e', 'x', '.', 'q'],
        '   a',
    ),
    'b01': (
        ['i  %&^%one(*&())   %&^two!@#$   three', 'w', 'w', 'l', 'l', 'x', '.', 'q'],
        '  %&^%one(*&())   %&two!@#$   three',
    ),
    'b02': (
        ['i  %&^%one(*&())   %&^two!@#$   three', 'e', 'e', 'h', 'h', 'x', '.', 'q'],
        '  %&^%one(*&())   %&^two!#$   three',
    ),
    'b03': (
        ['a  %&^%one(*&())   %&^two!@#$   three', 'b', 'b', 'b', 'l', 'l', 'x', '.', 'q'],
        '  %&%one(*&())   %&^two!@#$   three',
    ),
    'db1': (
        ['Aone two three', 'db', '.', 'x', 'q'],
        'one two',
    ),
    'db2': (
        ['I     one two three', 'w', 'h', 'db', 'x', '.', 'q'],
        'ne two three',
    ),
    'db3': (
        ['Aone two three     ', 'db', 'x', '.', 'q'],
        'one two',
    ),
    'dc1': (
        ['ione two three', 'dc', 'w', 'dc', 'w', 'dc', 'Apassed', 'Ipassed', '.', 'q'],
        'passed  passed',
    ),
    'dc2': (
        ['i  one  two  three     ', 'dc', 'w', 'h', 'dc', 'w', 'h', 'dc', 'w', 'h', 'dc', '.', 'q'],
        'onetwothree',
    ),
    'dc3': (
        ['ione one one one', 'w', 'w', 'w', 'sb', 'dc', 'x', '.', 'q'],
        'one one one',
    ),
    'dc4': (
        ['ia   b', 'l', 'dc', '.', 'q'],
        'ab',
    ),
    'dc5': (
        ['aa    ', 'dc', '.', 'q'],
        'a',
    ),
    'de1': (
        ['ione two three', 'de', '.', 'ipassed', 'q'],
        'passed two three',
    ),
    'de2': (
        ['i   one two three', 'de', '.', 'ipassed', 'q'],
        'passed two three',
    ),
    'de3': (
        ['Aone two three    ', 'b', 'e', 'de', '.', 'q'],
        'one two thre',
    ),
    'dw1': (
        ['ione two three', 'dw', '.', 'x', 'q'],
        'wo three',
    ),
    'dw2': (
        ['i  one two three', 'dw', '.', 'q'],
        'one two three',
    ),
    'dw3': (
        ['aone two three    ', 'b', 'dw', '.', 'apassed', 'q'],
        'one two passed',
    ),
    'sb1': (
        ['ione two three', 'w', 'sb', '.', 'q'],
        'two one three',
    ),
    'sb2': (
        ['ione  two   three', 'w', 'w', 'sb', 'sb', '.', 'x', 'q'],
        'hree  one   two',
    ),
    'sw1': (
        ['ione  two   three', 'sw', 'sw', '.', 'q'],
        'two  three   one',
    ),
    'sw2': (
        ['ione  two  three', 'sw', 'sw', '.', 'x', 'q'],
        'two  three  ne',
    ),
    'sw3': (
        ['ioneoneone  one  oneone', 'w', 'sw', 'x', 'b', 'sw', '.', 'x', 'q'],
        'oneoneone  ne  neone',
    ),
    'sw4': (
        ['ione  two  three', 'w', 'h', 'sw', '$', 'b', 'h', 'sw', '.', 'q'],
        'one  two  three',
    ),
}


def run_a3_sample(target: Path, no: int) -> None:
    commands, expected = SAMPLE_CASES[no]
    run_case(target, f"A3_test_{no}", commands, expected)


def final_visible_content(segments: list[str]) -> str:
    for segment in reversed(segments[:-1]):
        if segment == "":
            continue
        return segment.rstrip("\n")
    return ""


def run_a2hw_case(target: Path, case_key: str, commands: list[str], expected_final: str) -> None:
    output = run_session(target, commands)
    actual = split_segments(output, len(commands))
    actual = [normalize_segment(item) for item in actual]
    actual_final = normalize_segment(final_visible_content(actual))
    expected_final = normalize_segment(expected_final)
    if actual_final != expected_final:
        raise AssertionError(
            f"A2HW_({case_key}) failed\n"
            f"actual_final: {actual_final!r}\n"
            f"expected_final: {expected_final!r}"
        )
    print(f"[PASS] A2HW_({case_key})")


def A3_test_13(target: Path) -> None:
    run_a3_sample(target, 13)


def A3_test_14(target: Path) -> None:
    run_a3_sample(target, 14)


def A3_test_15(target: Path) -> None:
    run_a3_sample(target, 15)


def A3_test_16(target: Path) -> None:
    run_a3_sample(target, 16)


def A3_test_17(target: Path) -> None:
    run_a3_sample(target, 17)


def A3_test_18(target: Path) -> None:
    run_a3_sample(target, 18)


def A3_test_19(target: Path) -> None:
    run_a3_sample(target, 19)


def A3_test_20(target: Path) -> None:
    run_a3_sample(target, 20)


def A3_test_21(target: Path) -> None:
    run_a3_sample(target, 21)


def A3_test_22(target: Path) -> None:
    run_a3_sample(target, 22)


def A3_test_23(target: Path) -> None:
    run_a3_sample(target, 23)


def A3_test_24(target: Path) -> None:
    run_a3_sample(target, 24)


def A3_test_25(target: Path) -> None:
    run_a3_sample(target, 25)


def Test_From_Teacher(target: Path) -> None:
    commands = [
        "i abcd efg hijk lmn", "$", "dw", "h", "db", "h", "h", "de", "h", "Iab",
        "AAcd", "h", "h", "h", "X", "x", "h", "h", "h", "h", "i asd ", "l", "dc",
        "l", "sb", "sb", "l", "l", "l", "l", "sw", "sw", "h", "sw", "sb", ";", "O",
        "o", "k", "l", "l", "l", "l", "J", "k", "abcdefghijklmn", "j", "j", "dd",
        "2", "dd", "l", "l", "l", "l", "^", "dc", "q",
    ]
    expected = [
        " abcd efg hijk lmn\n",
        " abcd efg hijk lmn\n",
        " abcd efg hijk lm\n",
        " abcd efg hijk lm\n",
        " abcd efg m\n",
        " abcd efg m\n",
        " abcd efg m\n",
        " abcd ef\n",
        " abcd ef\n",
        "ab abcd ef\n",
        "ab abcd efAcd\n",
        "ab abcd efAcd\n",
        "ab abcd efAcd\n",
        "ab abcd efAcd\n",
        "ab abcd fAcd\n",
        "ab abcd Acd\n",
        "ab abcd Acd\n",
        "ab abcd Acd\n",
        "ab abcd Acd\n",
        "ab abcd Acd\n",
        "ab a asd bcd Acd\n",
        "ab a asd bcd Acd\n",
        "ab a  bcd Acd\n",
        "ab a  bcd Acd\n",
        "ab bcd  a Acd\n",
        "bcd ab  a Acd\n",
        "bcd ab  a Acd\n",
        "bcd ab  a Acd\n",
        "bcd ab  a Acd\n",
        "bcd ab  a Acd\n",
        "bcd a  ab Acd\n",
        "bcd a  Acd ab\n",
        "bcd a  Acd ab\n",
        "bcd a  Acd ab\n",
        "bcd a  Acd ab\n",
        "*bcd a  Acd ab\n",
        "*\n bcd a  Acd ab\n",
        " \n*\n bcd a  Acd ab\n",
        " \n \n*bcd a  Acd ab\n",
        " \n \n*bcd a  Acd ab\n",
        " \n \n*bcd a  Acd ab\n",
        " \n \n*bcd a  Acd ab\n",
        " \n \n*bcd a  Acd ab\n",
        " \n*bcd a  Acd ab\n \n",
        " \n bcd a  Acd ab\n*\n",
        " \n bcd a  Acd ab\n*bcdefghijklmn\n",
        " \n*bcd a  Acd ab\n bcdefghijklmn\n",
        "*\n bcd a  Acd ab\n bcdefghijklmn\n",
        "*bcd a  Acd ab\n bcdefghijklmn\n",
        " bcd a  Acd ab\n*bcdefghijklmn\n",
        "*bcd a  Acd ab\n",
        "*bcd a  Acd ab\n",
        "*bcd a  Acd ab\n",
        "*bcd a  Acd ab\n",
        "*bcd a  Acd ab\n",
        "*bcd a  Acd ab\n",
        "* a  Acd ab\n",
        "",
    ]
    run_case(target, "Test_From_Teacher", commands, expected)


def main() -> None:
    target = resolve_target()
    if not target.exists():
        raise SystemExit(f"Target file not found: {target}")

    tests = [
        test_invalid_input_prompt_only,
        test_help_output,
        test_insert_and_append,
        test_word_motion_and_delete,
        test_b_repeat_from_word_start,
        test_multiline_and_line_movement,
        test_line_cursor_render,
        ZZY_TP1,
        A3_test_13,
        A3_test_14,
        A3_test_15,
        A3_test_16,
        A3_test_17,
        A3_test_18,
        A3_test_19,
        A3_test_20,
        A3_test_21,
        A3_test_22,
        A3_test_23,
        A3_test_24,
        A3_test_25,
        Test_From_Teacher,
        # Add your new test function here, e.g.:
        # test_edge_case_spaces,
    ]

    passed = 0
    failed = []
    for test_func in tests:
        try:
            test_func(target)
            passed += 1
        except AssertionError as error:
            failed.append((test_func.__name__, str(error)))
            print(f"[FAIL] {test_func.__name__}")
            print(str(error))
        except Exception as error:
            failed.append((test_func.__name__, f"unexpected error: {error}"))
            print(f"[ERROR] {test_func.__name__}")
            print(f"unexpected error: {error}")
    for case_key in sorted(A2HW_CASES):
        commands, expected_final = A2HW_CASES[case_key]
        case_name = f"A2HW_({case_key})"
        try:
            run_a2hw_case(target, case_key, commands, expected_final)
            passed += 1
        except AssertionError as error:
            failed.append((case_name, str(error)))
            print(f"[FAIL] {case_name}")
            print(str(error))
        except Exception as error:
            failed.append((case_name, f"unexpected error: {error}"))
            print(f"[ERROR] {case_name}")
            print(f"unexpected error: {error}")
    total = len(tests) + len(A2HW_CASES)
    print(f"Summary: passed={passed}, failed={len(failed)}, total={total}")
    if failed:
        print("Failed cases:")
        for name, message in failed:
            print(f"- {name}: {message.splitlines()[0]}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
