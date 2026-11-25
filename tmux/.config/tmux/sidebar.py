#!/usr/bin/env python3
"""Clickable project sidebar for tmux, like neo-tree in nvim.

  sidebar.py toggle PANE   C-n e: show/hide in every window (showing jumps into it)
  sidebar.py focus PANE    C-n o: jump into the sidebar, or back out of it
  sidebar.py open WINDOW   add one to a window (tmux hooks call this)
  sidebar.py run           the UI inside each sidebar pane

Click a project or window to open it, right-click it to pin/unpin.
Keys inside: j/k move, enter open, p pin/unpin, esc back to your pane, q hide.
Pins: ~/.local/share/tmux/sidebar-pins, one path per line, shown in file order.
"""
import curses
import os
import subprocess
import sys

SELF = os.path.realpath(__file__)
WIDTH = 28
PINS = os.path.join(os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share'), 'tmux', 'sidebar-pins')


def tmux(*args):
    r = subprocess.run(['tmux', *args], capture_output=True, text=True)
    return r.stdout.rstrip('\n') if r.returncode == 0 else None


def refresh():
    """Make every sidebar redraw now: they read SIGWINCH as 'redraw'."""
    subprocess.run(['pkill', '-WINCH', '-f', 'sidebar.py run'])


def sidebars():
    """{window_id: pane_id} of every sidebar pane."""
    out = tmux('list-panes', '-a', '-F', '#{window_id} #{pane_id} #{@sidebar_pane}') or ''
    return {w: p for w, p, flag in (line.split(' ') for line in out.splitlines()) if flag == '1'}


def spawn(win):
    # argv[0] "sidebar" so the window is named that while focused, not "python3"
    pane = tmux('split-window', '-hbdf', '-l', str(WIDTH), '-t', win, '-P', '-F', '#{pane_id}',
                f'exec -a sidebar python3 {SELF} run')
    if pane:
        tmux('set', '-p', '-t', pane, '@sidebar_pane', '1')
    return pane


def open_in(win):
    if win not in sidebars():
        spawn(win)


def focus(pane):
    win, mine = tmux('display', '-p', '-t', pane, '#{window_id}\t#{@sidebar_pane}').split('\t')
    if mine == '1':
        tmux('last-pane', '-t', win)
    else:
        tmux('set', '-g', '@sidebar', '1')
        have = sidebars()
        for w in tmux('list-windows', '-a', '-F', '#{window_id}').split():
            if w not in have:
                have[w] = spawn(w)
        if have.get(win):
            tmux('select-pane', '-t', have[win])
    refresh()


def toggle(pane):
    if tmux('show', '-gv', '@sidebar') == '1':
        tmux('set', '-g', '@sidebar', '0')
        # one tmux call: when run from a sidebar (q), killing our own pane would stop a loop midway
        kills = [a for p in sidebars().values() for a in (';', 'kill-pane', '-t', p)][1:]
        if kills:
            tmux(*kills)
    else:
        focus(pane)


def load_pins():
    try:
        with open(PINS) as f:
            return [line for line in f.read().splitlines() if line]
    except FileNotFoundError:
        return []


def pin(path):
    pins = load_pins()
    if path in pins:
        pins.remove(path)
    else:
        pins.append(path)
    os.makedirs(os.path.dirname(PINS), exist_ok=True)
    with open(PINS + '.tmp', 'w') as f:
        f.write(''.join(p + '\n' for p in pins))
    os.replace(PINS + '.tmp', PINS)
    refresh()


def go(act, win):
    tmux('last-pane', '-t', win)  # leave the sidebar, like neo-tree after opening a file
    kind, target, path = act
    if kind == 'window':
        tmux('select-window', '-t', target)
    elif target:
        tmux('switch-client', '-t', target)
    else:
        subprocess.run(['sesh', 'connect', path], capture_output=True)


def build(sessions, me, pins):
    """Rows of (text, attr, action). action = (kind, tmux target or None, project path)."""
    rows = [('', 0, None)]

    def project(path, s):
        cur = s is not None and s['id'] == me
        attr = curses.color_pair(1) | curses.A_BOLD if cur else 0 if s else curses.A_DIM
        name = s['name'] if s else os.path.basename(path)
        rows.append((f" {'●' if s else '○'} {name}", attr, ('project', s and s['id'], path)))
        if cur:
            for wid, idx, wname, active in s['windows']:
                attr = curses.color_pair(2) | curses.A_BOLD if active else 0
                rows.append((f"   {'▌' if active else ' '}{idx} {wname}", attr, ('window', wid, path)))

    by_path = {}
    for s in sessions.values():
        by_path.setdefault(s['path'], s)
    shown = set()
    if pins:
        rows.append((' PINNED', curses.A_BOLD | curses.A_DIM, None))
        for p in pins:
            s = by_path.get(p)
            project(p, s)
            if s:
                shown.add(s['id'])
        rows.append(('', 0, None))
    rest = [s for s in sessions.values() if s['id'] not in shown]
    if rest:
        rows.append((' OPEN', curses.A_BOLD | curses.A_DIM, None))
        for s in rest:
            project(s['path'], s)
    return rows


def put(scr, y, text, attr):
    w = scr.getmaxyx()[1]
    try:
        scr.addnstr(y, 0, text.ljust(w), w, attr)
    except curses.error:
        pass  # curses errors after writing the bottom-right cell; the text is drawn anyway


def ui(scr):
    pane = os.environ['TMUX_PANE']
    curses.curs_set(0)
    curses.use_default_colors()
    curses.set_escdelay(25)
    curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON3_PRESSED)
    curses.mouseinterval(0)
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # current project
    curses.init_pair(2, curses.COLOR_YELLOW, -1)  # current window
    sel, keep, last_ww = None, WIDTH, None
    while True:
        out = tmux('display', '-p', '-t', pane,
                   '#{session_id}\t#{window_id}\t#{window_panes}\t'
                   '#{&&:#{window_active},#{session_attached}}\t#{pane_active}\t#{window_width}\t#{pane_width}',
                   ';', 'list-windows', '-a', '-F',
                   '#{session_id}\t#{session_name}\t#{session_path}\t'
                   '#{window_id}\t#{window_index}\t#{window_name}\t#{window_active}')
        if out is None:
            return
        head, *lines = out.split('\n')
        me, win, npanes, visible, focused, ww, pw = head.split('\t')
        if npanes == '1':
            return  # only the sidebar is left: exit so the window closes too
        if ww != last_ww:  # new or resized window: tmux scaled us with it, put our width back
            if int(pw) != keep:
                tmux('resize-pane', '-t', pane, '-x', str(keep))
        else:
            keep = int(pw)  # window size unchanged, so a new width means you dragged the border
        last_ww = ww
        sessions = {}
        for line in lines:
            sid, name, path, wid, idx, wname, active = line.split('\t')
            s = sessions.setdefault(sid, {'id': sid, 'name': name, 'path': path, 'windows': []})
            s['windows'].append((wid, idx, wname, active == '1'))
        rows = build(sessions, me, load_pins())
        acts = [r[2] for r in rows if r[2]]
        focused = focused == '1'
        if not focused or sel not in acts:
            sel = next((a for a in acts if a[1] == win), None)  # start on the current window

        h, w = scr.getmaxyx()
        body = h - focused  # last line holds the key hints while focused
        i = next((n for n, r in enumerate(rows) if r[2] == sel), 0)
        top = max(0, i - body + 1)
        scr.erase()
        for y, (text, attr, act) in enumerate(rows[top:top + body]):
            put(scr, y, text, attr | (curses.A_REVERSE if focused and act == sel else 0))
        if focused:
            put(scr, h - 1, ' ↵ open  p pin  q hide', curses.A_DIM)
        scr.refresh()

        scr.timeout(1000 if visible == '1' else -1)  # hidden ones sleep until a tmux hook wakes them
        key = scr.getch()
        if key == curses.KEY_MOUSE:
            try:
                _, _, y, _, button = curses.getmouse()
            except curses.error:
                continue
            act = rows[top + y][2] if y < body and top + y < len(rows) else None
            if act:
                sel = act
                if button & curses.BUTTON3_PRESSED:
                    pin(act[2])
                    if not focused:  # the click pulled focus in here; hand it back
                        tmux('last-pane', '-t', win)
                else:
                    go(act, win)
        elif key in (ord('j'), ord('k'), curses.KEY_DOWN, curses.KEY_UP) and acts:
            step = 1 if key in (ord('j'), curses.KEY_DOWN) else -1
            sel = acts[max(0, min(len(acts) - 1, (acts.index(sel) if sel in acts else 0) + step))]
        elif key in (10, 13, curses.KEY_ENTER, ord('l')) and sel:
            go(sel, win)
        elif key == ord('p') and sel:
            pin(sel[2])
        elif key == 27:
            tmux('last-pane', '-t', win)
        elif key == ord('q'):
            toggle(pane)


if __name__ == '__main__':
    cmd, arg = sys.argv[1], (sys.argv[2:] or [''])[0]
    if cmd == 'run':
        curses.wrapper(ui)
    else:
        {'toggle': toggle, 'focus': focus, 'open': open_in}[cmd](arg)
