#written at the beginning You must see my brilliant dictionary handling method
#写在前面 你一定要看看我天才的字典处理法
import re
#general environment variables for the editor编辑器的通用环境变量
content = ""          # Current editind content 当前编辑内容
cursor = 0            # Cursor's position 光标位置
show_cursor = True    # Row cursor default enabled 行光标默认开启
#display help info显示帮助信息
def display_help_info():
    print("""? - display this help info
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
dc - delete whitepaces or entire word at cursor
sw - swap word at cursor with next word
sb - swap word at cursor with previous word
v - view editor content
q - quit program""")
    
#?-display content 显示内容
def display_content():
    if not content or not show_cursor:
        print(content)
        return
    left , ch , right= content[:cursor], content[cursor], content[cursor + 1:]
    print(f"{left}\033[42m{ch}\033[0m{right}")
#.-highlight cursor position with green background 用绿色背景高亮光标位置
def do_dot(text=""):
    global show_cursor
    show_cursor = not show_cursor
#l-move cursor left光标向左移动
def do_h(text=""):
    global cursor
    cursor =max(cursor - 1, 0)
#h-move cursor right光标向右移动
def do_l(text=""):
    global cursor
    cursor = min(cursor + 1, len(content) - 1)
#^-move cursor to beginning of the line移动到行首
def do_caret(text=""):
    global cursor
    cursor = 0
#&-move cursor to end of the line移动到行尾
def do_dollar(text=""):
    global cursor
    cursor = len(content) - 1
#w-move cursor to beginning of next word 移动到下一个单词开头
def do_w(text=""):
    global cursor
    if content == "" or cursor == len(content) - 1:
        return
    for i in range(cursor, len(content)-1):
        if content[i]==" " and content[i+1] != " ":
            cursor = i + 1
            return
    cursor = len(content) - 1
#b-move cursor to beginning of current or previous word移动到当前或前一个单词开头
def do_b(text=""):
    global cursor
    if content == "" or cursor == 0:
        return
    for i in range(cursor-1, 0, -1):
        if content[i-1]==" " and content[i] != " ":
            cursor = i
            return
    cursor = 0
#e-move cursor to end of the word移动到单词结尾
def do_e(text=""):
    global cursor
    if content == "" or cursor == len(content) - 1:
        return
    for i in range(cursor+1, len(content)-1):
        if content[i] != " " and content[i+1] == " ":
            cursor = i
            return
    cursor = len(content) - 1
#i-insert text before cursor在光标前插入文本
def do_i(text):
    global content,cursor
    content = content[:cursor] + text + content[cursor:]
#a-append text after cursor在光标后插入文本
def do_a(text):
    global content,cursor
    if len(content) == 0:
        content = text
        cursor = len(content) - 1
    else:
        content = content[:cursor+1] + text + content[cursor+1:]
        cursor += len(text)
#I-insert text from beginning从行首插入文本
def do_I(text):
    global content,cursor
    content = text + content
    cursor =0
#A-append text at the end在行尾插入文本
def do_A(text):
    global content,cursor
    content = content + text
    cursor =len(content) - 1
#x-delete character at cursor删除光标所在字符
def do_x(text=""):
    global content,cursor
    if not content:
        return
    content = content[:cursor] + content[cursor + 1:]
    cursor = min(cursor, len(content) - 1) if content else 0
#X-delete character before cursor删除光标前字符
def do_X(text=""):
    global content,cursor
    if cursor == 0 or not content:
        return
    content = content[:cursor - 1] + content[cursor:]
    cursor -= 1

#delete a range of text from start to end 删除从start到end的文本
def delete_range(start, end):
    global content, cursor
    if start > end:
        start, end = end, start
    content = content[:start] + content[end:]
    cursor = start if start < len(content) else len(content) - 1 if content else 0

#dw-delete to the beginning of the next word删除到下一个单词开头
def do_dw(text=""):
    global cursor
    start = cursor
    do_w()
    end = cursor
    delete_range(start, end)

#de-delete to the end of the next word删除到下一个单词结尾
def do_de(text=""):
    global cursor
    start = cursor
    do_e()
    end = cursor + 1
    delete_range(start, end)

#db-delete to the beginning of the current or previous word删除到当前或前一个单词开头
def do_db(text=""):
    global cursor
    start = cursor+1
    do_b()
    end = cursor
    delete_range(end, start)

#dc-delete white spaces or entire word at cursor删除光标所在的空格或整个单词
def do_dc(text=""):
    global cursor, content
    if not content:
        return
    if content[cursor] == " ":
        left = cursor
        while left > 0 and content[left - 1] == " ":
            left -= 1
        right = cursor
        while right < len(content) and content[right] == " ":
            right += 1
        delete_range(left, right)
    else:
        left = cursor
        while left > 0 and content[left - 1] != " ":
            left -= 1
        right = cursor
        while right < len(content) and content[right] != " ":
            right += 1
        delete_range(left, right)

#sw-swap word at cursor with next word交换光标所在单词与下一个单词
def do_sw(text=""):
    global cursor, content
    if not content or content[cursor] == " ":
        return
    left_a = cursor
    while left_a > 0 and content[left_a - 1] != " ":
        left_a -= 1
    right_a = cursor
    while right_a < len(content) and content[right_a] != " ":
        right_a += 1
    offset = cursor - left_a
    left_b = right_a
    while left_b < len(content) and content[left_b] == " ":
        left_b += 1
    if left_b >= len(content):
        return
    right_b = left_b
    while right_b < len(content) and content[right_b] != " ":
        right_b += 1
    word_a = content[left_a:right_a]
    word_b = content[left_b:right_b]
    content = (
        content[:left_a] +
        word_b +
        content[right_a:left_b] +
        word_a +
        content[right_b:]
    )
    new_a_left = left_a + len(word_b) + (left_b - right_a)
    cursor = new_a_left + min(offset, len(word_a) - 1)

#sb-swap word at cursor with previous word交换光标所在单词与前一个单词
def do_sb(text=""):
    global cursor, content
    if not content or content[cursor] == " ":
        return
    left_a = cursor
    while left_a > 0 and content[left_a - 1] != " ":
        left_a -= 1
    right_a = cursor
    while right_a < len(content) and content[right_a] != " ":
        right_a += 1
    offset = cursor - left_a
    right_b = left_a
    while right_b > 0 and content[right_b - 1] == " ":
        right_b -= 1
    if right_b == 0 and (content[0] == " " or left_a == 0):
        return
    left_b = right_b
    while left_b > 0 and content[left_b - 1] != " ":
        left_b -= 1
    if left_b == right_b:
        return
    word_a = content[left_a:right_a]
    word_b = content[left_b:right_b]
    content = (
        content[:left_b] +
        word_a +
        content[right_b:left_a] +
        word_b +
        content[right_a:]
    )
    cursor = left_b + min(offset, len(word_a) - 1)

#v-view editor content查看编辑内容
def do_v(text=""):
    return None
#Talented and Brilliant Dictionary of Command Handlers XD 天才的命令处理函数字典
command_handlers = {
    '?': display_help_info,
    '.': do_dot,'h': do_h,'l': do_l,
    '^': do_caret,'$': do_dollar,'w': do_w,
    'b': do_b,'e': do_e,'i': do_i,
    'a': do_a,'I': do_I,'A': do_A,
    'x': do_x,'X': do_X,'dw': do_dw,'de': do_de,
    'db': do_db,'dc': do_dc,'sw': do_sw,'sb': do_sb,
    'v': do_v,
}
#interpret user's command and solve with error handling 解释用户输入的命令并进行错误处理
def parse_command(user_input):
    if not user_input:
        return None, None
    cmd, text = user_input[0], user_input[1:]
    if cmd in "ds":
        if len(user_input) < 2:
            return None, None
        cmd += user_input[1]
        text = user_input[2:]
    if (cmd in "iaIA" and not text) or (cmd not in "iaIA" and text):
        return None, None
    if cmd not in command_handlers:
        return None, None
    return cmd, text
#main loop 程序主循环
while True:
    user_input = input(">")
    cmd , text = parse_command(user_input)
    if cmd is None and text is None:
        continue
    elif cmd == "q":
        break
    elif cmd == "?":
        display_help_info()
    else:
        command_handlers[cmd](text)
        display_content()