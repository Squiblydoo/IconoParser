import os
import struct
import ast
import iconoParser.types as types
import iconoParser.dialogEncode as iconoEncode

# This is the first line we printed in the CSV
# Basically, I'm making sure that we receive the right file back
# This keeps users from passing the wrong file in and then us mangling it.
#FILE_MAGIC = b'dialog part,text size (do not edit),text\r\r\n'

def guiExport(frames):
    encodedLine = b'' 
    arrays = [list(group) for group in zip(*frames)]
    for parts in arrays:
        encodedLine += struct.pack("<l", len(parts))
        for i, element in enumerate(parts):
            if len(element) == 2:
                for part in element:
                    encodedLine += struct.pack("<q", part)
            else:
                for part in element:
                    if type(part) == int:
                        encodedLine += struct.pack("<l", part)
                    elif isinstance(part, bytes):
                        encodedLine += part  # If it's already bytes, just append it
                    else:
                        # Convert element to string explicitly if it's not bytes, then encode
                        encodedLine += bytes(str(part), "utf-8")
    return encodedLine




def parse(path):

    output = ""
    f = open(path, 'r')
    f.seek(0, os.SEEK_END)
    end = f.tell()
    f.seek(0, os.SEEK_SET)

#    magic = f.readline()
#    if magic != FILE_MAGIC:
#        raise Exception("Invalid file")
    encodedLine = b''  
    cutscene_array = []
    while (end - f.tell()) > 0:
        line = f.readline()
        list_strings = line.strip().split('","')

        # Remove the leading and trailing double quotes from the first and last elements
        list_strings[0] = list_strings[0][1:]
        list_strings[-1] = list_strings[-1][:-1]

        # Convert each string representation of a list back into a list using ast.literal_eval
        arrays = [ast.literal_eval(lst) for lst in list_strings]
        cutscene_array.append(arrays)
        
    # Assuming frames has been modified and you want to transpose it back
    original_structure = [list(group) for group in zip(*cutscene_array)]
    for parts in original_structure:
        encodedLine += struct.pack("<l", len(parts))
        for i, element in enumerate(parts):
            if len(element) == 2:
                for part in element:
                    encodedLine += struct.pack("<q", part)
            else:
                for part in element:
                    if part == 3:  # When we're at the third element
                        # Ensure elements[3] exists and calculate its length
                        if len(element) > 3:
                            length_of_element_3 = len(element[3])
                            part = length_of_element_3
                            #encodedLine += struct.pack("<l", length_of_element_3)
                    if type(part) == int:
                        encodedLine += struct.pack("<l", part)
                    elif isinstance(part, bytes):
                        encodedLine += part  # If it's already bytes, just append it
                    else:
                        # Convert element to string explicitly if it's not bytes, then encode
                        encodedLine += bytes(str(part), "utf-8")



    
    return encodedLine
