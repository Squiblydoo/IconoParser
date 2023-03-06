## UI Libraries
from tkinter import *
from tkinter import ttk
import tkinter.scrolledtext as st
from tkinterdnd2 import DND_FILES, TkinterDnD


#IconoParser Pluggins
import iconoParser.helperDictionaries as helperDict
import fileParse

def get_key(val):
    for key, value in helperDict.DIALOG_FUNCTION.items():
        if val == value:
            return key

class main_window(TkinterDnD.Tk):
        
    def __init__(self):
        TkinterDnD.Tk.__init__(self)

        # Basic Window Configuration
        self.geometry("800x600")
        self.title("IconoParser")
        style = ttk.Style()
        style.configure("Treeview",
                        background="white")
        style.map('Treeview',
                background=[('selected', 'blue')])

        # Frame and scrollbar for Treeview
        treeFrame = Frame(self)
        treeFrame.pack(pady=20)
        treeScroll = Scrollbar(treeFrame)
        self.dialogTable = ttk.Treeview(treeFrame, yscrollcommand=treeScroll.set)
        treeScroll.config(command=self.dialogTable.yview)
        treeScroll.pack(side=RIGHT, fill=Y)
        self.dialogTable.pack()
        
        # Default tabel design
        self.dialogTable['columns'] = ("DialogPart",  "Text")

        #Formatting columns
        self.dialogTable.column("#0", width=60, minwidth=25)
        self.dialogTable.column("DialogPart", anchor=W, width=80)
        self.dialogTable.column("Text", anchor=W, width=800)

        #Headings
        self.dialogTable.heading("#0", text="")
        self.dialogTable.heading("DialogPart", text="DialogPart", anchor=W)
        self.dialogTable.heading("Text", text="Text", anchor=W)

        self.dialogTable.tag_configure("speakerHighlight", background="#ccffff")
        self.dialogTable.tag_configure("dialogAndAction", background="white")
        self.dialogTable.drop_target_register(DND_FILES)
        self.dialogTable.dnd_bind("<<Drop>>", self.processFileUpload)
        self.dialogTable.pack()


        ## Overarching options Frame: contains other frames.
        optionFrame = Frame(self)
        optionFrame.pack()

        ## Dialog modifying options
        modifyFrame = LabelFrame(optionFrame, text="Modify Lines")
        modifyFrame.grid(row=0, column=0, pady=10,padx=10)

        newDialogLabel = Label(modifyFrame, text="Dialog")
        newDialogLabel.pack()
        self.newTextEntry = st.ScrolledText(modifyFrame, width=50, height=3)
        self.newTextEntry.pack()

        #add_record = Button(modifyFrame, text="Add Dialog", command=addRecord)
        #add_record.pack()

        selectButton = Button(modifyFrame, text="Select Record", command=self.selectRecord)
        selectButton.pack()

        updateButton = Button(modifyFrame, text="Save Changes", command=self.saveUpdatedRecord)
        updateButton.pack()

        ## Dialog Options Key
        keyFrame = LabelFrame(optionFrame, text="Dialog Options Key - Reference Only")
        keyFrame.grid(row=0, column=1, pady=10,padx=10)

        dialogStyleLabel = Label(keyFrame, text="Dialog Bubble Style")
        dialogStyleLabel.pack()
        dialogStyleSelection = StringVar()
        dialogStyles = ttk.Combobox(keyFrame, textvariable=dialogStyleSelection, width=50)
        dialogStyles['values'] = (
            "{bub01}",
            "{bub02}", 
            "{bub03}",
            "{bub04}",
            "{bub05}")
        def changeDialogStyle():
            print()
        dialogStyles.bind('<<ComboboxSelected>>', changeDialogStyle)
        dialogStyles.pack()

        colorsLabel = Label(keyFrame, text="Color Options")
        colorsLabel.pack()
        colorSelection = StringVar()
        colorOptions = ttk.Combobox(keyFrame, textvariable=colorSelection, width=50)
        colorOptions['values'] = (
            "{dye00} = normal",
            "{dye01} = red",
            "{dye02} = for choices- light yellow or possibly blue",
            "{dye03} = unused",
            "{dye04} = also yellow, for names",
            "{dye05} = green, tweaks/contra stuff",
            "{dye06} = light blue, for Holy things",
            "{dye07} = grey",
            "{dye08} = only in unused text",
            "{dye09} = cyan",
            "{dye10} = purple, for one concern related things")
        def changeColorChoice():
            pass
        colorOptions.bind('<<ComboboxSelected>>', changeColorChoice)
        colorOptions.pack()

        exportChanges = Button(self, text="Export Changes", command=self.dataExport)
        exportChanges.pack()

    # Load selected record details
    def selectRecord(self):
        self.newTextEntry.delete("0.0", "end")
        selectedRow = self.dialogTable.focus()
        textValue = self.dialogTable.item(selectedRow, 'values')
        self.newTextEntry.insert(INSERT, textValue[1])

    # Save current details to selected record
    def saveUpdatedRecord(self):
        selectedRow = self.dialogTable.focus()
        textValue = self.dialogTable.item(selectedRow, 'values')
        dialogNumber = self.dialogTable.item(selectedRow, 'text')
        self.dialogTable.item(selectedRow, text=dialogNumber, values=(textValue[0], self.newTextEntry.get('0.0', 'end')))
        self.newTextEntry.delete("0.0", "end")
        
    # Add record to the end of the table.
    def addRecord(self):
        self.dialogTable.insert(parent='', index='end', iid=self.count, text='', \
                    values=(helperDict.DIALOG_FUNCTION["0"], self.newTextEntry.get()))
        
    def processFileUpload(self, event):
        # Remove brackets if there are spaces in path
        filePath = event.data
        if filePath[0] == '{' and filePath[-1] == '}':
            filePath=filePath[1:-1]

        #Process file using iconoParser
        data = fileParse.guiParse(filePath)
        self.count = 0
        self.dialogCount = 0
        for record in data:
            if self.count == 0:
                self.count += 1
                pass
            else:
                if record[0] == 0:
                    self.dialogCount += 1
                self.dialogTable.insert(parent='', index='end', iid=self.count, text=self.dialogCount, 
                        values=(helperDict.DIALOG_FUNCTION[record[0]],record[2]),
                        tags=(helperDict.TAG_ENUM[record[0]],))
                self.count +=1
    
    def dataExport(self):
        # Prepare data for iconoParser
        dataObject = []

        for i in range(self.count):
            if i != 0:
                rowValues = self.dialogTable.item(i, 'values')
                dataObject.append((get_key(rowValues[0]), len(rowValues[1]), rowValues[1]))
        fileParse.guiExport(dataObject)
        





def main():
    root = main_window()
    root.mainloop()

if __name__== "__main__":
    main()