## UI Libraries
from tkinter import *
from tkinter import ttk
import tkinter.scrolledtext as st
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
import re

#IconoParser Pluggins
import iconoParser.helperDictionaries as helperDict
import cutsceneParse
import iconoParser.backtoCutSceneFormat

class main_window(TkinterDnD.Tk):
    
        
    def __init__(self):
        TkinterDnD.Tk.__init__(self)

        # Basic Window Configuration
        self.geometry("660x750")
        self.title("IconoParser")
        style = ttk.Style()
        style.configure("Treeview",
                        background="white")
        style.map('Treeview',
                background=[('selected', 'blue')])
        self.stored_frames = []

        instructionLabel = Label(self, text="Use menu to open a file.\n'Function' names are only a guide.\n'Type 6' items are empty, change to 'type 2' to if adding a value.\nLook at multiple files to get an idea of how they work.")
        instructionLabel.pack()
        menu = Menu(self)
        self.config(menu=menu)
        file_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File", command=self.openFile)
        file_menu.add_command(label="Export", command=self.exportFile)
        file_menu.add_command(label="Close File", command=self.closeFile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        help_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Getting Started", command=self.starting_advice)
        help_menu.add_command(label="I broke something!", command=self.broken_help)
        help_menu.add_command(label="About", command=self.about)

        
        treeFrame = Frame(self)
        treeFrame.pack(pady=20)
        self.frame_table = ttk.Treeview(treeFrame, height=15)
        
        # self.frame_table = ttk.Treeview(treeFrame, yscrollcommand=treeScroll.set, height=15)
        # treeScroll = Scrollbar(treeFrame)
        # treeScroll.pack(side=RIGHT, fill=Y)
        # treeScroll.config(command=self.frame_table.yview)
        

        self.frame_table["columns"] = ("1", "2", "3", "4", "5")
        self.frame_table.column("#0", width=0, stretch=NO)
        self.frame_table.column("1", width=0,  stretch=NO)
        self.frame_table.column("2", anchor=W, width=40)
        self.frame_table.column("3", width=0, stretch=NO)
        self.frame_table.column("4", anchor=W, width=380)
        self.frame_table.column("5", width=80, stretch=NO)
        
        self.frame_table.heading("1", text="1")
        self.frame_table.heading("2", text="Type")
        self.frame_table.heading("3", text="3")
        self.frame_table.heading("4", text="Value")
        self.frame_table.heading("5", text="Encoding")
        self.frame_table.bind("<Double-1>", self.doubleClickRecord)
        self.frame_table.grid(row=0, column=1, rowspan=15, sticky="nsew")

        self.label_table = ttk.Treeview(treeFrame, height=15)
        self.label_table["columns"] = ("1")
        self.label_table.column("#0", width=0, stretch=NO)
        self.label_table.column("1", anchor=W, width=80)
        self.label_table.grid(row=0, column=0, rowspan=15, sticky="nsew")
        self.label_table.heading("1", text="Function")
        self.label_table.insert(parent="", index=0, values=("N/A"))
        self.label_table.insert(parent="", index=1, values=("Time"))
        self.label_table.insert(parent="", index=2, values=("Duration"))
        self.label_table.insert(parent="", index=3, values=("?"))
        self.label_table.insert(parent="", index=4, values=("?"))
        self.label_table.insert(parent="", index=5, values=("Target"))
        self.label_table.insert(parent="", index=6, values=("Target_#"))
        self.label_table.insert(parent="", index=7, values=("Animation"))
        self.label_table.insert(parent="", index=8, values=("?"))
        self.label_table.insert(parent="", index=9, values=("?"))
        self.label_table.insert(parent="", index=10, values=("?"))
        self.label_table.insert(parent="", index=11, values=("?"))
        self.label_table.insert(parent="", index=12, values=("?"))
        self.label_table.insert(parent="", index=13, values=("?"))
        self.label_table.insert(parent="", index=14, values=("?"))

        navigation_frame = Frame(self)
        navigation_frame.pack()        
        self.frame_number_label = Label(navigation_frame, text="Frame Number: 0")
        self.frame_number_label.grid(row=0, column=0)
        
        self.current_array_index = 0  # Initialize the current array index


        self.go_to_frame_button = Button(navigation_frame, text="Go To >", command=self.go_to_frame)
        self.go_to_frame_button.grid(row=0, column=1, sticky="w")
        self.go_to_frame_entry = Entry(navigation_frame, width=3)
        self.go_to_frame_entry.grid(row=0, column=1, sticky="e")
        self.prev_button = Button(navigation_frame, text="Previous", command=self.display_previous_array)
        self.prev_button.grid(row=0, column=2)
        self.next_button = Button(navigation_frame, text="Next", command=self.display_next_array)
        self.next_button.grid(row=0, column=3)

        self.insert_copy_frame_button = Button(navigation_frame, text="Insert Copy", command=self.insert_copy_frame)
        self.insert_copy_frame_button.grid(row=1, column=2)
        self.insert_new_animation_frame = Button(navigation_frame, text="Insert New Frame", command=self.insert_new_animation_frame)
        self.insert_new_animation_frame.grid(row=1, column=0)
        self.delete_frame_button = Button(navigation_frame, text="Delete Frame", command=self.delete_frame)
        self.delete_frame_button.grid(row=1, column=1)
    
        optionFrame = Frame(self)
        optionFrame.pack()
        modifyFrame = LabelFrame(optionFrame, text="Modify Lines")
        modifyFrame.grid(row=0, column=0, pady=10,padx=10)
        newDialogLabel = Label(modifyFrame, text="Edit Values")
        newDialogLabel.grid(row=0, column=0)
        self.typeValueTextBox = Entry(modifyFrame)
        self.type_label = Label(modifyFrame, text="Type")
        self.type_label.grid(row=2, column=0)
        self.typeValueTextBox.grid(row=2, column=1)
        self.newTextEntry = st.ScrolledText(modifyFrame, width=30, height=5)
        self.newTextEntry_label = Label(modifyFrame, text="Value")
        self.newTextEntry_label.grid(row=3, column=0)
        self.newTextEntry.grid(row=3, column=1)

        save_record = Button(modifyFrame, text="Save", command=self.saveRecord)
        save_record.grid(row=4, column=1)

        export_button = Button(self, text="Export", command=self.exportFile)
        export_button.pack()

        close_button = Button(self, text="Close File", command=self.closeFile)
        close_button.pack()

    def about(self):
        about_window = Toplevel(self)
        about_window.title("About")
        about_window.geometry("400x400")
        about_label = Label(about_window, text="\n\nIconoParser is a tool for editing files in Iconoclasts.\nCreated by Squiblydoo.\nRobin art is by Sho Sakazaki, used with permission.")
        about_label.pack()
        about_window.mainloop()

    def broken_help(self):
        broken_window = Toplevel(self)
        broken_window.title("I broke something!")
        broken_window.geometry("400x400")
        broken_label = Label(broken_window, text="\n\nIf you attempted to edit something and want to\n revert there are two options.\n1) When editing a file a copy is made with '_backup'.\n You can replace the malformed one with this copy.\n The backup is in the same directory as the file you edited.\n2) You can also 'Verify Game Files' in steam to restore \nthe original files. All modified files in the \ngame's directory will be checked and restored.")
        broken_label.pack()

    def starting_advice(self):
        start_window = Toplevel(self)
        start_window.title("Getting Started")
        start_window.geometry("400x400")
        start_label = Label(start_window, text="\n\nTo get started:\n drag and drop a cut scene file onto the window.\nYou can then edit the values in the table.\nWhen you are finished, you can export the file.\nPut the modified file in the game directory to use it.\n \nThese files are normally located as follows:\nWindows:\n C:/Program Files (x86)/Steam/steamapps/common\n/Iconoclasts/data/scene\nMac: \n~/Library/Application Support/Steam/steamapps/common\n/Iconoclasts/data/scene\nLinux: \n~/.steam/steam/steamapps/common\n/Iconoclasts/data/scene")
        start_label.pack()

    def closeFile(self):
        self.stored_frames = []
        self.frame_table.delete(*self.frame_table.get_children())
        self.frame_number_label.config(text="Frame Number: 0")

    def exportFile(self):
        file_path = filedialog.asksaveasfilename()
        convert = iconoParser.backtoCutSceneFormat.guiExport(self.stored_frames)

        FILE_MAGIC = 0x415252312E300F000000
        length_in_bytes = 10
        file_magic_bytes = FILE_MAGIC.to_bytes(length_in_bytes, 'big')
        
        output = file_magic_bytes + convert
        with open(file_path, "wb") as dia_file:
            dia_file.write(output)

    # def insert_new_frame(self):
    #     self.current_array_index += 1
    #     self.stored_frames.insert(self.current_array_index, [])  # Insert an empty frame at the current index
    #     self.update_frame_number_label()
    #     self.frame_table.delete(*self.frame_table.get_children())
    #     self.frame_number_label.config(text=f"Frame Number: {self.current_array_index}")
    def go_to_frame(self):
        self.current_array_index = int(self.go_to_frame_entry.get())
        self.update_frame_number_label()
        self.load_frame_data()

    def insert_new_animation_frame(self):
        self.current_array_index += 1
        self.stored_frames.insert(self.current_array_index, [[1, 0], [1, 2, 2, b'set_time!!!'], [1, 2, 2, b'0'], [1, 2, 2, b'0'], [1, 2, 2, b'0'], [1, 2, 10, b'set_target!!!'], [1, 2, 2, b'set target number!'], [1, 2, 40, b'!Animation,SET_ANIMATION,#NextAnim,0,X,864,Y,1952'], [1, 2, 9, b'\r\r\r\r\r\r\r\r\x00'], [1, 6, '', ''], [1, 6, '', ''], [1, 6, '', ''], [1, 6, '', ''], [1, 6, '', ''], [1, 6, '', ''] ])
        self.update_frame_number_label()
        self.load_frame_data()
        self.frame_number_label.config(text=f"Frame Number: {self.current_array_index}")


    def insert_copy_frame(self):
        self.current_array_index += 1
        self.stored_frames.insert(self.current_array_index, self.stored_frames[self.current_array_index - 1].copy())
        self.update_frame_number_label()
        self.frame_number_label.config(text=f"Frame Number: {self.current_array_index}")

    def delete_frame(self):
        if len(self.stored_frames) > 1:
            self.stored_frames.pop(self.current_array_index)
            self.current_array_index -= 1
            self.update_frame_number_label()
            self.load_frame_data()

        else:
            self.stored_frames = []
            self.frame_table.delete(*self.frame_table.get_children())
            self.frame_number_label.config(text="Frame Number: 0")

    def saveRecord(self):
        selectedRow = self.frame_table.focus()
        textValue = self.frame_table.item(selectedRow, 'values')

        self.frame_table.item(selectedRow, values=(textValue[0], self.typeValueTextBox.get(), textValue[2], self.newTextEntry.get("0.0", 'end'), textValue[4]))
        self.typeValueTextBox.delete(0, END)
        self.newTextEntry.delete("0.0", "end")
        self.stored_frames[self.current_array_index] = []
        for item in self.frame_table.get_children():
            values = self.frame_table.item(item, 'values')
            # Check if the first value is '1' and the second value is '0'
            if values[0] == '1' and values[1] == '0':
                # Convert the 2-value slice to a list of bytes and append
                self.stored_frames[self.current_array_index].append([int(value) for value in values[:2]])
            else:
                # Convert the entire values tuple to a list of bytes and append
                value_0_int = int(values[0])
                value_1_int = int(values[1])

                if values[3] != '':
                    value_3 = values[3].rstrip("\n").encode('utf-8') + b'\x00'
                    if values[4] == 'hex':
                        value_3 = bytes.fromhex(values[3])
                else:
                    value_3 = b''
                if values[2] != '':
                    value_2_int = len(value_3)
                else:
                    value_2_int = b''
                self.stored_frames[self.current_array_index].append(
                    [value_0_int, value_1_int, value_2_int, value_3]
                )
        

    def update_frame_number_label(self):
        self.frame_number_label.config(text=f"Frame Number: {self.current_array_index}")

    def selectRecord(self):
        self.newTextEntry.delete("0.0", "end")
        selectedRow = self.dialogTable.focus()
        textValue = self.dialogTable.item(selectedRow, 'values')
        self.newTextEntry.insert(INSERT, textValue[1])

    def doubleClickRecord(self, event):
        self.newTextEntry.delete("0.0", "end")
        self.typeValueTextBox.delete(0, END)
        selectedRow = self.frame_table.focus()
        textValue = self.frame_table.item(selectedRow, 'values')
        self.typeValueTextBox.insert(INSERT, textValue[1])
        self.newTextEntry.insert(INSERT, textValue[3])

    def display_previous_array(self):
        if self.current_array_index > 0:
            self.current_array_index -= 1
            self.update_frame_number_label()
            self.load_frame_data()

    def load_frame_data(self):
        current_array = self.stored_frames[self.current_array_index]
        for item in self.frame_table.get_children():
            self.frame_table.delete(item)
        
        # Insert the next array into the table
        self.count = 0
        for array in current_array:  # Process only the first frame
            if len(array) == 2:
                # Insert the array with 2 elements into the table, filling the first two columns
                self.frame_table.insert(parent="", index=self.count, values=(array[0], array[1], "", ""))
                self.count += 1
            elif len(array) == 4:
                encoding = ""
                if self.current_array_index == 57:
                    if array[1] == 6:
                        pass
                if array[3] is not None and isinstance(array[3], bytes):
                    decoded_value = array[3].decode("utf-8").rstrip('\x00')
                    # Adjusted regex to include underscores and alphanumeric characters
                    if re.match("^[a-zA-Z0-9_#!]", decoded_value):
                        value = decoded_value
                        encoding = 'str'
                    else:
                        # Convert to hexadecimal if there are non-alphanumeric/underscore characters
                        value = array[3].hex()
                        encoding = 'hex'
                else:
                    value = array[3]
                # Insert the array with 4 elements into the table, filling all columns
                self.frame_table.insert(parent="", index=self.count, values=(array[0], array[1], array[2], value, encoding))
                self.count += 1

    def display_next_array(self):
        if self.current_array_index < len(self.stored_frames) - 1:
            self.current_array_index += 1
            self.update_frame_number_label()
            next_array = self.stored_frames[self.current_array_index]
            self.load_frame_data()
            

    def openFile(self):
        self.closeFile()
        file_path = filedialog.askopenfilename()
        if file_path:
            self.processFileUpload(file_path)


    def processFileUpload(self, event):
        # Handle both the event object and the file path string
        try:
            file_path = event.data
        except AttributeError:
            file_path = event
        # Remove brackets if there are spaces in path
        file_path = event
        if file_path[0] == '{' and file_path[-1] == '}':
            file_path=file_path[1:-1]


        frames, frame_count = cutsceneParse.guiParse(file_path)
        self.count = 0
        if frames:
            self.stored_frames = frames  # Store all frames
            self.load_frame_data()

def main():
    root = main_window()
    root.mainloop()

if __name__== "__main__":
    main()