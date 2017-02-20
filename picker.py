#!/usr/bin/python

# This code is available for use under CC0 (Creative Commons 0 - universal).
# You can copy, modify, distribute and perform the work, even for commercial
# purposes, all without asking permission. For more information, see LICENSE.md or
# https://creativecommons.org/publicdomain/zero/1.0/

# usage:
# opts = Picker(
#    title = 'Delete all files',
#    options = ["Yes", "No"]
# ).getSelected()

# returns a simple list
# cancel returns False

import curses
import shutil
from curses import wrapper

class Picker:
    """Allows you to select from a list with curses"""
    stdscr = None
    win = None
    title = ""
    arrow = ""
    footer = ""
    more = ""
    c_selected = ""
    c_empty = ""

    cursor = 0
    offset = 0
    selected = 0
    selcount = 0
    aborted = False

    window_height = shutil.get_terminal_size().lines - 10
    window_width = shutil.get_terminal_size().columns - 20
    all_options = []
    length = 0

    def curses_start(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.win = curses.newwin(
            5 + self.window_height,
            self.window_width,
            2,
            4
        )

    def curses_stop(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def getSelected(self):
        if self.aborted == True:
            return( False )

        ret_s = [x for x in self.all_options if x["selected"]]
        ret = [x["label"] for x in ret_s]
        return(ret)

    def redraw(self):
        self.win.clear()
        self.win.border(
            self.border[0], self.border[1],
            self.border[2], self.border[3],
            self.border[4], self.border[5],
            self.border[6], self.border[7]
        )
        self.win.addstr(
            self.window_height + 4, 5, " " + self.footer + " "
        )

        position = 0
        range = self.all_options[self.offset:self.offset+self.window_height+1]
        for option in range:
            if option["selected"] == True:
                line_label = self.c_selected + " "
            else:
                line_label = self.c_empty + " "

            if len(option["label"]) > (self.window_width - 20):
                reduced = option["label"][:self.window_width - 20] + "..."
            else:
                reduced = option["label"]
            self.win.addstr(position + 2, 5, line_label + reduced)
            position = position + 1

        # hint for more content above
        if self.offset > 0:
            self.win.addstr(1, 5, self.more)

        # hint for more content below
        if self.offset + self.window_height <= self.length - 2:
            self.win.addstr(self.window_height + 3, 5, self.more)

        self.win.addstr(0, 5, " " + self.title + " ")
        self.win.addstr(
            0, self.window_width - 8,
            " " + str(self.selcount) + "/" + str(self.length) + " "
        )
        self.win.addstr(self.cursor + 2,1, self.arrow)
        self.win.refresh()

    def check_cursor_up(self):
        if self.cursor < 0:
            self.cursor = 0
            if self.offset > 0:
                self.offset = self.offset - 1

    def check_cursor_down(self):
        if self.cursor >= self.length:
            self.cursor = self.cursor - 1

        if self.cursor > self.window_height:
            self.cursor = self.window_height
            self.offset = self.offset + 1

            if self.offset + self.cursor >= self.length:
                self.offset = self.offset - 1

    def curses_loop(self, stdscr):
        while 1:
            self.redraw()
            c = stdscr.getch()

            if c == ord('q') or c == ord('Q'):
                self.aborted = True
                break
            elif c == curses.KEY_UP:
                self.cursor = self.cursor - 1
            elif c == curses.KEY_DOWN:
                self.cursor = self.cursor + 1
            #elif c == curses.KEY_PPAGE:
            #elif c == curses.KEY_NPAGE:
            elif c == ord(' '):
                self.all_options[self.selected]["selected"] = \
                    not self.all_options[self.selected]["selected"]
            elif c == 10:
                break

            # deal with interaction limits
            self.check_cursor_up()
            self.check_cursor_down()

            # compute selected position only after dealing with limits
            self.selected = self.cursor + self.offset

            temp = self.getSelected()
            self.selcount = len(temp)

    def __init__(self, options, title='Select', arrow="-->",
                 footer="Space = toggle, Enter = accept, q = cancel",
                 more="...", border="||--++++", c_selected="[X]", c_empty="[ ]", checked="[ ]"):
        self.title = title
        self.arrow = arrow
        self.footer = footer
        self.more = more
        self.border = border
        self.c_selected = c_selected
        self.c_empty = c_empty

        self.all_options = []

        for option in options:
            self.all_options.append({
                "label": option,
                "selected": True if (option in checked) else False
            })
            self.length = len(self.all_options)

        self.curses_start()
        curses.wrapper( self.curses_loop )
        self.curses_stop()
