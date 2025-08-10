#!/usr/bin/env python3
import os
import sys  
import shlex
import readline
import shutil
import curses
import glob
import time
import subprocess

env_vars = {}

COMMANDS = ["say", "sv", "fd", "ld", "qw", "cl", "dl", "ed", "help", "exit", "version", "run"]

CELESTIA_VERSION = "1.0.2"

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"

# Detect installed apps from PATH
def get_installed_apps():
    app_names = set()
    for path_dir in os.getenv("PATH", "").split(os.pathsep):
        if os.path.isdir(path_dir):
            for file in os.listdir(path_dir):
                file_path = os.path.join(path_dir, file)
                if os.access(file_path, os.X_OK) and not os.path.isdir(file_path):
                    app_names.add(file)
    return sorted(app_names)

APP_LIST = get_installed_apps()

def completer(text, state):
    buffer = readline.get_line_buffer()
    line = shlex.split(buffer)
    if not line:
        options = [cmd + ' ' for cmd in COMMANDS if cmd.startswith(text)]
    else:
        if readline.get_begidx() == 0:
            options = [cmd + ' ' for cmd in COMMANDS if cmd.startswith(text)]
        elif line[0] == "run":
            options = [app + ' ' for app in APP_LIST if app.startswith(text)]
        else:
            before_cursor = buffer[:readline.get_endidx()]
            tokens = before_cursor.split()
            if not tokens:
                return None
            last_token = tokens[-1]
            options = [f for f in glob.glob(last_token + '*')]
    try:
        return options[state]
    except IndexError:
        return None

readline.set_completer(completer)
readline.parse_and_bind('tab: complete')

# UPDATED get_prompt with colors, moved OUTSIDE main()
def get_prompt():
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    if cwd == home:
        cwd_display = ""
    elif cwd.startswith(home):
        cwd_display = cwd.replace(home, "~")
    else:
        cwd_display = cwd
    if cwd_display:
        return f"{BOLD}{CYAN}VortexOS{RESET}:{GREEN}{cwd_display}{RESET}> "
    else:
        return f"{BOLD}{CYAN}VortexOS{RESET}> "

def print_splash():
    splash = (
    r"""
     ______  _______  __       _______     _______.___________. __       ___       ______        _______.
     /      ||   ____||  |     |   ____|   /       |           ||  |     /   \     /  __  \      /       |
    |  ,----'|  |__   |  |     |  |__     |   (----`---|  |----`|  |    /  ^  \   |  |  |  |    |   (----`
    |  |     |   __|  |  |     |   __|     \   \       |  |     |  |   /  /_\  \  |  |  |  |     \   \    
    |  `----.|  |____ |  `----.|  |____.----)   |      |  |     |  |  /  _____  \ |  `--'  | .----)   |   
    \______||_______||_______||_______|_______/       |__|     |__| /__/     \__\ \______/  |_______/    
                                                                                                      
    Welcome to CelestiaOS v""" + CELESTIA_VERSION + """
    Type 'help' to get started.
"""
)
    print(splash)

def cmd_say(args):
    out = []
    for arg in args:
        if arg.startswith("$"):
            var_name = arg[1:]
            out.append(env_vars.get(var_name, arg))
        else:
            out.append(arg)
    print(" ".join(out))

def cmd_sv(args):
    if len(args) != 1 or '=' not in args[0]:
        print("sv usage: sv var=value")
        return
    var, value = args[0].split('=', 1)
    env_vars[var] = value

def cmd_fd(args):
    if len(args) == 0:
        target = os.path.expanduser("~")
    else:
        target = args[0]
        if target == "~":
            target = os.path.expanduser("~")
    try:
        os.chdir(target)
    except FileNotFoundError:
        print(f"fd: no such file or directory: {target}")
    except NotADirectoryError:
        print(f"fd: not a directory: {target}")
    except PermissionError:
        print(f"fd: permission denied: {target}")

def cmd_ld(args):
    target = args[0] if args else "."
    if not os.path.exists(target):
        print(f"ld: no such file or directory: {target}")
        return
    if os.path.isfile(target):
        print(target)
        return
    try:
        items = os.listdir(target)
        for item in items:
            print(item)
    except PermissionError:
        print(f"ld: permission denied: {target}")

def cmd_qw(args):
    if not args:
        print("qw usage: qw filename [text to write]")
        return
    filename = args[0]
    if len(args) == 1:
        if not os.path.exists(filename):
            print(f"{filename} doesn't exist.")
            create = input(f"Do you want to create {filename}? (y/n): ").strip().lower()
            if create == 'y':
                try:
                    with open(filename, 'w') as f:
                        pass
                    print(f"Created {filename}")
                except Exception as e:
                    print(f"Error creating file: {e}")
            return
        try:
            with open(filename, 'r') as f:
                content = f.read()
            print(content)
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        text = " ".join(args[1:])
        try:
            with open(filename, 'w') as f:
                f.write(text)
            print(f"qw: wrote to '{filename}'")
        except Exception as e:
            print(f"Error writing to file: {e}")

def cmd_cl(args):
    os.system('cls' if os.name == 'nt' else 'clear')

def cmd_dl(args):
    if not args:
        print("dl usage:")
        print("  dl filename [-y]")
        print("  dl -fl foldername [-y]")
        return
    flags = [arg for arg in args if arg.startswith('-')]
    others = [arg for arg in args if not arg.startswith('-')]
    is_folder = False
    auto_yes = False
    for flag in flags:
        if flag == '-fl':
            is_folder = True
        elif flag == '-y':
            auto_yes = True
        else:
            print(f"dl: unknown flag {flag}")
            return
    if len(others) == 0:
        print("dl: specify file or folder name")
        return
    target = others[0]
    if not os.path.exists(target):
        print(f"dl: no such file or directory: {target}")
        return
    if is_folder and not os.path.isdir(target):
        print(f"dl: {target} is not a folder")
        return
    if not is_folder and os.path.isdir(target):
        print(f"dl: {target} is a folder, use -fl flag")
        return
    if not auto_yes:
        ans = input(f"Are you sure you want to delete '{target}'? (y/n): ").strip().lower()
        if ans != 'y':
            print("Delete cancelled")
            return
    try:
        if is_folder:
            shutil.rmtree(target)
        else:
            os.remove(target)
        print(f"Deleted '{target}'")
    except Exception as e:
        print(f"dl: error deleting {target}: {e}")

def run_editor(filename):
    def editor(stdscr):
        curses.curs_set(1)
        stdscr.keypad(True)
        curses.use_default_colors()
        try:
            with open(filename, 'r') as f:
                lines = f.read().splitlines()
            if len(lines) == 0:
                lines = ['']
        except FileNotFoundError:
            lines = ['']
        cursor_x, cursor_y = 0, 0
        offset_y = 0
        height, width = stdscr.getmaxyx()
        saved = True

        def redraw():
            stdscr.clear()
            for idx in range(offset_y, min(len(lines), offset_y + height - 1)):
                try:
                    stdscr.addstr(idx - offset_y, 0, lines[idx])
                except curses.error:
                    pass
            status = f"Editing: {filename}  Lines: {len(lines)}  {'Saved' if saved else 'Modified'}  F2=Save  F4=Quit"
            try:
                stdscr.addstr(height-1, 0, status[:width-1], curses.A_REVERSE)
            except curses.error:
                pass
            stdscr.move(cursor_y - offset_y, cursor_x)
            stdscr.refresh()

        while True:
            redraw()
            key = stdscr.getch()

            if key == curses.KEY_F2:
                try:
                    with open(filename, 'w') as f:
                        f.write('\n'.join(lines) + '\n')
                    saved = True
                except Exception as e:
                    stdscr.addstr(0, 0, f"Error saving file: {e}")
                    stdscr.refresh()
                    stdscr.getch()
            elif key == curses.KEY_F4:
                if not saved:
                    stdscr.addstr(height-2, 0, "Unsaved changes! Press F4 again to quit without saving, any other key to cancel.")
                    stdscr.refresh()
                    confirm = stdscr.getch()
                    if confirm == curses.KEY_F4:
                        break
                else:
                    break
            elif key in (curses.KEY_BACKSPACE, 127):
                if cursor_x > 0:
                    lines[cursor_y] = lines[cursor_y][:cursor_x-1] + lines[cursor_y][cursor_x:]
                    cursor_x -= 1
                    saved = False
                elif cursor_y > 0:
                    prev_len = len(lines[cursor_y-1])
                    lines[cursor_y-1] += lines[cursor_y]
                    del lines[cursor_y]
                    cursor_y -= 1
                    cursor_x = prev_len
                    saved = False
            elif key == curses.KEY_DC:
                if cursor_x < len(lines[cursor_y]):
                    lines[cursor_y] = lines[cursor_y][:cursor_x] + lines[cursor_y][cursor_x+1:]
                    saved = False
                elif cursor_y + 1 < len(lines):
                    lines[cursor_y] += lines[cursor_y+1]
                    del lines[cursor_y+1]
                    saved = False
            elif key == curses.KEY_LEFT:
                if cursor_x > 0:
                    cursor_x -= 1
                elif cursor_y > 0:
                    cursor_y -= 1
                    cursor_x = len(lines[cursor_y])
            elif key == curses.KEY_RIGHT:
                if cursor_x < len(lines[cursor_y]):
                    cursor_x += 1
                elif cursor_y + 1 < len(lines):
                    cursor_y += 1
                    cursor_x = 0
            elif key == curses.KEY_UP:
                if cursor_y > 0:
                    cursor_y -= 1
                    cursor_x = min(cursor_x, len(lines[cursor_y]))
                    if cursor_y < offset_y:
                        offset_y -= 1
            elif key == curses.KEY_DOWN:
                if cursor_y + 1 < len(lines):
                    cursor_y += 1
                    cursor_x = min(cursor_x, len(lines[cursor_y]))
                    if cursor_y >= offset_y + height - 1:
                        offset_y += 1
            elif key == curses.KEY_ENTER or key == 10 or key == 13:
                new_line = lines[cursor_y][cursor_x:]
                lines[cursor_y] = lines[cursor_y][:cursor_x]
                lines.insert(cursor_y+1, new_line)
                cursor_y += 1
                cursor_x = 0
                saved = False
            elif 0 <= key <= 255:
                lines[cursor_y] = lines[cursor_y][:cursor_x] + chr(key) + lines[cursor_y][cursor_x:]
                cursor_x += 1
                saved = False

    curses.wrapper(editor)

def cmd_ed(args):
    if not args:
        print("ed usage: ed filename")
        return
    run_editor(args[0])

def cmd_run(args):
    if not args:
        print("run usage: run appname [args...]")
        return
    appname = args[0]
    appargs = args[1:]
    try:
        result = subprocess.run([appname] + appargs)
    except FileNotFoundError:
        print(f"run: command not found: {appname}")

def cmd_help(args):
    help_text = """
Available commands:
  say [text or $var]    - Print text or variable
  sv var=value          - Set variable
  fd [path]             - Change directory
  ld [path]             - List directory contents
  qw filename [text]    - Write text to file or read file if no text
  cl                    - Clear screen
  dl filename [-y]      - Delete file with optional yes flag
  dl -fl foldername [-y]- Delete folder with optional yes flag
  ed filename           - Edit file in text editor
  run app [args...]     - Run external app with arguments
  help                  - Show this help
  version               - Show version
  exit                  - Exit VortexOS
"""
    print(help_text)

def cmd_version(args):
    print(f"CelestiaOS version {CELESTIA_VERSION}")

def main():
    print_splash()
    while True:
        try:
            prompt = get_prompt()   # get prompt string
            line = input(prompt)    # read input line using prompt
        except EOFError:
            print()
            break
        if not line.strip():
            continue
        try:
            parts = shlex.split(line)
        except ValueError as e:
            print(f"Parsing error: {e}")
            continue
        cmd = parts[0]
        args = parts[1:]
        if cmd == "say":
            cmd_say(args)
        elif cmd == "sv":
            cmd_sv(args)
        elif cmd == "fd":
            cmd_fd(args)
        elif cmd == "ld":
            cmd_ld(args)
        elif cmd == "qw":
            cmd_qw(args)
        elif cmd == "cl":
            cmd_cl(args)
        elif cmd == "dl":
            cmd_dl(args)
        elif cmd == "ed":
            cmd_ed(args)
        elif cmd == "run":
            cmd_run(args)
        elif cmd == "help":
            cmd_help(args)
        elif cmd == "version":
            cmd_version(args)
        elif cmd == "exit":
            break
        else:
            print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
