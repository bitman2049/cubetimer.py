#!/usr/bin/python3

import curses
import time
import json
import os

class timer():
    def __init__(self):
        self.curr = 0
        self.start = 0
        self.timing = False
        self.load()
        if self.history:
            self.curr = self.history[0]

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
        if self.history:
            del self.history[0]
        if self.history:
            self.curr = self.history[0]
        else:
            self.curr = 0

    def save(self):
        with open("hist", "w") as f:
            json.dump(self.history, f)

    def load(self):
        if os.path.isfile("hist"):
            with open("hist", "r") as f:
                self.history = json.load(f)
        else:
            self.history = []
            
class display():
    asciinums = [
        [" ,---. ","/    /\\","|   / |","|  /  |","\\ /   /"," `._.' "],
        [" ,-,   ","/  |   ","   |   ","   |   ","   |   ","___|___"],
        [" ,---. ","/     \\","      /"," ,---' ","/      ","|______"],
        ["------.","     / ","   ,/_ ","      \\","      /","`.__.' "],
        ["  ,  , "," /   | ","/____|_","     | ","     | ","     | "],
        [".----- ","|      ","|____  ","     `,","      /","`.__.' "],
        [" ,---. ","/     \\","|.---. ","|     \\","\\     /"," `._.' "],
        ["------.","      |","     / ","    /  ","   /   ","  /    "],
        [" ,---. ","|     |"," `>-<' ","/     \\","\\     /"," `._.' "],
        [" ,---. ","/     \\","\\     |"," `---'|","      /","`.__.' "],
    ]
    
    def __init__(self, x, y, timer):
        self.window = curses.newwin(10, 59, y, x)
        self.timer = timer
        self.draw()

    def draw(self, isbest=False):
        self.window.border("|", "|", "-", "-", "+", "+", "+", "+")
        self.window.addch(9,46,"+")
        if isbest:
            flag = curses.color_pair(3) | curses.A_BOLD
        else:
            flag = 0
        self.window.addch(7, 29, "o", flag)
        vint = int(1000 * self.timer.curr + 0.5)
        for lineno in range(6):
            for i, n in enumerate(f"{vint:6d}"):
                if n == ' ':
                    if i <= 1:
                        string = "       "
                    else:
                        string = self.asciinums[0][lineno]
                else:
                    string = self.asciinums[int(n)][lineno]
                off = 0
                if i > 2:
                    off = 2
                self.window.addstr(2 + lineno, 5 + i*8 + off, string, flag)
        self.window.redrawwin()   
        self.window.refresh()

class history_box():
    def __init__(self, x, y, history):
        self.window = curses.newwin(15, 14, y, x)
        self.history = history
        self.draw()

    def draw(self):
        self.window.addstr(1, 4, "History")
        for i, t in enumerate(self.history[:12]):
            if t == min(self.history[:12]):
                flag = curses.color_pair(1)
            elif t == max(self.history[:12]):
                flag = curses.color_pair(2)
            else:
                flag = 0
            self.window.addstr(2 + i, 1, f"{i+1:2d}: {t:7.3f}", flag)
        self.window.clrtobot()
        self.window.border("|", "|", "-", "-", "+", "+", "+", "+")
        self.window.redrawwin()
        self.window.refresh()

class stats_box():
    def __init__(self, x, y, history):
        self.window = curses.newwin(15,46,y,x)
        self.history = history
        self.draw()
     
    def draw(self):
        nonestr = "-------"
        self.window.clrtobot()
        self.window.border("|", "|", "-", "-", "+", "+", "+", "+")
        self.window.addstr(1, 20, "Stats")
        self.window.addstr(3, 3, "Best [all time]")
        if self.history:
            t = min(self.history)
            self.window.addstr(4, 5, f"{t:7.3f}")
        else:
            self.window.addstr(4, 5, nonestr)
        self.window.addstr(6, 3, "Best [last 12]")
        if self.history:    
            t = min(self.history[:12])
            self.window.addstr(7, 5, f"{t:7.3f}")
        else:
            self.window.addstr(7, 5, nonestr)
        self.window.addstr(3, 28, "Avg [3 of 5]")
        if len(self.history) >= 5:
            t = self.avg(5)
            self.window.addstr(4, 30, f"{t:7.3f}")
        else:
            self.window.addstr(4, 30, nonestr)
        self.window.addstr(6, 28, "Avg [10 of 12]")
        if len(self.history) >= 12:
            t = self.avg(12)
            self.window.addstr(7, 30, f"{t:7.3f}")
        else:
            self.window.addstr(7, 30, nonestr)
        self.window.redrawwin()
        self.window.refresh()
        
    def avg(self, n):
        times = self.history[:n]
        hi = max(times)
        lo = min(times)
        times.remove(hi)
        times.remove(lo)
        return sum(times) / max(len(times), 1)

class application():
    tickdur = 0.001
    frameskip = 50
    
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
        self.history_box = history_box(45, 9, self.timer.history)
        self.stats_box = stats_box(0, 9, self.timer.history)
        self.display = display(0, 0, self.timer)
        self.tick = 0
        self.draw()
    
    def __del__(self):
        self.timer.save()
        curses.endwin()

    def run(self):
        while not self.ex:
            self.update()
            self.draw()
            time.sleep(self.tickdur)

    def update(self):
        ch = self.window.getch()
        if ch == ord('q'):
            self.ex = True
        elif ch == ord(' '):
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
        self.timer.update()
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

