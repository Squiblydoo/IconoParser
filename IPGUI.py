## UI Libraries
from tkinter import *
from tkinter import ttk
import tkinter.scrolledtext as st
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog

from PIL import Image, ImageTk

#IconoParser Pluggins
import IconoParserGUI
import sceneParserGUI
        
class main_window(TkinterDnD.Tk):
    
    def __init__(self):
        TkinterDnD.Tk.__init__(self)
        self.title("IPGUI")
        self.geometry("800x600")
        self.resizable(False, False)
        self.menubar = Menu(self)
        self.config(menu=self.menubar)
        self.filemenu = Menu(self.menubar, tearoff=0)

        self.filemenu.add_command(label="Open Text Editor", command=self.open_text_editor)
        self.filemenu.add_command(label="Open Cut Scene Editor", command=self.open_cut_scene_editor)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.robin_image = ImageTk.PhotoImage(Image.open("Robin.png"))
        robin_label = Label(self, image=self.robin_image)
        robin_label.pack()
        self.label = Label(self, text="Welcome to IconoParser. Please select an option below.")
        self.label.pack()
        self.button_frame = Frame(self)
        self.button_frame.pack()
        self.button_editor = Button(self.button_frame, text="Open Text Editor (Modify game text)", command=self.open_text_editor)
        self.button_editor.pack()
        self.button_cut_scene = Button(self.button_frame, text="Open Cut Scene Editor (Modify cut scenes)", command=self.open_cut_scene_editor)
        self.button_cut_scene.pack()


    def open_text_editor(self):
        root = IconoParserGUI.main_window()
        root.mainloop()

    def open_cut_scene_editor(self):    
        root = sceneParserGUI.main_window()
        root.mainloop()        

    


def main():
    root = main_window()
    root.mainloop()

if __name__== "__main__":
    main()