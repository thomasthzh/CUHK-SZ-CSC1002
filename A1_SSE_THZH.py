#written at the beginning You must see my brilliant dictionary handling method
#写在前面 你一定要看看我天才的字典处理法
import re
#general environment variables for the editor编辑器的通用环境变量
Content = ""          # Current editind content 当前编辑内容
Cursor = 0            # Cursor's position 光标位置
Show_cursor = True    # Row cursor default enabled 行光标默认开启
#display help info显示帮助信息
def display_help_info():
    print(
    """
    ? - display this help info
    h - move cursor left
    l - move cursor right
    . - toggle row cursor on and off
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
    v - view editor content
    q - quit program
    """
    )
#display content 显示内容
def display_content():
    if not Content or not Show_cursor:
        print(Content)
        return
    left , ch , right= Content[:Cursor], Content[Cursor], Content[Cursor + 1:]
    print(f"{left}\033[42m{ch}\033[0m{right}")
#highlight cursor position with green background 用绿色背景高亮光标位置
def do_dot(text=""):
    global Show_cursor
    Show_cursor = not Show_cursor
#move cursor left光标向左移动
def do_h(text=""):
    global Cursor
    Cursor =max(Cursor - 1, 0)
#move cursor right光标向右移动
def do_l(text=""):
    global Cursor
    Cursor = min(Cursor + 1, len(Content) - 1)
#move cursor to beginning of the line移动到行首
def do_caret(text=""):
    global Cursor
    Cursor = 0
#move cursor to end of the line移动到行尾
def do_dollar(text=""):
    global Cursor
    Cursor = len(Content) - 1
#move cursor to beginning of next word 移动到下一个单词开头
def do_w(text=""):
    global Cursor
    if Content == "" or Cursor == len(Content) - 1:
        return
    for i in range(Cursor, len(Content)-1):
        if Content[i]==" " and Content[i+1] != " ":
            Cursor = i + 1
            return
    Cursor = len(Content) - 1
#move cursor to beginning of current or previous word移动到当前或前一个单词开头
def do_b(text=""):
    global Cursor
    if Content == "" or Cursor == 0:
        return
    for i in range(Cursor-1, 0, -1):
        if Content[i-1]==" " and Content[i] != " ":
            Cursor = i
            return
    Cursor = 0
#move cursor to end of the word移动到单词结尾
def do_e(text=""):
    global Cursor
    if Content == "" or Cursor == len(Content) - 1:
        return
    for i in range(Cursor+1, len(Content)-1):
        if Content[i] != " " and Content[i+1] == " ":
            Cursor = i
            return
    Cursor = len(Content) - 1
#insert text before cursor在光标前插入文本
def do_i(text):
    global Content,Cursor
    Content = Content[:Cursor] + text + Content[Cursor:]
#append text after cursor在光标后插入文本
def do_a(text):
    global Content,Cursor
    if len(Content) == 0:
        Content = text
        Cursor = len(Content) - 1
    else:
        Content = Content[:Cursor+1] + text + Content[Cursor+1:]
        Cursor += len(text)
#insert text from beginning从行首插入文本
def do_I(text):
    global Content,Cursor
    Content = text + Content
    Cursor =0
#append text at the end在行尾插入文本
def do_A(text):
    global Content,Cursor
    Content = Content + text
    Cursor =len(Content) - 1
#delete character at cursor删除光标所在字符
def do_x(text=""):
    global Content,Cursor
    if not Content:
        return
    Content = Content[:Cursor] + Content[Cursor + 1:]
    Cursor = min(Cursor, len(Content) - 1) if Content else 0
#delete character before cursor删除光标前字符
def do_X(text=""):
    global Content,Cursor
    if Cursor == 0 or not Content:
        return
    Content = Content[:Cursor - 1] + Content[Cursor:]
    Cursor -= 1
#view editor content查看编辑内容
def do_v(text=""):
    return None
#Talented and Brilliant Dictionary of Command Handlers XD 天才的命令处理函数字典
command_handlers = {
    '.': do_dot,'h': do_h,'l': do_l,
    '^': do_caret,'$': do_dollar,'w': do_w,
    'b': do_b,'e': do_e,'i': do_i,
    'a': do_a,'I': do_I,'A': do_A,
    'x': do_x,'X': do_X,'v': do_v,
}
#interpret user's command and solve with error handling 解释用户输入的命令并进行错误处理
# def parse_command(user_input):
#     if not user_input:
#         return None , None
#     cmd , text=user_input[0] , user_input[1:]
#     if ( 
#         (cmd not in "?.hl^$wbeiaIAxXvq") or
#         (cmd in "iaIA" and not text) or 
#         (cmd not in "iaIA" and text)
#     ):
#         return None , None
#     return cmd  ,text
def parse_command(user_input):
    if not user_input:
        return None , None
    match = re.match(r"([?.hl^$wbeiaIAxXvq])(.*)", user_input)
    if not match:
        return None , None
    cmd , text = match.groups()
    if cmd in "iaIA" and not text or cmd not in "iaIA" and text:
        return None , None
    return cmd  ,text
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