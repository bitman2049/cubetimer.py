#!/usr/bin/python3

import curses
import time

def avg(history, n, discard_outliers):
    if n > len(history) or n <= 0:
        return -1
    if discard_outliers:
        times = history[:n]
        hi = max(times)
        lo = min(times)
        times.remove(hi)
        times.remove(lo)
        return sum(times) / max(len(times), 1)
    else:
        return sum(history[:n])/max(n, 1)

class timer():
    curr = 0
    start = 0
    timing = False
    history = []
    
    def __init__(self):
        self.curr = 0
        self.start = 0
        self.timing = False
        self.history = []

    def update(self):
        if not self.timing:
            return
        self.curr = time.time() - self.start

    def start_time(self):
        self.start = time.time()
        self.curr = 0
        self.timing = True

    def stop_time(self):
        self.timing = False
        self.history.insert(0, self.curr)

    def discard_last(self):
        if len(self.history) > 0:
            del self.history[0]

class big_digit():
    value = None
    digits = [
        " ,---. /    /\\|   / ||  /  |\\ /   / `._.'",  # 0
        " ,-,   /  |      |      |      |   ___|___",   # 1
        " ,---. /     \\      / ,---' /      |______",  # 2
        "------.     /    ,/_       \\      /`.__.'",   # 3
        "  ,  ,  /   | /____|_     |      |      |",    # 4
        ".----- |      |____       `,      /`.__.'",    # 5
        " ,---. /     \\|.---. |     \\\\     / `._.'", # 6
        "------.      |     /     /     /     /",       # 7
        " ,---. |     | `>-<' /     \\\\     / `._.'",  # 8
        " ,---. /     \\\\     | `---'|      /`.__.'",  # 9
    ]
    
    def __init__(self, value=0):
        self.value=value

    def to_list(self):
        # TODO redo class so lists are stored statically
        digstr = self.digits[self.value]
        lst = [digstr[7*i:7*i+7] for i in range(6)]
        if len(lst[5]) < 7:
            lst[5] = lst[5] + " "*(7 - len(lst[5]))
        return lst

class display():
    digits = []
    value = 0
    window = None
    
    def __init__(self, x, y, value):
        self.window = curses.newwin(10, 59, y, x)
        for i in range(6):
            d = big_digit()
            self.digits.append(d)
        self.update(0)
        self.draw()

    def update(self, value):
        self.value = value
        tint = int(1000 * self.value + 0.5)
        denom = 10 ** (len(self.digits) - 1)
        for d in self.digits:
            d.value = (tint // denom) % 10
            denom //= 10
        return

    def draw(self, isbest=False):
        self.window.border("|", "|", "-", "-", "+","+","+","+")
        if isbest:
            flag = curses.color_pair(3)
        else:
            flag = 0
        self.window.addch(7, 29, "o", flag)
        for lineno in range(6):
            start = False
            for i, d in enumerate(self.digits):
                string = d.to_list()[lineno]
                if not start and d.value == 0 and i <= 1:
                    string = "       "
                else:
                    start = True
                off = 0
                if i > 2:
                    off = 2
                self.window.addstr(2 + lineno, 5 + i*8 + off, string, flag)
        self.window.redrawwin()   
        self.window.refresh()

class history_box():
    window = None
    history = None
    
    def __init__(self, x, y, history):
        self.window = curses.newwin(15, 15, y, x)
        self.history = history
        self.draw()

    def draw(self):
        self.window.addstr(1, 5, "History")
        for i, t in enumerate(self.history[:12]):
            if t == min(self.history[:12]):
                flag = curses.color_pair(1)
            elif t == max(self.history[:12]):
                flag = curses.color_pair(2)
            else:
                flag = 0
            self.window.addstr(2 + i, 2, "{:2d}: ".format(i + 1) + "{:7.3f}".format(t), flag)
        self.window.clrtobot()
        self.window.border("|", "|", "-", "-", "+","+","+","+")
        self.window.redrawwin()
        self.window.refresh()

class stats_box():
    window = None
    history = None
    
    def __init__(self, x, y, history):
        self.window = curses.newwin(15,46,y,x)
        self.history = history
        self.draw()
     
    def draw(self):
        nonestr = "-------"
        self.window.clrtobot()
        self.window.border("|", "|", "-", "-", "+","+","+","+")
        self.window.addstr(1, 20, "Stats")
        self.window.addstr(3, 2, "Best single [session]")
        if self.history:
            t = min(self.history)
            self.window.addstr(4, 4, f"{t:7.3f}")
        else:
            self.window.addstr(4, 4, nonestr)
        self.window.addstr(6, 2, "Best single [last 12]")
        if self.history:    
            t = min(self.history[:12])
            self.window.addstr(7, 4, f"{t:7.3f}")
        else:
            self.window.addstr(7, 4, nonestr)
        self.window.addstr(3, 28, "Avg [3 of 5]")
        if len(self.history) >= 5:
            t = avg(self.history, 5, True)
            self.window.addstr(4, 30, f"{t:7.3f}")
        else:
            self.window.addstr(4, 30, nonestr)
        self.window.addstr(6, 28, "Avg [10 of 12]")
        if len(self.history) >= 12:
            t = avg(self.history, 12, True)
            self.window.addstr(7, 30, f"{t:7.3f}")
        else:
            self.window.addstr(7, 30, nonestr)
        self.window.redrawwin()
        self.window.refresh()

class application():
    window = None
    timer = None
    display = None
    history_box = None
    stats_box = None
    tick = 0
    tickdur = 0.001
    frameskip = 50
    ex = False
    
    def __init__(self):
        self.window = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.curs_set(0)
        self.ex = False
        self.timer = timer()
        self.history_box = history_box(44, 9, self.timer.history)
        self.stats_box = stats_box(0, 9, self.timer.history)
        self.display = display(0, 0, 0)
        self.tick = 0
        self.draw()
    
    def __del__(self):
        curses.endwin()

    def run(self):
        while not self.ex:
            self.update()
            self.draw()
            time.sleep(self.tickdur)

    def update(self):
        ch = self.window.getch()
        if ch == 27:
            self.window.nodelay(True)
            ch2 = self.window.getch()
            if ch2 == -1:
                self.ex = True
            else:
                if not self.timer.timing:
                    self.window.nodelay(False)
        elif ch == 32:
            if self.timer.timing:
                self.timer.stop_time()
                self.window.nodelay(False)
            else:
                self.window.nodelay(True)
                self.timer.start_time()
        elif ch == 127:
            if self.timer.timing:
                self.timer.stop_time()
                self.window.nodelay(False)
            self.timer.discard_last()
            self.timer.curr = 0
        self.timer.update()
        self.display.update(self.timer.curr)
        self.tick += 1
                
    def draw(self):
        if not self.timer.timing or self.tick % self.frameskip == 0:
            self.window.refresh()
            self.display.draw(not self.timer.timing and self.timer.history and self.timer.history[0]==min(self.timer.history))
            self.history_box.draw()
            self.stats_box.draw()

def main():
    app = application()
    app.run()

if __name__ == "__main__":
    main()


