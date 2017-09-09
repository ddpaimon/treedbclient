from tkinter import *


class PopupWindow(object):
    value = ''

    def __init__(self, root, text=''):
        top = self.top = Toplevel(root)
        self.l = Label(top, text="Enter node name")
        self.l.pack()
        self.entry = Entry(top)
        self.entry.insert(0, text)
        self.entry.select_range(0, 'end')
        self.entry.pack()
        self.okButton = Button(top, text='Ok', command=self.cleanup)
        self.okButton.pack()
        self.entry.focus()

    def cleanup(self):
        self.value = self.entry.get()
        self.top.destroy()
