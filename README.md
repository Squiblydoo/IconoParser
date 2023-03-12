# IconoParser
![Robin_Stock_Icon_Scaled](https://user-images.githubusercontent.com/77356206/224560771-74a4db37-9020-41b4-8533-9c5d6c6f2052.png)
<br>
(Image/app Icon by Sho Sakazaki, used with permission)

A GUI parser or CLI parser for converting the text from the game Iconoclasts into a human readable format and back again.

# How to use
## Method one: GUI
Download built program [from releases page here](https://github.com/Squiblydoo/IconoParser/releases). 
Run the program. Go to the game's directory (on Windows this is probably "C:\Program Files (x86)\Steam\steamapps\common\Iconoclasts\data\")
Drag-and-Drop a "dia" file from the directory into the main part of the window. Please note, only the file named "dia" is fully supported. I plan to add support for the other language files at a later time.*

Once dropped, the file will be automatically processed. You can then edit the file. Save your changes and then export the changed file.

After a few seconds, a file named "dia2" will be written to the directory from where you ran the program.

I recommend making a backup of the original "dia" file, or store the original in another directory. Then rename the "dia2" file to the name of the original "dia" file.

I've also included a video below.

*IF YOU WANT TO CONTRIBUTE TO THE DECODING OF THESE FILES, PLEASE DO!

https://user-images.githubusercontent.com/77356206/223280939-daeabce9-5212-4ea3-aa97-6065e7065a89.mp4

## Method two:
The tool can also be used with CLI. This is best if you just want to dump the whole text file, or modify it in a different editor.
To use the Commandline there are two commands to know and python 3 needs to be installed:

**Convert to CSV**<br>
`python fileParser.py -f dia -c csv`<br>
This command takes the following parameters:<br>
- name of the parser (`fileParser.py`) 
- the "file flag" (`-f`) 
- the name of the file we are converting from (`dia`)
- the "conversion" flag (`-c`) 
- the format we are converting to `csv`

**Convert from CSV**<br>
`python fileParser.py -f parsed.csv -c dia`<br>
This command takes the following parameters:<br>
- name of the parser (`fileParser.py`)
- the "file flag" (`-f`)
- the name of the file we are converting from (`parsed.csv`)
- the "conversion" flag (`-c`)
- the format we are converting to `dia`

Known issue: using both methods could cause some wonkiness. The CSV method currently has a discrepency that is caused by using the CSV format. I am planning to modify this format to avoid these problems but have not yet done so.
