import re


HELP_TEXT = """? - display this help info
. - toggle row cursor on and off
; - toggle line cursor on and off
h - move cursor left
l - move cursor right
^ - move cursor to beginning of line
$ - move cursor to end of line
w - move cursor to beginning of next word
b - move cursor to beginning of current or previous word
e - move cursor to end of current or next word
j - move to line above
k - move to line below
i - insert <text> before cursor
a - append <text> after cursor
I - insert <text> at beginning of line
A - append <text> at end of line
o - insert empty line below current line
O - insert empty line above current line
x - delete character at cursor
X - delete character before cursor
dw - delete to start of next word
de - delete to end of word
db - delete to start of current or previous word
dc - delete spaces or entire word at cursor
dd - delete current line
sw - swap word at cursor with next word
sb - swap word at cursor with previous word
J - move current line up
K - move current line down
<Line_No.> - jump to line number
v - view editor content
q - quit program"""

TEXT_COMMANDS = {"i", "a", "I", "A"}
SINGLE_COMMANDS = {
    "?", ".", ";", "h", "l", "^", "$", "w", "b", "e", "j", "k",
    "o", "O", "x", "X", "J", "K", "v", "q"
}
DOUBLE_COMMANDS = {"dw", "de", "db", "dc", "sw", "sb", "dd"}


def make_state():
    return {
        "lines": [""],
        "row": 0,
        "col": 0,
        "show_row_cursor": True,
        "show_line_cursor": False,
    }


def current_line(state):
    return state["lines"][state["row"]]


def set_current_line(state, text):
    state["lines"][state["row"]] = text


def line_end(text):
    return len(text) - 1 if text else 0


def clamp_col(state):
    state["col"] = min(state["col"], line_end(current_line(state)))


def row_count(state):
    return len(state["lines"])


def next_word_start(text, col):
    if not text or col >= len(text) - 1:
        return None
    for idx in range(col, len(text) - 1):
        if text[idx] == " " and text[idx + 1] != " ":
            return idx + 1
    return None


def prev_word_start(text, col):
    if not text or col == 0:
        return 0
    for idx in range(col, 0, -1):
        if text[idx - 1] == " " and text[idx] != " ":
            return idx
    return 0


def word_end(text, col):
    if not text or col >= len(text) - 1:
        return line_end(text)
    seek = col + 1 if text[col] != " " and text[col + 1] == " " else col
    seek = skip_spaces_forward(text, seek)
    return seek_word_end(text, seek)


def skip_spaces_forward(text, idx):
    while idx < len(text) and text[idx] == " ":
        idx += 1
    return idx


def seek_word_end(text, idx):
    if idx >= len(text):
        return len(text) - 1
    while idx + 1 < len(text) and text[idx + 1] != " ":
        idx += 1
    return idx


def delete_span(text, start, end):
    if start > end:
        start, end = end, start
    if start == end:
        end += 1
    new_text = text[:start] + text[end:]
    new_col = start if start < len(new_text) else line_end(new_text)
    return new_text, new_col


def word_bounds(text, col):
    if not text or text[col] == " ":
        return None
    return scan_word_left(text, col), scan_word_right(text, col)


def scan_word_left(text, col):
    while col > 0 and text[col - 1] != " ":
        col -= 1
    return col


def scan_word_right(text, col):
    while col < len(text) and text[col] != " ":
        col += 1
    return col


def next_word_bounds(text, start):
    left = skip_spaces_forward(text, start)
    if left >= len(text):
        return None
    return left, scan_word_right(text, left)


def prev_word_bounds(text, end):
    right = skip_spaces_backward(text, end)
    if right == 0:
        return None
    return scan_word_left(text, right - 1), right


def skip_spaces_backward(text, idx):
    while idx > 0 and text[idx - 1] == " ":
        idx -= 1
    return idx


def space_bounds(text, col):
    return scan_space_left(text, col), scan_space_right(text, col)


def scan_space_left(text, col):
    while col > 0 and text[col - 1] == " ":
        col -= 1
    return col


def scan_space_right(text, col):
    while col < len(text) and text[col] == " ":
        col += 1
    return col


def display_help():
    print(HELP_TEXT)


def highlight_line(state, text, active):
    if not (active and state["show_row_cursor"] and text):
        return text
    col = min(state["col"], len(text) - 1)
    return f"{text[:col]}\033[42m{text[col]}\033[0m{text[col + 1:]}"


def line_prefix(state, idx):
    if not state["show_line_cursor"]:
        return ""
    return "*" if idx == state["row"] else " "


def display_content(state):
    for idx, text in enumerate(state["lines"]):
        body = highlight_line(state, text, idx == state["row"])
        print(line_prefix(state, idx) + body)


def do_dot(state, _=""):
    state["show_row_cursor"] = not state["show_row_cursor"]


def do_semicolon(state, _=""):
    state["show_line_cursor"] = not state["show_line_cursor"]


def do_h(state, _=""):
    state["col"] = max(state["col"] - 1, 0)


def do_l(state, _=""):
    state["col"] = min(state["col"] + 1, line_end(current_line(state)))


def do_caret(state, _=""):
    state["col"] = 0


def do_dollar(state, _=""):
    state["col"] = line_end(current_line(state))


def do_w(state, _=""):
    nxt = next_word_start(current_line(state), state["col"])
    state["col"] = nxt if nxt is not None else line_end(current_line(state))


def do_b(state, _=""):
    state["col"] = prev_word_start(current_line(state), state["col"])


def do_e(state, _=""):
    state["col"] = word_end(current_line(state), state["col"])


def move_row(state, delta):
    row = state["row"] + delta
    if 0 <= row < row_count(state):
        state["row"] = row
        clamp_col(state)


def do_j(state, _=""):
    move_row(state, -1)


def do_k(state, _=""):
    move_row(state, 1)


def do_i(state, text):
    line, col = current_line(state), state["col"]
    set_current_line(state, line[:col] + text + line[col:])


def append_point(state):
    return 0 if not current_line(state) else state["col"] + 1


def do_a(state, text):
    line, point = current_line(state), append_point(state)
    set_current_line(state, line[:point] + text + line[point:])
    state["col"] = point + len(text) - 1


def do_I(state, text):
    set_current_line(state, text + current_line(state))
    state["col"] = 0


def do_A(state, text):
    line = current_line(state) + text
    set_current_line(state, line)
    state["col"] = line_end(line)


def insert_empty_line(state, delta):
    idx = state["row"] + delta
    state["lines"].insert(idx, "")
    state["row"] = idx
    state["col"] = 0


def do_o(state, _=""):
    insert_empty_line(state, 1)


def do_O(state, _=""):
    insert_empty_line(state, 0)


def do_x(state, _=""):
    line, col = current_line(state), state["col"]
    if not line:
        return
    set_current_line(state, line[:col] + line[col + 1:])
    clamp_col(state)


def do_X(state, _=""):
    line, col = current_line(state), state["col"]
    if not line or col == 0:
        return
    set_current_line(state, line[:col - 1] + line[col:])
    state["col"] -= 1


def apply_delete(state, start, end):
    new_line, new_col = delete_span(current_line(state), start, end)
    set_current_line(state, new_line)
    state["col"] = min(state["col"], line_end(new_line)) if new_line else new_col


def do_dw(state, _=""):
    line, start = current_line(state), state["col"]
    nxt = next_word_start(line, start)
    end = nxt if nxt is not None else len(line)
    new_line, new_col = delete_span(line, start, end)
    set_current_line(state, new_line)
    state["col"] = new_col


def do_de(state, _=""):
    start = state["col"]
    do_e(state)
    apply_delete(state, start, state["col"] + 1)


def do_db(state, _=""):
    old_col = state["col"]
    do_b(state)
    apply_delete(state, state["col"], old_col + 1)


def do_dc(state, _=""):
    line, col = current_line(state), state["col"]
    if not line:
        return
    bounds = space_bounds(line, col) if line[col] == " " else word_bounds(line, col)
    if bounds is not None:
        apply_delete(state, bounds[0], bounds[1])


def do_dd(state, _=""):
    del state["lines"][state["row"]]
    if state["lines"]:
        state["row"] = min(state["row"], row_count(state) - 1)
        clamp_col(state)
        return
    state["lines"], state["row"], state["col"] = [""], 0, 0


def swap_text(line, left_a, right_a, left_b, right_b):
    return line[:left_a] + line[left_b:right_b] + line[right_a:left_b] + line[left_a:right_a] + line[right_b:]


def swap_text_rev(line, left_a, right_a, left_b, right_b):
    return line[:left_b] + line[left_a:right_a] + line[right_b:left_a] + line[left_b:right_b] + line[right_a:]


def swap_with(state, bounds_getter):
    line, col = current_line(state), state["col"]
    first = word_bounds(line, col)
    if first is None:
        return
    second = bounds_getter(line, first[0], first[1])
    if second is None:
        return
    apply_swap(state, line, first, second)


def apply_swap(state, line, first, second):
    left_a, right_a = first
    left_b, right_b = second
    offset = state["col"] - left_a
    if left_b > left_a:
        apply_forward_swap(state, line, first, second, offset)
        return
    apply_backward_swap(state, line, first, second, offset)


def apply_forward_swap(state, line, first, second, offset):
    left_a, right_a = first
    left_b, right_b = second
    set_current_line(state, swap_text(line, left_a, right_a, left_b, right_b))
    old_len, new_len = right_a - left_a, right_b - left_b
    state["col"] = left_a + (left_b - right_a) + min(offset, old_len - 1) + new_len


def apply_backward_swap(state, line, first, second, offset):
    left_a, right_a = first
    left_b, right_b = second
    set_current_line(state, swap_text_rev(line, left_a, right_a, left_b, right_b))
    state["col"] = left_b + min(offset, right_a - left_a - 1)


def do_sw(state, _=""):
    swap_with(state, lambda line, _left, right: next_word_bounds(line, right))


def do_sb(state, _=""):
    swap_with(state, lambda line, left, _right: prev_word_bounds(line, left))


def swap_lines(state, a, b):
    state["lines"][a], state["lines"][b] = state["lines"][b], state["lines"][a]


def do_move_line_up(state, _=""):
    if state["row"] == 0:
        return
    swap_lines(state, state["row"], state["row"] - 1)
    state["row"] -= 1
    clamp_col(state)


def do_move_line_down(state, _=""):
    if state["row"] >= row_count(state) - 1:
        return
    swap_lines(state, state["row"], state["row"] + 1)
    state["row"] += 1
    clamp_col(state)


def do_line_no(state, target):
    state["row"] = min(target - 1, row_count(state) - 1)
    state["col"] = 0


def do_v(_state, _=""):
    return None


def parse_command(user_input):
    if not user_input:
        return None, None
    if re.fullmatch(r"[1-9]\d*", user_input):
        return user_input, ""
    return parse_non_numeric(user_input)


def parse_non_numeric(user_input):
    cmd = user_input[0]
    if cmd in TEXT_COMMANDS and len(user_input) > 1:
        return cmd, user_input[1:]
    if len(user_input) == 2 and user_input in DOUBLE_COMMANDS:
        return user_input, ""
    if len(user_input) == 1 and cmd in SINGLE_COMMANDS:
        return cmd, ""
    return None, None


def run_command(state, handlers, command, text):
    if command.isdigit():
        do_line_no(state, int(command))
        return
    handlers[command](state, text)


def should_skip_output(command):
    return command in {"?", "q"}


def read_parsed_command():
    return parse_command(input(">"))


def handle_command(state, handlers, command, text):
    if command == "?":
        display_help()
        return
    run_command(state, handlers, command, text)
    if not should_skip_output(command):
        display_content(state)


def build_handlers():
    return {
        ".": do_dot, ";": do_semicolon, "h": do_h, "l": do_l, "^": do_caret,
        "$": do_dollar, "w": do_w, "b": do_b, "e": do_e, "j": do_j, "k": do_k,
        "i": do_i, "a": do_a, "I": do_I, "A": do_A, "o": do_o, "O": do_O,
        "x": do_x, "X": do_X, "dw": do_dw, "de": do_de, "db": do_db,
        "dc": do_dc, "dd": do_dd, "sw": do_sw, "sb": do_sb,
        "J": do_move_line_up, "K": do_move_line_down, "v": do_v,
    }


def main():
    state, handlers = make_state(), build_handlers()
    while True:
        command, text = read_parsed_command()
        if command is None:
            continue
        if command == "q":
            break
        handle_command(state, handlers, command, text)


if __name__ == "__main__":
    main()
