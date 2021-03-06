import itertools
import random
import sys
import tkinter as tk
import math
import matplotlib.pyplot as plt
import datetime as t

# increasing recusrion limit
sys.setrecursionlimit(100000)


class MineSweeper2(object):
    """
    In this class, Actual computation and minesweeper generation takes place
    This class creates the basic layout of the minesweeper board using the constructor. It checks if the opened cell is
    safe (S) or a mine (M) and updates the information for each cell accordingly, until all the cells are opened.
    """

    # Constructor with 3 arguments, size of minesweeper, mine density and the mode to play in
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
        if xy in self.opened:       # if the cell id already opened, do nothing
            return

        self.opened.add(xy)  # add to the list of opened cells
        if xy in self._mines:  # if mine, update status to M
            self.mines_busted.add(xy)       # add cell xy to the busted mines list
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
        self.flagged.add(xy)        # add to the flagged cells list

    def getneighbour(self, x, y):
        """
        returns the list of neighbors for the cell (x, y)
        """
        # check to the left and right of that cell and return those cells
        neigh = set((nx, ny) for nx in [x - 1, x, x + 1] for ny in [y - 1, y, y + 1] if (nx, ny) != (x, y) if
                    (nx, ny) in self.cells)
        return neigh

    def getmines(self):
        """
        returns the number of mines based on the user input size of the minesweeper board
        """
        # Number of mines determined by the mine density times the size of the board
        return math.floor(self.mdensity * (self.size ** 2))

    def constraintsolver(self):
        """
        returns the hint generated by solving the constraint equations
        """
        listconst = self.createconstraint()     # get the constraint equations for the cells in the board
        if listconst:
            listconst = self.trivialcase(listconst)
            listconst = self.subtractconstraint(listconst, 0)   # subtract the constraint equations to get a hint
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
                    if self.data.get(n).get("status") == "C":       # if the cell is covered, add to the hidden list
                        hiddenlist.add(n)
                    elif self.data.get(n).get("status") == "M":  # if the cell is a mine, add to minelist
                        mine += 1  # update number of mines detected
                # if cells exist in the hidden list and if the constraint doesn't already exist
                if hiddenlist and {"const": sorted(list(hiddenlist)),
                                   "val": self.data.get((x, y)).get("clue") - mine} not in listconst:
                    # add the constraint to the listconst
                    listconst.append(
                        {"const": sorted(list(hiddenlist)), "val": self.data.get((x, y)).get("clue") - mine})
                else:
                    # add to the solved list
                    self.solved.add((x, y))
        # return the list of constraints
        return listconst

    def trivialcase(self, lc):
        """
        function to solve the constraint equations using the trivial case
        :param lc: list of constraints
        :return:
        """
        trivial = []
        s = set()
        f = set()
        # run for all the constraints
        for c in lc:
            # if the number of variables in the constraint is the same as the constraint value
            if len(c.get("const")) == c.get("val"):
                # add all the constraint variables to flagged list
                for i in c.get("const"):
                    f.add(i)
                    self.data.get(i)["status"] = "M"        # and update their status to be a mine
                    self.flag(i)                            # and flag them
                trivial.append(c)       # add this constraint to the trivial case list
            elif c.get("val") == 0:     # if the value of the constraint is 0
                for i in c.get("const"):
                    s.add(i)        # add all the constraint variables to safe list
                    self.data.get(i)["status"] = "S"        # update status to be safe
                    if i not in self.opened and i not in self.safe:
                        # add to safe list only if that variable (cell) is not opened and doesn't already exist in the
                        # safe list
                        self.safe.append(i)
                trivial.append(c)       # add this constraint to the trivial case list
        [lc.remove(i) for i in trivial]
        # if the length of the safe and flagged sets are not 0 and lc is not empty
        if len(s) != 0 or len(f) != 0 and lc:
            # for all the constraints
            for c in lc:
                for sa in s:
                    if sa in c.get("const"):        # if the safe set elements exist in the constraints
                        c.get("const").remove(sa)   # remove that variable from the constraint
                # for all the flagged variables
                for fl in f:
                    # if the flagged variable exists in the constraint equation
                    if fl in c.get("const"):
                        c.get("const").remove(fl)       # remove that flagged element from the constraint
                        c["val"] = c.get("val") - 1     # decrement the constraint value by 1
            # update the list of constraints and solve using the trivial case
            lc = [const for index, const in enumerate(lc) if const not in lc[index + 1:] and const.get('const')]
            lc = self.trivialcase(lc)
        return lc

    def subtractconstraint(self, lc, updates):
        """
        function to subtract the constraint equations
        """
        # get all possible combinations in pairs
        for x, y in itertools.combinations(lc, 2):
            S1 = set(x.get("const"))        # assign 1 constraint equation to S1
            S2 = set(y.get("const"))        # assign another constraint equation to S2
            if S1.intersection(S2):     # if S1 and S2 have common elements
                if x.get("val") > y.get("val"):     # and if S1's constraint value is greater than S2's constraint value
                    updates = self.updateconst(x, y, lc, updates)   # update the constraint accordingly

                elif x.get("val") < y.get("val"):   # if S2's constraint value is greater than S1's constraint value
                    updates = self.updateconst(y, x, lc, updates)       # update the constraint accordingly
            else:       # if S2 and S1 don't have any common elements
                # if S2 exists in S1 and number of constraint variables in S2 is greater than S2's constraint value
                if S2.issubset(S1) and len(S2) > y.get("val"):
                    updates = self.updateconst(x, y, lc, updates)   # update the constraint accordingly
                # if S1 exists in S2 and number of constraint variables in S1 is greater than  S1's constraint value
                elif S1.issubset(S2) and len(S1) > x.get("val"):
                    updates = self.updateconst(y, x, lc, updates)       # update the constraint accordingly
        # if updates are made
        if updates != 0:
            lc = self.trivialcase(lc)       # update using the trivial case
            lc = self.subtractconstraint(lc, 0)     # and subtract the constraints
        return lc       # return the resulting list of constraint equations

    def updateconst(self, maxs, mins, uc, updates):
        """
        function to update the constraints
        """
        maxset = set(maxs.get("const"))
        minset = set(mins.get("const"))
        pos = list(maxset - minset)     # get the list of variables that are positive, after subtracting
        neg = list(minset - maxset)     # get the list of variables that are negative after subtracting
        # if the length of positive variables is equal to the difference between max's and min's value
        if len(pos) == maxs.get("val") - mins.get("val"):
            # if the constraint with positive variables and value being the difference between max and min's value
            # doesn't exist in uc
            if {"const": sorted(pos), "val": maxs.get("val") - mins.get("val")} not in uc:
                # add it to uc
                uc.append({"const": sorted(pos), "val": maxs.get("val") - mins.get("val")})
                updates = updates + 1       # increment number of updates
            # if the constraint with negative variables and value 0 doesn't exist in uc and number of negative variables
            # is not 0
            if {"const": sorted(neg), "val": 0} not in uc and len(neg) != 0:
                uc.append({"const": sorted(neg), "val": 0})     # add it to uc
                updates = updates + 1               # increment number of updates
        # if number of negative variables is 0 and max's and min's value are equal and doesn't exist in uc
        elif len(neg) == 0 and maxs.get("val") == mins.get("val") and len(pos) > 0:
            # if the constraint with pos variables and value being difference of maxs and mins doesn't exist in uc
            if {"const": sorted(pos), "val": maxs.get("val") - mins.get("val")} not in uc:
                uc.append({"const": sorted(pos), "val": 0})     # add that constraint to uc
                updates = updates + 1           # and increment the number of updates
        return updates      # return number of updates

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

        return step     # return the next step to follow, the hint

    def win(self):
        """
        Display final score after game is completed. final score is #mines flagged/# mines
        """
        # Total number of mines busted by user while playing
        if self.mines_busted:
            print("You finished with %s tripped mines. Final score %s" % (
                len(self.mines_busted), len(self.flagged) / len(self._mines)))


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

        # Creating window and adding properties to it
        window = tk.Tk()
        table = tk.Frame(window)
        table.pack()
        squares = {}

        # Build buttons
        for xy in self.cells:       # create buttons for all the cells in the board
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

        # Displaying final score
        window.title("You finished with %s tripped mines. Final score %s" % (
            len(self.mines_busted), len(self.flagged) / len(self._mines)))
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
            button.config(relief=tk.SUNKEN)     # set the cell to be sunken once it is opened

    def getvisualdataforcell(self, xy):
        """
        Fetching Visual data for cell based on its status
        """
        # If cell is opened and it is a mine, it will be marked as a mine. Else, the clue will be displayed.
        if xy in self.opened:
            if xy in self._mines:
                return u'\N{SKULL AND CROSSBONES}', None, 'red'

            mn = self.data.get(xy).get("clue")
            if mn >= 0:     # if the clue is greater than or equal to 0
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
    # using the matplotlib library to plot the graphs
    fig = plt.figure()  # Initializing figure
    ax1 = fig.add_subplot()
    ax1.set_xlabel(xlable)
    ax1.set_ylabel(ylabel)
    ax1.set_title(title)
    thiningfactors = list(data.keys())      # get the keys from the data dictionary

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
        # initialize the parameters for the board
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
                # get the total number of mines, flagged mines, busted mines and time taken once th game is completed
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
        # game.display()


if __name__ == '__main__':
    # Runs the main function
    main(MineSweeper2Play)
