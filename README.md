# IconoParser
A simple parser for converting the text from the game Iconoclasts into a human readable format.

# How to use
Place a "dia" (aka dialog file) from the game's data directory into the same directory as the parser and run the following command: <br>
`python fileParser.py -f dia -c csv`<br>
This command does the following:
- executes the python script (`python fileParser.py`) 
- provides the dia file as input (`-f dia`) 
- it specifies to convert the file to csv (`-c csv`).

It will write a file to the same directory named "parsed.csv". This is a human readable file and can be opened in a word processor or text editor.

After edits have been made, run the following command:<br>
`python fileParser.py -f parsed.csv -c dia`<br>
This command does the following:
- Executes the python script (`python fileParser.py`)
- provides the parsed script for input (`-f parsed.csv`)
- it specifies to convert the file to the original format (`-c dia`)

It will write a file to the same directory named "dia2". In order to use it, you will need to save a copy of the original "dia" file from the Game's directory; rename "dia2" to "dia" and place it in the game's directory where you found the "dia" file.

The default directory for the dia file is located here:<br>
Windows: `"C:\Program Files (x86)\Steam\steamapps\common\Iconoclasts\data\dia"`
