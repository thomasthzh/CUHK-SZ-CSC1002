#This time I reconstruct my code, maybe this code style is better
#I ensure that every function is small and does one thing, and I also add some comments to explain the purpose of each function. I also use a dictionary to map commands to their handlers, which makes the code more organized and easier to maintain.
#If you are reading my code, just enjoy it
#The 3 most things I am proud of is build_handlers, state used to maintain 2-D editor and reuse basic functions to realize the functionality.
# awa XD (0v0) 
import re

GREEN_BG_ON = "\033[42m"
GREEN_BG_OFF = "\033[0m"

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

TEXT_COMMANDS = {"i", "a", "I", "A"}
SINGLE_COMMANDS = {
    "?", ".", ";", "h", "l", "^", "$", "w", "b", "e", "j", "k",
    "o", "O", "x", "X", "J", "K", "v", "q"
}
DOUBLE_COMMANDS = {"dw", "de", "db", "dc", "sw", "sb", "dd"}


# Create initial editor state, 创建编辑器初始状态
def make_state():
    return {
        "lines": [""],
        "row": 0,
        "col": 0,
        "show_row_cursor": True,
        "show_line_cursor": False,
    }


# Get current active line text, 获取当前活动行文本
def current_line(state):
    return state["lines"][state["row"]]


# Update current active line text, 更新当前活动行文本
def set_current_line(state, text):
    state["lines"][state["row"]] = text


# Return last valid index of a line, 返回行的最后有效索引
def line_end(text):
    return len(text) - 1 if text else 0


# Clamp column within current line bounds, 将列光标限制在当前行范围内
def clamp_col(state):
    state["col"] = min(state["col"], line_end(current_line(state)))


# Get total number of lines, 获取总行数
def row_count(state):
    return len(state["lines"])


# Find start index of next word, 查找下一个单词起始位置
def next_word_start(text, col):
    if not text or col >= len(text) - 1:
        return None
    for idx in range(col, len(text) - 1):
        if text[idx] == " " and text[idx + 1] != " ":
            return idx + 1
    return None


# Find start index of current/previous word, 查找当前或前一个单词起始位置
def prev_word_start(text, col):
    if not text or col == 0:return 0
    probe = min(col, len(text) - 1)
    probe -= 1 if text[probe] != " " and text[probe - 1] == " " else 0
    while probe > 0 and text[probe] == " ": probe -= 1
    while probe > 0 and text[probe - 1] != " ": probe -= 1
    return probe


# Find end index of current/next word, 查找当前或下一个单词结束位置
def word_end(text, col):
    if not text or col >= len(text) - 1:
        return line_end(text)
    seek = col + 1 if text[col] != " " and text[col + 1] == " " else col
    seek = skip_spaces_forward(text, seek)
    return seek_word_end(text, seek)


# Skip spaces moving forward, 向前跳过连续空格
def skip_spaces_forward(text, idx):
    while idx < len(text) and text[idx] == " ":
        idx += 1
    return idx


# Walk to the end of a word, 移动到单词末尾
def seek_word_end(text, idx):
    if idx >= len(text):
        return len(text) - 1
    while idx + 1 < len(text) and text[idx + 1] != " ":
        idx += 1
    return idx


# Delete substring and return new cursor, 删除片段并返回新光标位置
def delete_span(text, start, end):
    if start > end:
        start, end = end, start
    if start == end:
        end += 1
    new_text = text[:start] + text[end:]
    new_col = start if start < len(new_text) else line_end(new_text)
    return new_text, new_col


# Get word boundaries at cursor, 获取光标所在单词边界
def word_bounds(text, col):
    if not text or text[col] == " ":
        return None
    return scan_word_left(text, col), scan_word_right(text, col)


# Scan left to word start, 向左扫描到单词起点
def scan_word_left(text, col):
    while col > 0 and text[col - 1] != " ":
        col -= 1
    return col


# Scan right to word end boundary, 向右扫描到单词终点边界
def scan_word_right(text, col):
    while col < len(text) and text[col] != " ":
        col += 1
    return col


# Get boundaries of next word, 获取下一个单词边界
def next_word_bounds(text, start):
    left = skip_spaces_forward(text, start)
    if left >= len(text):
        return None
    return left, scan_word_right(text, left)


# Get boundaries of previous word, 获取前一个单词边界
def prev_word_bounds(text, end):
    right = skip_spaces_backward(text, end)
    if right == 0:
        return None
    return scan_word_left(text, right - 1), right


# Skip spaces moving backward, 向后跳过连续空格
def skip_spaces_backward(text, idx):
    while idx > 0 and text[idx - 1] == " ":
        idx -= 1
    return idx


# Get continuous space boundaries at cursor, 获取光标处连续空格边界
def space_bounds(text, col):
    return scan_space_left(text, col), scan_space_right(text, col)


# Scan left across spaces, 向左扫描空格区间
def scan_space_left(text, col):
    while col > 0 and text[col - 1] == " ":
        col -= 1
    return col


# Scan right across spaces, 向右扫描空格区间
def scan_space_right(text, col):
    while col < len(text) and text[col] == " ":
        col += 1
    return col


# Print help menu text, 打印帮助菜单
def display_help():
    print(HELP_TEXT)


# Render row-cursor highlight on active line, 在活动行渲染行光标高亮
def highlight_line(state, text, active):
    if not (active and state["show_row_cursor"] and text):
        return text
    col = min(state["col"], len(text) - 1)
    return f"{text[:col]}{GREEN_BG_ON}{text[col]}{GREEN_BG_OFF}{text[col + 1:]}"


# Build line-cursor prefix marker, 生成行光标前缀标记
def line_prefix(state, idx):
    if not state["show_line_cursor"]:
        return ""
    return "*" if idx == state["row"] else " "


# Print all editor lines to console, 将编辑器全部行输出到控制台
def display_content(state):
    for idx, text in enumerate(state["lines"]):
        body = highlight_line(state, text, idx == state["row"])
        print(line_prefix(state, idx) + body)


# Toggle row cursor visibility, 切换行内光标显示
def do_dot(state, _=""):
    state["show_row_cursor"] = not state["show_row_cursor"]


# Toggle line cursor visibility, 切换行光标显示
def do_semicolon(state, _=""):
    state["show_line_cursor"] = not state["show_line_cursor"]


# Move cursor left by one, 光标左移一位
def do_h(state, _=""):
    state["col"] = max(state["col"] - 1, 0)


# Move cursor right by one, 光标右移一位
def do_l(state, _=""):
    state["col"] = min(state["col"] + 1, line_end(current_line(state)))


# Move cursor to line start, 光标移动到行首
def do_caret(state, _=""):
    state["col"] = 0


# Move cursor to line end, 光标移动到行尾
def do_dollar(state, _=""):
    state["col"] = line_end(current_line(state))


# Move cursor to next word start, 光标移动到下一个单词开头
def do_w(state, _=""):
    nxt = next_word_start(current_line(state), state["col"])
    state["col"] = nxt if nxt is not None else line_end(current_line(state))


# Move cursor to current/previous word start, 光标移动到当前或前一个单词开头
def do_b(state, _=""):
    state["col"] = prev_word_start(current_line(state), state["col"])


# Move cursor to word end, 光标移动到单词结尾
def do_e(state, _=""):
    state["col"] = word_end(current_line(state), state["col"])


# Move active line cursor vertically, 垂直移动活动行光标
def move_row(state, delta):
    row = state["row"] + delta
    if 0 <= row < row_count(state):
        state["row"] = row
        clamp_col(state)


# Move to previous line, 移动到上一行
def do_j(state, _=""):
    move_row(state, -1)


# Move to next line, 移动到下一行
def do_k(state, _=""):
    move_row(state, 1)


# Insert text before cursor, 在光标前插入文本
def do_i(state, text):
    line, col = current_line(state), state["col"]
    set_current_line(state, line[:col] + text + line[col:])


# Get insertion point for append command, 获取追加命令插入位置
def append_point(state):
    return 0 if not current_line(state) else state["col"] + 1


# Append text after cursor, 在光标后追加文本
def do_a(state, text):
    line, point = current_line(state), append_point(state)
    set_current_line(state, line[:point] + text + line[point:])
    state["col"] = point + len(text) - 1


# Insert text at line beginning, 在行首插入文本
def do_I(state, text):
    set_current_line(state, text + current_line(state))
    state["col"] = 0


# Append text at line end, 在行尾追加文本
def do_A(state, text):
    line = current_line(state) + text
    set_current_line(state, line)
    state["col"] = line_end(line)


# Insert an empty line around active line, 在活动行附近插入空行
def insert_empty_line(state, delta):
    idx = state["row"] + delta
    state["lines"].insert(idx, "")
    state["row"] = idx
    state["col"] = 0


# Insert empty line below, 在下方插入空行
def do_o(state, _=""):
    insert_empty_line(state, 1)


# Insert empty line above, 在上方插入空行
def do_O(state, _=""):
    insert_empty_line(state, 0)


# Delete character at cursor, 删除光标处字符
def do_x(state, _=""):
    line, col = current_line(state), state["col"]
    if not line:
        return
    set_current_line(state, line[:col] + line[col + 1:])
    clamp_col(state)


# Delete character before cursor, 删除光标前字符
def do_X(state, _=""):
    line, col = current_line(state), state["col"]
    if not line or col == 0:
        return
    set_current_line(state, line[:col - 1] + line[col:])
    state["col"] -= 1


# Apply deletion range to current line, 在当前行应用删除范围
def apply_delete(state, start, end):
    new_line, new_col = delete_span(current_line(state), start, end)
    set_current_line(state, new_line)
    state["col"] = min(state["col"], line_end(new_line)) if new_line else new_col


# Delete toward next word start, 删除到下一个单词开头
def do_dw(state, _=""):
    line, start = current_line(state), state["col"]
    nxt = next_word_start(line, start)
    end = nxt if nxt is not None else len(line)
    new_line, new_col = delete_span(line, start, end)
    set_current_line(state, new_line)
    state["col"] = new_col


# Delete toward word end, 删除到单词结尾
def do_de(state, _=""):
    line, start = current_line(state), state["col"]
    end = word_end(line, start) + 1
    new_line, _ = delete_span(line, start, end)
    set_current_line(state, new_line)
    state["col"] = min(start, line_end(new_line))


# Delete backward to previous word start, 向后删除到前一个单词开头
def do_db(state, _=""):
    old_col = state["col"]
    do_b(state)
    apply_delete(state, state["col"], old_col + 1)


# Delete spaces or word at cursor, 删除光标处空格段或整个单词
def do_dc(state, _=""):
    line, col = current_line(state), state["col"]
    if not line:
        return
    bounds = space_bounds(line, col) if line[col] == " " else word_bounds(line, col)
    if bounds is not None:
        apply_delete(state, bounds[0], bounds[1])


# Delete current line, 删除当前行
def do_dd(state, _=""):
    del state["lines"][state["row"]]
    if state["lines"]:
        state["row"] = min(state["row"], row_count(state) - 1)
        clamp_col(state)
        return
    state["lines"], state["row"], state["col"] = [""], 0, 0


# Swap two forward-order word segments, 交换顺序为前后关系的两个单词片段
def swap_text(line, left_a, right_a, left_b, right_b):
    return line[:left_a] + line[left_b:right_b] + line[right_a:left_b] + line[left_a:right_a] + line[right_b:]


# Swap current word with adjacent direction, 按方向交换当前单词
def swap_with(state, direction):
    line = current_line(state)
    first = word_bounds(line, state["col"])
    if first is None:return
    second = next_word_bounds(line, first[1]) if direction > 0 else prev_word_bounds(line, first[0])
    if second is None:return
    apply_swap(state, line, first, second)


# Apply swap and update cursor position, 执行交换并更新光标位置
def apply_swap(state, line, first, second):
    left_a, right_a = first; left_b, right_b = second
    offset = state["col"] - left_a
    if left_b > left_a:
        set_current_line(state, swap_text(line, left_a, right_a, left_b, right_b))
        old_len, new_len = right_a - left_a, right_b - left_b
        state["col"] = left_a + (left_b - right_a) + min(offset, old_len - 1) + new_len; return
    set_current_line(state, line[:left_b] + line[left_a:right_a] + line[right_b:left_a] + line[left_b:right_b] + line[right_a:])
    state["col"] = left_b + min(offset, right_a - left_a - 1)


# Swap with next word, 与下一个单词交换
def do_sw(state, _=""):
    swap_with(state, 1)


# Swap with previous word, 与前一个单词交换
def do_sb(state, _=""):
    swap_with(state, -1)


# Swap two line contents, 交换两行内容
def swap_lines(state, a, b):
    state["lines"][a], state["lines"][b] = state["lines"][b], state["lines"][a]


# Move active line upward, 将当前行上移
def do_move_line_up(state, _=""):
    if state["row"] == 0:
        return
    swap_lines(state, state["row"], state["row"] - 1)
    state["row"] -= 1
    clamp_col(state)


# Move active line downward, 将当前行下移
def do_move_line_down(state, _=""):
    if state["row"] >= row_count(state) - 1:
        return
    swap_lines(state, state["row"], state["row"] + 1)
    state["row"] += 1
    clamp_col(state)


# Jump to specified line number, 跳转到指定行号
def do_line_no(state, target):
    state["row"] = min(target - 1, row_count(state) - 1)
    state["col"] = 0


# No-op view command hook, 查看命令占位函数
def do_v(_state, _=""):
    return None


# Parse raw user command input, 解析用户原始命令输入
def parse_command(user_input):
    if not user_input:
        return None, None
    if re.fullmatch(r"[1-9]\d*", user_input):
        return user_input, ""
    return parse_non_numeric(user_input)


# Parse non-numeric command patterns, 解析非数字命令格式
def parse_non_numeric(user_input):
    cmd = user_input[0]
    if cmd in TEXT_COMMANDS and len(user_input) > 1:return cmd, user_input[1:]
    if len(user_input) == 2 and user_input in DOUBLE_COMMANDS:return user_input, ""
    if len(user_input) == 1 and cmd in SINGLE_COMMANDS:return cmd, ""
    return None, None


# Execute parsed command handler, 执行解析后的命令处理器
def run_command(state, handlers, command, text):
    if command.isdigit():
        do_line_no(state, int(command))
        return
    handlers[command](state, text)


# Read one input and parse it, 读取一条输入并解析
def read_parsed_command():
    return parse_command(input(">"))


# Handle one command lifecycle, 处理单条命令的执行流程
def handle_command(state, handlers, command, text):
    if command == "?":
        display_help()
        return
    run_command(state, handlers, command, text)
    if not (command in {"?", "q"}):
        display_content(state)


# Build command-to-function mapping in HELP_TEXT order, 按 HELP_TEXT 顺序构建映射
build_handlers = {
    ".": do_dot, ";": do_semicolon,
    "h": do_h, "l": do_l, "^": do_caret, "$": do_dollar, "w": do_w, "b": do_b, "e": do_e,
    "j": do_j, "k": do_k,
    "i": do_i, "a": do_a, "I": do_I, "A": do_A, "o": do_o, "O": do_O,
    "x": do_x, "X": do_X, "dw": do_dw, "de": do_de, "db": do_db, "dc": do_dc, "dd": do_dd,
    "sw": do_sw, "sb": do_sb, "J": do_move_line_up, "K": do_move_line_down,
    "v": do_v,
}


# Run the editor main loop, 运行编辑器主循环
def main():
    state, handlers = make_state(), build_handlers
    while True:
        command, text = read_parsed_command()
        if command is None:continue
        if command == "q":break
        handle_command(state, handlers, command, text)


if __name__ == "__main__":
    main()
