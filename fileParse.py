
import argparse
import textwrap
import sys

import iconoParser.diaParser
import iconoParser.csvParser
import iconoParser.csvOutput

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
        [IconoParser]
        
        [Convert Diaglog files from or to CSV]
        Provide the commandline a parameter to conver a dialog file to a CSV
        or convert the CSV back to the game's required format.
        ''')
    )
    parser.add_argument('-f', '-filename', help='Path to dia* file', action='store',
        type=str, default="f")

    parser.add_argument('-c', '-convert', action='store', help="Convert to CSV or to DIA formats.",
                         default="csv", choices=["csv", "dia"])

    args = parser.parse_args()

    if args.c == "csv":
        convert = iconoParser.diaParser.parse(args.f)
        header = ["dialog part", "text size (do not edit)", "text"]
        output = []
        output.append(header)
        for item in convert:
            line = []
            for i in range(len(header)):
                line.append(item[i])
            output.append(line)  
                
        sys.modules["iconoParser.csvOutput"].__getattribute__(
            "csvOutput")(output)
    
    elif args.c == "dia":
        FILE_MAGIC = b'\x41\x52\x52\x31\x2e\x30\x9a\x10'
        File_Version = b'\x00\x00'
        
        convert = iconoParser.csvParser.parse(args.f)
        output = FILE_MAGIC + File_Version + convert
        with open("dia2.txt", "wb") as dia_file:
            dia_file.write(output)

    

if __name__ == "__main__":
    main()