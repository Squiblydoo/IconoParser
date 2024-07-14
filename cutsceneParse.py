
import argparse
import textwrap
import sys
import shutil

import iconoParser.cutsceneParser
import iconoParser.backtoCutSceneFormat
import iconoParser.csvOutput
import iconoParser.rawParser

def guiParse(file_path):
        backup_file = file_path + "_backup"
        shutil.copy(file_path, backup_file)
        output = []
        
        # Assuming convert is an array of arrays, and all inner arrays are of the same size

        convert, frame_length = iconoParser.cutsceneParser.parse(file_path)
        frames = [list(group) for group in zip(*convert)]
        return frames, frame_length
        

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
    parser.add_argument('-f', '-filename', help='Path to cutscene file', action='store',
        type=str, default="f")

    parser.add_argument('-c', '-convert', action='store', help="Convert to cutscene to editable format or convert back.",
                         default="csv", choices=["csv", "arr"])

    args = parser.parse_args()

    if args.c == "csv":
        convert, frame_length = iconoParser.cutsceneParser.parse(args.f)

        # Make a backup of the original file before modifying the original
        backup_file = args.f + "_backup"
        shutil.copy(args.f, backup_file)
        output = []
        
        # Assuming convert is an array of arrays, and all inner arrays are of the same size
        frames = [list(group) for group in zip(*convert)]
                
        sys.modules["iconoParser.csvOutput"].__getattribute__(
            "csvOutput")(frames, args.f + ".csv")
    
    elif args.c == "arr":
        FILE_MAGIC = 0x415252312E300F000000
        length_in_bytes = 10
        file_magic_bytes = FILE_MAGIC.to_bytes(length_in_bytes, 'big')
        
        convert = iconoParser.backtoCutSceneFormat.parse(args.f)
        output = file_magic_bytes + convert
        with open(args.f + ".arr", "wb") as dia_file:
            dia_file.write(output )

    

if __name__ == "__main__":
    main()