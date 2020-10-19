import random
import sys
import tkinter as tk
import math

# defaults to 1000, recursive AI might need more (e.g. 40x40 game)
sys.setrecursionlimit(100000)


class MineSweeperInteractive(object):
    """
    """

    def __init__(self, size):
        self.size = size

        # Create minesweeper board
        self.cells = set((x, y)
                         for x in range(self.size)
                         for y in range(self.size))

        # setting mines
        mines_number = self.getmines()
        self._mines = set()
        while len(self._mines) < mines_number:
            self._mines.add((random.randrange(size),
                             random.randrange(size)))

        # For each square, gives the set of its neighbours
        # ni = not identified
        # neighbours =  number of neighbour
        self.data = {}
        for (x, y) in self.cells:
            neighbour = self.getneighbour(x, y)
            self.data[x, y] = {"neighbour": neighbour, "neighbours": len(neighbour), "status": "C", "clue": "ni"}
        # Environment data:
        self.empty_remaining = size * size - mines_number
        # Mantain list of open cells.
        self.opened = set()
        # flagged the identified mine.
        self.flagged = set()
        # Mantain list of safe cells to generate hints.
        self.safe = []
        # mines_near[xy] will be populated when you open xy.
        # It it was a mine, it will be 'mine' instead of a number.
        self.mines_busted = set()
        # keeping track of suggestions initialized with 1 signifies it is random
        self.suggestedstep = ((-1, -1), 1)

        # Starting point suggestion
        print("Start with cell %s " % str(random.choice(list(self.cells))))

    def open(self, xy):
        """
        Opens the cell xy and checks if it is a mine or safe
        """
        if xy in self.opened:
            return

        self.opened.add(xy)     # add to the list of opened cells
        if xy in self._mines:       # if mine, update status to M
            self.mines_busted.add(xy)
            self.data.get(xy)["status"] = "M"
        else:
            # Updating the clue
            self.data.get(xy)["status"] = "S"   # otherwise update status to S
            self.data.get(xy)["clue"] = len(self.data[xy].get("neighbour") & self._mines)
            self.empty_remaining -= 1
            if self.empty_remaining <= 0:
                self.win()

    def flag(self, xy):
        """
        Flags the cell xy
        """
        self.flagged.add(xy)

    def win(self):
        """
        Display number of mines tripped (busted)
        """
        trippedmines = len(self.mines_busted)
        if trippedmines:
            self.message("You finished with %s tripped mines. Total mines were %s" %(trippedmines, len(self._mines)))
        else:
            self.message("You won without tripping any mines :-)")

    def getneighbour(self, x, y):
        """
        returns list of neighbors for the cell (x, y)
        """
        neigh = set((nx, ny) for nx in [x - 1, x, x + 1] for ny in [y - 1, y, y + 1] if (nx, ny) != (x, y) if
                    (nx, ny) in self.cells)
        return neigh

    def getmines(self):
        """
        returns number of mines based on the size of the maze
        """
        if self.size < 20:
            return math.floor(0.25 * (self.size ** 2))
        elif 20 <= self.size < 40:
            return math.floor(0.30 * (self.size ** 2))
        elif 40 <= self.size < 60:
            return math.floor(0.35 * (self.size ** 2))
        elif 60 <= self.size < 100:
            return math.floor(0.40 * (self.size ** 2))
        else:
            return math.floor(0.50 * (self.size ** 2))

    def updateinformation(self):
        """
        updates the information for the cells in the board
        """
        # for all the cells in the board except the busted mines and flagged cells
        for (x, y) in (self.cells - self.mines_busted - self.flagged):
            if self.data.get((x, y)).get("clue") != "ni":    # if the clue for the cell is not ni (not identified)
                hidden = 0
                hiddenlist = set()
                safe = 0
                safelist = set()
                mine = 0
                minelist = set()
                for n in self.data.get((x, y)).get("neighbour"):
                    if self.data.get(n).get("status") == "C":
                        hidden += 1
                        hiddenlist.add(n)
                    elif self.data.get(n).get("status") == "S":     # if the status of the cell is safe, add to safelist
                        safe += 1   # update number of safe cells
                        safelist.add(n)
                    elif self.data.get(n).get("status") == "M":     # if the cell is a mine, add to minelist
                        mine += 1   # update number of mines detected
                        minelist.add(n)
                if self.data.get((x, y)).get("clue") - mine == hidden:
                    for sn in hiddenlist:
                        self.data.get(sn)["status"] = "M"
                        self.flag(sn)
                elif (self.data.get((x, y)).get("neighbours") - self.data.get((x, y)).get("clue")) - safe == hidden:
                    for sn in hiddenlist:
                        self.data.get(sn)["status"] = "S"
                        if sn not in self.opened and sn not in self.safe:
                            self.safe.append(sn)
        return self.generatehint()

    def generatehint(self):
        """
        function to generate a hint for the game to proceed
        """
        if self.safe:    # if safe
            step = self.safe.pop(0)     # remove the first element from the safe list
            rand = 0
        else:
            permittedsteps = self.cells - self.opened - self.flagged    # get remaining cells excluding the opened and flagged cells
            step = random.choice(list(permittedsteps))      # from these cells, choose one randomly
            rand = 1
        self.suggestedstep = (step, rand)
        return step, rand

    def message(self, string):
        """ To be overridden by GUI class"""


class MineSweeperInteractiveGUI(MineSweeperInteractive):
    """
    GUI wrapper.
    Left/right-click calls .open() / flag();
    calling .open() and .flag() also updates GUI.
    """

    def __init__(self, *args, **kw):
        MineSweeperInteractive.__init__(self, *args, **kw)
        self.window = tk.Tk()
        self.table = tk.Frame(self.window)
        self.table.pack()
        self.squares = {}
        # Build buttons

        for xy in self.cells:
            self.squares[xy] = button = tk.Button(self.table, padx=0, pady=0)
            row, column = xy
            # expand button to North, East, West, South
            button.grid(row=row, column=column, sticky="news")
            scale = math.floor(50 // (1 if self.size // 10 == 0 else self.size // 10))
            self.table.grid_columnconfigure(column, minsize=scale)
            self.table.grid_rowconfigure(row, minsize=scale)

            # needed to restore bg to default when unflagging
            self._default_button_bg = self.squares[xy].cget("bg")

            def clicked(selected=xy):
                self.open(selected)
                if self.empty_remaining > 0:
                    if selected != self.suggestedstep[0] and self.suggestedstep[1] != 1:
                        if selected in self.safe:
                            self.safe.remove(selected)
                        self.safe.insert(0, self.suggestedstep[0])
                    step, rand = self.updateinformation()
                    if rand == 0:
                        print("Hint :: Choose %s " % str(step))
                    else:
                        print("Random suggestion :: Choose %s " % str(step))

            button.config(command=clicked)
            self.refresh(xy)

    def refresh(self, xy):
        """Update GUI for given square."""
        button = self.squares[xy]

        text, fg, bg = self.getvisualdataforcell(xy)
        button.config(text=text, fg=fg, bg=bg)

        if xy in self.opened:
            button.config(relief=tk.SUNKEN)

        if self.empty_remaining > 0:
            self.message("%d Cells to go" %
                         len(self.cells - self.opened))

    def getvisualdataforcell(self, xy):
        """"""
        if xy in self.opened:
            if xy in self._mines:
                return u'\N{SKULL AND CROSSBONES}', None, 'red'

            mn = self.data.get(xy).get("clue")
            if mn > 0:
                # "standard" minesweeper colors (I think?)
                fg = {1: 'blue', 2: 'dark green', 3: 'red',
                      4: 'dark blue', 5: 'dark red',
                      }.get(mn, 'black')
                return str(mn), fg, 'white'
            else:
                return '0', None, 'white'

        # unopened
        if self.empty_remaining > 0:
            # during play
            if xy in self.flagged:
                return u'\N{BLACK FLAG}', None, 'yellow'
            else:
                return ' ', None, self._default_button_bg
        else:
            # after victory
            if xy in self.flagged:
                return u'\N{WHITE FLAG}', None, 'green'
            else:
                return '', None, 'green'

    def open(self, xy):
        super(MineSweeperInteractiveGUI, self).open(xy)
        self.refresh(xy)

    def updateinformation(self):
        step = super(MineSweeperInteractiveGUI, self).updateinformation()
        for i in self.flagged:
            self.refresh(i)
        return step

    def flag(self, xy):
        super(MineSweeperInteractiveGUI, self).flag(xy)
        self.refresh(xy)

    def win(self):
        super(MineSweeperInteractiveGUI, self).win()
        # change all unopened mines to victory state
        for xy in self._mines - self.opened:
            self.refresh(xy)

    def message(self, string):
        self.window.title(string)


def main(cls):
    root = tk.Tk()
    root.title("Let's Play Minesweeper")
    canvas1 = tk.Canvas(root, width=400, height=200, relief='raised')
    canvas1.pack()
    label1 = tk.Label(root, text='Minesweeper')
    label1.config(font=('helvetica', 14))
    canvas1.create_window(200, 25, window=label1)
    label2 = tk.Label(root, text='Enter the size:')
    label2.config(font=('helvetica', 10))
    canvas1.create_window(200, 75, window=label2)
    entry1 = tk.Entry(root)
    canvas1.create_window(200, 125, window=entry1)

    def startgame():
        size = int(entry1.get())
        game = cls(size)
        root.destroy()
        game.window.mainloop()

    button1 = tk.Button(text='Lets Play', command=startgame, bg='brown', fg='white',
                        font=('helvetica', 9, 'bold'))
    canvas1.create_window(200, 175, window=button1)
    root.mainloop()


if __name__ == '__main__':
    main(MineSweeperInteractiveGUI)