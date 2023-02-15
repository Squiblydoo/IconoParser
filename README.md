# IconoParser
A simple parser for converting the text from the game Iconoclasts into a human readable format.

# How to use
Place a "dia" (aka dialog file) from the game's data directory into the same directory as the parser. (The dialog files can be found at `C:\Program Files (x86)\Steam\steamapps\common\Iconoclasts\data`.) run the parser and redirect the output to file. For example:
```
python fileParser.py -f dia > parsed.csv
```
This command does the following:
- executes the python script (`python fileParser.py`) 
- provides the file for parsing (`-f dia`) 
- writes it to a file named "parsed.csv" (`> parsed.csv`).
