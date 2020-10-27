import itertools
import random
import sys
import tkinter as tk
import math
import matplotlib.pyplot as plt
import datetime as t

# defaults to 1000, recursive AI might need more (e.g. 40x40 game)
sys.setrecursionlimit(100000)


class MineSweeper2(object):
    """
    In this class, Actual computation and minesweeper generation takes place
    This class creates the basic layout of the minesweeper board using the constructor. It checks if the opened cell is
    safe (S) or a mine (M) and updates the information for each cell accordingly, until all the cells are opened.
    """

    # Constructor with 2 arguments, size of minesweeper and the mode
    def __init__(self, size, mdensity, mode):
        self.size = size
        self.mode = mode
        self.mdensity = mdensity

        # Creates the minesweeper board
        self.cells = set((x, y)
                         for x in range(self.size)
                         for y in range(self.size))

        # Getting Number of mines
        mines_number = self.getmines()
        self._mines = set()
        # Setting mines at random location
        while len(self._mines) < mines_number:
            self._mines.add((random.randrange(size),
                             random.randrange(size)))

        # For each square, gives the set of its neighbours
        # ni = not identified
        # neighbour =  List of neighbors
        # neighbours =  Length of neighbors
        # Status = Status of cell(It can be C= Covered, M= Mined, S= Safe)
        # Clue = Provides Number of mines around specific location
        self.data = {}  # data to keep track of required parameters
        for (x, y) in self.cells:  # for all the cells in the board, get their neighbors and update each cell's data
            neighbour = self.getneighbour(x, y)
            self.data[x, y] = {"neighbour": neighbour, "neighbours": len(neighbour), "status": "C", "clue": "ni"}
        # Environment data:
        self.empty_remaining = size * size - mines_number  # number of non-mines
        # Maintain list of open cells.
        self.opened = set()
        # flagged the identified mine.
        self.flagged = set()
        # Maintain list of safe cells to generate hints.
        self.safe = []
        # Keep track of solved data after identifying
        self.solved = set()
        # If it was a mine, it will be 'mine' instead of a number.
        self.mines_busted = set()

    def open(self, xy):
        """
        Opens the cell at x, y location and checks if it is a mine or safe
        """
        if xy in self.opened:
            return

        self.opened.add(xy)  # add to the list of opened cells
        if xy in self._mines:  # if mine, update status to M
            self.mines_busted.add(xy)
            self.data.get(xy)["status"] = "M"
        else:
            # Updating the clue
            self.data.get(xy)["status"] = "S"  # otherwise update status as safe
            # Updating clue based on mines found in neighbors
            self.data.get(xy)["clue"] = len(self.data[xy].get("neighbour") & self._mines)
            # Reducing the number of empty mines
            self.empty_remaining -= 1  # decrease number of non-mines by 1
            # Checking the condition of winning
            if self.empty_remaining <= 0 and self.mode == "T":
                self.win()

    def flag(self, xy):
        """
        function to flag (mark) the cell denoted by xy
        """
        self.flagged.add(xy)

    def getneighbour(self, x, y):
        """
        returns the list of neighbors for the cell (x, y)
        """
        neigh = set((nx, ny) for nx in [x - 1, x, x + 1] for ny in [y - 1, y, y + 1] if (nx, ny) != (x, y) if
                    (nx, ny) in self.cells)
        return neigh

    def getmines(self):
        """
        returns the number of mines based on the user input size of the minesweeper board
        """
        return math.floor(self.mdensity * (self.size ** 2))

    def constraintsolver(self):
        listconst = self.createconstraint()
        if listconst:
            listconst = self.trivialcase(listconst)
            listconst = self.subtractconstraint(listconst, 0)
        return self.generatehint()

    def createconstraint(self):
        """
        updates the constraint for the cells in the board
        """
        listconst = []
        # for all the cells in the board except the busted mines and flagged cells
        for (x, y) in (self.cells - self.mines_busted - self.flagged):
            if self.data.get((x, y)).get("clue") != "ni":  # if the clue for the cell is not ni (not identified)
                # List of hidden cells around x, y
                hiddenlist = set()
                mine = 0
                # List of mine cells around x, y
                # Iterating over each neighbor of x, y to update the above mentioned list
                for n in self.data.get((x, y)).get("neighbour"):
                    if self.data.get(n).get("status") == "C":
                        hiddenlist.add(n)
                    elif self.data.get(n).get("status") == "M":  # if the cell is a mine, add to minelist
                        mine += 1  # update number of mines detected
                if hiddenlist and {"const": sorted(list(hiddenlist)),
                                   "val": self.data.get((x, y)).get("clue") - mine} not in listconst:
                    listconst.append(
                        {"const": sorted(list(hiddenlist)), "val": self.data.get((x, y)).get("clue") - mine})
                else:
                    self.solved.add((x, y))
        # Based on updated information, calling method to generate hint
        return listconst

    def trivialcase(self, lc):
        trivial = []
        s = set()
        f = set()
        for c in lc:
            if len(c.get("const")) == c.get("val"):
                for i in c.get("const"):
                    f.add(i)
                    self.data.get(i)["status"] = "M"
                    self.flag(i)
                trivial.append(c)
            elif c.get("val") == 0:
                for i in c.get("const"):
                    s.add(i)
                    self.data.get(i)["status"] = "S"
                    if i not in self.opened and i not in self.safe:
                        self.safe.append(i)
                trivial.append(c)
        [lc.remove(i) for i in trivial]
        if len(s) != 0 or len(f) != 0 and lc:
            for c in lc:
                for sa in s:
                    if sa in c.get("const"):
                        c.get("const").remove(sa)
                for fl in f:
                    if fl in c.get("const"):
                        c.get("const").remove(fl)
                        c["val"] = c.get("val") - 1
            lc = [i for n, i in enumerate(lc) if i not in lc[n + 1:]]
            lc = self.trivialcase(lc)
        return lc

    def subtractconstraint(self, lc, updates):
        for x, y in itertools.combinations(lc, 2):
            S1 = set(x.get("const"))
            S2 = set(y.get("const"))
            if S1.intersection(S2):
                if x.get("val") > y.get("val"):
                    self.updateconst(x, y, lc, updates)

                elif x.get("val") < y.get("val"):
                    self.updateconst(y, x, lc, updates)
            else:
                if S2.issubset(S1) and len(S2) > y.get("val"):
                    updates = self.updateconst(x, y, lc, updates)
                elif S1.issubset(S2) and len(S1) > x.get("val"):
                    updates = self.updateconst(y, x, lc, updates)
        if updates != 0:
            lc = self.trivialcase(lc)
            lc = self.subtractconstraint(lc, 0)
        return lc

    def updateconst(self, maxs, mins, uc, updates):
        maxset = set(maxs.get("const"))
        minset = set(mins.get("const"))
        pos = list(maxset - minset)
        neg = list(minset - maxset)
        if len(pos) == maxs.get("val") - mins.get("val"):
            if {"const": sorted(pos), "val": maxs.get("val") - mins.get("val")} not in uc:
                uc.append({"const": sorted(pos), "val": maxs.get("val") - mins.get("val")})
                updates = updates + 1
            if {"const": sorted(neg), "val": 0} not in uc and len(neg) != 0:
                uc.append({"const": sorted(neg), "val": 0})
                updates = updates + 1
        return updates

    def generatehint(self):
        """
        function to generate a hint for the game to proceed
        """

        # If safe list is not empty, give first element in safe list as a hint
        if self.safe:  # if safe
            step = self.safe.pop(0)  # remove the first element from the list
        else:
            # get remaining cells excluding the opened and flagged cells
            permittedsteps = self.cells - self.opened - self.flagged  # get remaining cells excluding the opened and flagged cells
            step = random.choice(list(permittedsteps))  # from these cells, choose one randomly

        return step

    def win(self):
        """
        Display number of mines tripped (busted)
        """
        # Total number of mines busted by user while playing
        if self.mines_busted:
            print("You finished with %s tripped  mines :: Total numbers of mine were %s"
                  % (len(self.mines_busted), len(self._mines)))
        else:
            print("You won without tripping any mines :-)")


class MineSweeper2Play(MineSweeper2):
    """
    Play the Minesweeper game!
    This class automates the playing of minesweeper based on hints for the above class using the Tkinter library.
    Based on 'Test' it also displays the results
    """

    # Constructor
    def __init__(self, *args, **kw):
        # Calling MAIN CLASS
        MineSweeper2.__init__(self, *args, **kw)  # use the __init__ function from the above class to create the board

    def letsplay(self):
        """
        plays the game; starts timer and runs until all cells are opened and returns the time taken in microseconds
        """
        start_time = t.datetime.now()  # Noting time taken to complete
        while self.empty_remaining > 0:  # until all cells are opened
            step = self.constraintsolver()
            self.open(step)
        return len(self._mines), len(self.flagged), len(self.mines_busted), (t.datetime.now() - start_time).microseconds

    def display(self):
        """
        displays the GUI for the game, using the Tkinter library
        """

        # Creating window and adding properties
        window = tk.Tk()
        table = tk.Frame(window)
        table.pack()
        squares = {}

        # Build buttons
        for xy in self.cells:
            squares[xy] = button = tk.Button(table, padx=0, pady=0)
            row, column = xy
            # expand button to North, East, West, South
            button.grid(row=row, column=column, sticky="news")

            # Scaling the size of button based on the sie of minesweeper
            scale = math.floor(50 // (1 if self.size // 10 == 0 else self.size // 10))
            table.grid_columnconfigure(column, minsize=scale)
            table.grid_rowconfigure(row, minsize=scale)
            # needed to restore bg to default when unflagging
            self.refresh(xy, squares)

        # if the board is cleared without tripping any mines
        if self.mines_busted == 0:
            window.title("You won without tripping any mines :-)")
        else:  # otherwise, print number of mines tripped
            window.title("You finished with %s tripped mines and Total number of mines were %s" % (
                len(self.mines_busted), len(self._mines)))
        window.mainloop()

    def refresh(self, xy, squares):
        """
        Update the GUI for given square
        """
        button = squares[xy]

        # Fetching and setting visual data for the cell
        text, fg, bg = self.getvisualdataforcell(xy)
        button.config(text=text, fg=fg, bg=bg)

        # Updating information for button if it is opened
        if xy in self.opened:
            button.config(relief=tk.SUNKEN)

    def getvisualdataforcell(self, xy):
        """
        Fetching Visual data for cell based on its status
        """
        # If cell is opened and it is mine, it will be marked as a mine. Else, the clue will be displayed.
        if xy in self.opened:
            if xy in self._mines:
                return u'\N{SKULL AND CROSSBONES}', None, 'red'

            mn = self.data.get(xy).get("clue")
            if mn >= 0:
                # Standard minesweeper colors
                fg = {0: 'black', 1: 'blue', 2: 'dark green', 3: 'red',
                      4: 'dark blue', 5: 'dark red',
                      }.get(mn, 'black')
                return str(mn), fg, 'white'

        # if xy is in flagged
        elif xy in self.flagged:
            # display a white flag
            return u'\N{WHITE FLAG}', None, 'green'
        # For remaining cells, they will be just green
        elif xy in self._mines:
            self.flagged.add(xy)
            return u'\N{WHITE FLAG}', None, 'green'
        else:
            # display green cell
            return '', None, 'green'


def disp_data(data, varnames, xlable, ylabel, title):
    """
    This method is used to visualize data by displaying the graph
    :param data: data to be plotted
    :param varnames: variables to be plotted
    :param xlable: x label
    :param ylabel: y label
    :param title: title
    """
    fig = plt.figure()  # Initializing figure
    ax1 = fig.add_subplot()
    ax1.set_xlabel(xlable)
    ax1.set_ylabel(ylabel)
    ax1.set_title(title)
    thiningfactors = list(data.keys())

    for var in varnames:
        success = list(map(lambda key: round(data.get(key).get(var)), data.keys()))
        ax1.plot(thiningfactors, success, label=var)
    ax1.legend(title="Mines")
    ax1.grid(True)


def main(cls):
    """
    Main function to either play the Minesweeper game, or analyze the performance of the player
    """
    # This is used to either analyze the basic minesweeper board or test it
    Mode = input("Select the mode (Analysis/Test) ")
    # if mode is Analysis
    if "analysis".casefold().__eq__(Mode.casefold()):
        result = {}
        sizes = [30, 40, 50, 60]
        mdenisty = 0.40
        iterations = 5
        print("Generating Data")
        # for the sizes defined above
        for size in sizes:
            # Avg total number of mines
            meanmines = 0
            # Avg total number of flagged mines
            meanflagged = 0
            # Avg total number of busted mines
            meanbusted = 0
            # Avg time taken
            meantimetaken = 0
            # Plays the game "iterations" number of times
            for i in range(0, iterations):
                game = cls(size, mdenisty, "A")
                tmines, tflagged, tbusted, timetaken = game.letsplay()
                # Update meanmines, meanflagged, meanbusted, meantimetaken accordingly
                meanmines += tmines
                meanflagged += tflagged
                meanbusted += tbusted
                meantimetaken += round(timetaken / (10 ** 3), 4)
            result[size] = {"meanmines": math.floor(meanmines / iterations),
                            "meanflagged": math.floor(meanflagged / iterations),
                            "meanbusted": math.floor(meanbusted / iterations),
                            "meantimetaken": math.floor(meantimetaken / iterations)}
        print("Plotting Data")
        # displays the graph for the parameters mentioned above
        disp_data(result, ["meanmines", "meanflagged", "meanbusted"], "Sizes", "Numbers", "Size vs efficiency")
        disp_data(result, ["meantimetaken"], "Sizes", "Time( MilliSeconds )", "Size vs Time taken")
        plt.show()
    else:  # if the mode is Test
        # Ask user for input size
        size = int(input("Enter the size "))
        mdensity = float(input("Enter the mine density (0 - 1) "))
        game = cls(size, mdensity, "T")
        # Play the game and display the board
        game.letsplay()
        game.display()


if __name__ == '__main__':
    # Runs the main function
    main(MineSweeper2Play)
