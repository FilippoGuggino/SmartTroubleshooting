"""
This module provides the GUI for the technician

Author: Leonardo Cecchelli
"""

from tkinter import Label, Listbox, Tk, Button, Text, END
from tkinter import messagebox
from smart_troubleshooting.technical_support_system.request_manager import RequestManager
from smart_troubleshooting.technical_support_system.solution_organizer import SolutionOrganizer


def count(letters):
    """
    Utility function that counts the number of words from a given input
    """
    text = letters.get('1.0', 'end-1c')
    rows = text.count('\n')
    letters = len(text) - rows
    return letters


class MainMenu:
    """
    This class implements the window and the widgets for the GUI
    """

    def __init__(self):
        """
        Initialize all the interface and session state variables
        """
        # interface variables
        self.enumerated_sol = []
        self.window = Tk()
        self.request_manager = RequestManager()
        self.sol_listbox = Listbox(self.window, width=60, height=5, font=('times', 13))
        self.man_sol_btn = Button(self.window, text="Insert solution", bg="orange", fg="white",
                                  command=lambda: self.insert_man_sol(self.man_sol_desc))
        self.man_sol_desc = Text(height=3, width=100, wrap="word")
        self.man_sol_lbl = Label(self.window, text="Insert your own solution",
                                 font=("Arial Bold", 13))
        self.sol_btn = Button(self.window, text="Confirm solution", bg="orange",
                              fg="white", command=self.confirm_sol)
        self.sol_lbl = Label(self.window, text="Select your solution from the list",
                             font=("Arial Bold", 13))
        self.prob_btn = Button(self.window, text="Insert problem", bg="orange",
                               fg="white",
                               command=lambda: self.insert_problem(self.prob_desc))
        self.prob_desc = Text(height=5, width=100, wrap="word")
        self.prob_lbl = Label(self.window, text="Insert a new problem",
                              font=("Arial Bold", 13))
        self.sol_organizer = SolutionOrganizer()
        self.probl_status = Label(self.window, text="PROBLEM STATUS: NO PROBLEM INSERTED",
                                  fg="red", font=("Arial Bold", 13, 'bold'))
        # session variables
        self.problem_inserted = False
        self.no_solutions = True
        self.empty_description = True
        self.empty_solution = True
        self.presented_solutions = 0
        self.problem_desc_ins = ""

    # utility functions
    def change_prob_status(self):
        """
        Utility function used to change the color of the problem status banner to green
        """
        self.probl_status.configure(text="PROBLEM STATUS: PROBLEM INSERTED", fg="green",
                                    font=("Arial Bold", 13, 'bold'))

    def display_solutions(self, solutions):
        """
        Displays all solutions by manipulating the listbox
        :param solutions: The array of solution descriptions
        """
        index = 1

        already_added = set()
        for sol in solutions:
            if sol in already_added:
                # skip if this solution has been already shown
                continue
            else:
                already_added.add(sol)

            self.enumerated_sol.append({'number': index, 'solution': sol})
            index = index + 1
        self.sol_listbox = Listbox(self.window, width=60, height=5, font=('times', 13))
        self.sol_listbox.place(x=32, y=90)

        for items in self.enumerated_sol:
            self.presented_solutions = self.presented_solutions + 1
            self.sol_listbox.insert(END, items['solution'])
            self.sol_listbox.grid(column=0, row=7, padx=5, pady=10, ipady=3)
            self.sol_lbl.destroy()
        self.no_solutions = False

    def clean_session(self):
        """
        Resets all the session state variables in order to receive a new problem to troubleshoot
        """
        self.problem_inserted = False
        self.no_solutions = True
        self.empty_description = True
        self.empty_solution = True
        self.presented_solutions = 0
        self.enumerated_sol = []
        self.request_manager.flush_solution_responses()
        self.sol_organizer.clean_solutions()
        self.sol_lbl = Label(self.window, text="No solution available at the moment",
                             font=("Arial Bold", 10))
        self.sol_lbl.grid(column=0, row=7, padx=5, pady=5, ipady=3)
        self.probl_status.configure(text="PROBLEM STATUS: PROBLEM INSERTED", fg="red",
                                    font=("Arial Bold", 13, 'bold'))
        self.sol_listbox.destroy()

    # input handlers
    def insert_problem(self, prob_desc):
        """
        Sends a new problem description to the solution organizer module
        :param prob_desc: The problem description inserted by the user
        """
        word_num = count(prob_desc)
        if word_num == 0:
            self.empty_description = True
            messagebox.showinfo('Empty problem description', 'Please insert a problem description')
            return
        if self.problem_inserted:
            messagebox.showinfo('Attention', 'You have already inserted a problem')
            return
        self.empty_description = False
        self.change_prob_status()
        self.problem_inserted = True
        self.problem_desc_ins = self.prob_desc.get("1.0", END)
        self.problem_desc_ins = self.problem_desc_ins.replace('\n', '')
        solutions = self.sol_organizer.compute_solution_list(self.problem_desc_ins)
        if not solutions:
            self.no_solutions = True
            return
        self.display_solutions(solutions)

    def insert_man_sol(self, man_sol_desc):
        """
        Sends to the solved repository the data about the manual solution inserted by the user
        :param man_sol_desc: The manual solution inserted by the user
        """
        word_num = count(man_sol_desc)
        if word_num == 0:
            self.empty_solution = True
            messagebox.showinfo('Empty solution description',
                                'Please insert a solution description')
            return
        if not self.problem_inserted:
            messagebox.showinfo('No problem detected', 'Please insert a problem first')
            return
        # insert solution into json
        man_sol = self.man_sol_desc.get("1.0", END)
        man_sol = man_sol.replace('\n', '')
        self.request_manager.add_manual_solution(self.problem_desc_ins, man_sol,
                                                 self.presented_solutions)
        self.clean_session()
        messagebox.showinfo('Success', 'Solution sent!')

    def confirm_sol(self):
        """
        Sends the data about the selected solution from the listbox
        """
        if self.no_solutions:
            if not self.problem_inserted:
                messagebox.showinfo('No problem detected', 'Please insert a problem first')
            else:
                messagebox.showinfo('No solutions available',
                                    'The system was unable to find a solution to your problem')
                self.clean_session()
                return
        else:
            # insert problem into json
            sol = self.sol_listbox.get(self.sol_listbox.curselection())
            index = 1
            for solution_found in self.enumerated_sol:
                if solution_found['solution'] == sol:
                    index = solution_found['number']
                    break
            self.request_manager.add_select_solution(self.problem_desc_ins, sol, index,
                                                     self.presented_solutions)
            self.clean_session()
            messagebox.showinfo('Success', 'Solution sent!')

    def start_interface(self):
        """
        Spawns all the necessary widgets by adjusting their positions
        and style settings
        """
        self.window.title("Smart Troubleshooting User Interface")
        mainmenu_lbl = Label(self.window, text="Smart Troubleshooting - Main Menu",
                             font=("Arial Bold", 20, 'bold'))
        mainmenu_lbl.grid(column=0, row=0)

        self.probl_status.grid(column=0, row=2, padx=5, pady=10, ipady=3)

        # Insert problem option
        self.prob_lbl.grid(column=0, row=3, padx=5, pady=5, ipady=3)
        self.prob_desc.grid(column=0, row=4, padx=5, pady=5, ipady=3)
        self.prob_btn.grid(column=1, row=5, padx=5, pady=5, ipady=3)

        # View solution list and select one option
        self.sol_lbl.grid(column=0, row=6, padx=5, pady=5, ipady=3)
        self.sol_lbl = Label(self.window, text="No solution available at the moment",
                             font=("Arial Bold", 10))
        if self.no_solutions:
            self.sol_lbl.grid(column=0, row=7, padx=5, pady=5, ipady=3)
        else:
            self.sol_listbox.grid(column=0, row=7, padx=5, pady=10, ipady=3)
            # print solutions
        self.sol_btn.grid(column=1, row=8, padx=5, pady=5, ipady=3)

        # Insert manual solution option
        self.man_sol_lbl.grid(column=0, row=9, padx=5, pady=5, ipady=3)
        self.man_sol_desc.grid(column=0, row=10, padx=5, pady=5, ipady=3)
        self.man_sol_btn.grid(column=1, row=11, padx=5, pady=5, ipady=3)

        self.window.mainloop()
