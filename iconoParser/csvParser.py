import os
import struct

import iconoParser.types as types
import iconoParser.dialogEncode as iconoEncode

# This is the first line we printed in the CSV
# Basically, I'm making sure that we receive the right file back
# This keeps users from passing the wrong file in and then us mangling it.
FILE_MAGIC = b'dialog part,text size (do not edit),text\r\r\n'

def parse(path):

    output = ""
    f = open(path, 'rb')
    f.seek(0, os.SEEK_END)
    end = f.tell()
    f.seek(0, os.SEEK_SET)

    magic = f.readline()
    if magic != FILE_MAGIC:
        raise Exception("Invalid file")
    encodedLine = b''  
 
    while (end - f.tell()) > 0:
        line = f.readline()
        parts = line.decode().split(",")
        if len(parts) > 3:
            for i in range(3, len(parts)):
                parts[2] +="," + parts[i]

        
        ## Each dialog part consists of three parts. This is indicated by a 
        ## four bytes before the section. Each of the three parts are prefaced by two additional
        ## sets of four bytes "1" and "2"
        ## We add those bytes as little-endian
        if parts[0] == "0":
            encodedLine += struct.pack("<lll", 3, 1, 2)
        else: 
            encodedLine += struct.pack("<ll", 1, 2)
        
        ## Encode the text stripping off the whitespace that was inadvertently added to the string.
        if parts[0] == "0" or parts[0] == "1":
            encodedText = iconoEncode.encode(parts[2].strip())
        elif parts[0] == "2":
            encodedText = bytes(parts[2].strip().strip('"'), "utf-8")
        

        ## Length is calculated with the nullbyte.
        ## In the encoded version, each line needs to have a null byte
        ## appended to the end. This is likely for the game engine's parser.
        encodedText += b'\x00'
        encodedLength = len(encodedText)
        encodedLine += struct.pack("<l", encodedLength)
        encodedLine += encodedText
        
        

    
    return encodedLine
