
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

    parser.add_argument('-c', '-csv', action='store', help="Specify to convert a dia* file to CSV")
    parser.add_argument('-d', '-dia', action='store', help="Specify to conver a csv back to the dia* format.")

    args = parser.parse_args()

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
    

if __name__ == "__main__":
    main()