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
        self.geometry("540x650")
        self.title("IconoParser")
        style = ttk.Style()
        style.configure("Treeview",
                        background="white")
        style.map('Treeview',
                background=[('selected', 'blue')])
        self.stored_frames = []

        instructionLabel = Label(self, text="Drag and drop cut scene file onto window below")
        instructionLabel.pack()
        menu = Menu(self)
        self.config(menu=menu)
        file_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.openFile)
        treeFrame = Frame(self)
        treeFrame.pack(pady=20)
        treeScroll = Scrollbar(treeFrame)
        self.frame_table = ttk.Treeview(treeFrame, yscrollcommand=treeScroll.set)
        treeScroll.pack(side=RIGHT, fill=Y)

        self.frame_table.pack()
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

        # for i in range(1, 16):
        #     self.frame_table.insert("", "end", text=str(i), values=(""))
        self.frame_table.pack()

        navigation_frame = Frame(self)
        navigation_frame.pack()        
        self.frame_number_label = Label(navigation_frame, text="Frame Number: 0")
        self.frame_number_label.grid(row=0, column=0)
        
        self.current_array_index = 0  # Initialize the current array index

        self.prev_button = Button(navigation_frame, text="Previous", command=self.display_previous_array)
        self.prev_button.grid(row=0, column=1)
        self.next_button = Button(navigation_frame, text="Next", command=self.display_next_array)
        self.next_button.grid(row=0, column=2)
    
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

    def exportFile(self):
        file_path = filedialog.asksaveasfilename()
        convert = iconoParser.backtoCutSceneFormat.guiExport(self.stored_frames)

        FILE_MAGIC = 0x415252312E300F000000
        length_in_bytes = 10
        file_magic_bytes = FILE_MAGIC.to_bytes(length_in_bytes, 'big')
        
        output = file_magic_bytes + convert
        with open(file_path, "wb") as dia_file:
            dia_file.write(output)
        

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
            prev_array = self.stored_frames[self.current_array_index]
            
            # Clear the existing content in the table
            for item in self.frame_table.get_children():
                self.frame_table.delete(item)
            
            # Insert the previous array into the table
            self.count = 0
            for array in prev_array:
                if len(array) == 2:
                    # Insert the array with 2 elements into the table
                    self.frame_table.insert(parent="", index=self.count, values=(array[0], array[1], "", ""))
                    self.count += 1
                elif len(array) == 4:
                    encoding = ''
                    if array[3] is not None and isinstance(array[3], bytes):
                        decoded_value = array[3].decode("utf-8").rstrip('\x00')
                        # Adjusted regex to include underscores and alphanumeric characters
                        if re.match("^[a-zA-Z0-9_#]", decoded_value):
                            value = decoded_value
                            encoding = 'str'
                        else:
                            # Convert to hexadecimal if there are non-alphanumeric/underscore characters
                            value = array[3].hex()
                            encoding = 'hex'

                    else:
                        value = array[3]
                    self.frame_table.insert(parent="", index=self.count, values=(array[0], array[1], array[2], value, encoding))
                    self.count += 1
        else:
            print("No previous arrays to display.")
    

    def display_next_array(self):
        if self.current_array_index < len(self.stored_frames) - 1:
            self.current_array_index += 1
            self.update_frame_number_label()
            next_array = self.stored_frames[self.current_array_index]
            
            # Assuming 'self.frame_table' is your table widget
            # First, clear the existing content in the table
            for item in self.frame_table.get_children():
                self.frame_table.delete(item)
            
            # Insert the next array into the table
            self.count = 0
            for array in next_array:  # Process only the first frame
                if len(array) == 2:
                    # Insert the array with 2 elements into the table, filling the first two columns
                    self.frame_table.insert(parent="", index=self.count, values=(array[0], array[1], "", ""))
                    self.count += 1
                elif len(array) == 4:
                    encoding = ""
                    if array[3] is not None and isinstance(array[3], bytes):
                        decoded_value = array[3].decode("utf-8").rstrip('\x00')
                        # Adjusted regex to include underscores and alphanumeric characters
                        if re.match("^[a-zA-Z0-9_#]", decoded_value):
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
        else:
            print("No more arrays to display.")

    def openFile(self):
        file_path = filedialog.askopenfilename()
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

        #Process file using iconoParser
        frames, frame_count = cutsceneParse.guiParse(file_path)
        # Step 1: Initialize a storage mechanism for the array objects
        # This should be done in the initialization method of your class, for example:
        # def __init__(self, ...):
        #     self.stored_arrays = []
        self.count = 0
        if frames:
            # Assuming each 'frame' is a list of array objects and we want to show the first one and store the rest
            for array in frames[0]:  # Process only the first frame
                    if len(array) == 2:
                        # Insert the array with 2 elements into the table, filling the first two columns
                        self.frame_table.insert(parent="", index=self.count, values=(array[0], array[1], "", ""))
                        self.count += 1
                    elif len(array) == 4:
                        encoding = ''
                        # Insert the array with 4 elements into the table, filling all columns
                        if array[3] is not None and isinstance(array[3], bytes):
                            decoded_value = array[3].decode("utf-8").rstrip('\x00')
                            # Adjusted regex to include underscores and alphanumeric characters
                            if re.match("^[a-zA-Z0-9_#]", decoded_value):
                                value = decoded_value
                                encoding = 'str'
                            else:
                                # Convert to hexadecimal if there are non-alphanumeric/underscore characters
                                value = array[3].hex()
                                encoding = 'hex'
                        else:
                            value = array[3]
                        self.frame_table.insert(parent="", index=self.count, values=(array[0], array[1], array[2], value, encoding))
                        self.count += 1

                # Step 3: Store the rest of the frames in the initialized list for later use
            self.stored_frames = frames  # Store all frames

def main():
    root = main_window()
    root.mainloop()

if __name__== "__main__":
    main()