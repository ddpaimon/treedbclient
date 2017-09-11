from tkinter import *
from main_window import MainWindow



if __name__ == "__main__":
    root = Tk()
    root.columnconfigure(0, weight=1)
    root.columnconfigure(2, weight=1)
    root.rowconfigure(0, weight=1)
    m = MainWindow(root)
    root.mainloop()
