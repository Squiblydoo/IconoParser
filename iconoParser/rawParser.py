import os
import struct

import iconoParser.types as types
import iconoParser.dialogEncode as iconoEncode



def parse(data):

    encodedLine = b''  
    i = 0
    while i < len(data):
        line = data[i]

        
        ## Each dialog part consists of three parts. This is indicated by a 
        ## four bytes before the section. Each of the three parts are prefaced by two additional
        ## sets of four bytes "1" and "2"
        ## We add those bytes as little-endian
        if line[0] == 0:
            encodedLine += struct.pack("<lll", 3, 1, 2)
        else: 
            encodedLine += struct.pack("<ll", 1, 2)
                
        
        if line[0] == 0 or line[0] == 1:
            encodedText = iconoEncode.encode(line[2])
        elif line[0] == 2:
            encodedText = bytes(line[2], "utf-8")
        

        ## Length is calculated with the nullbyte.
        ## In the encoded version, each line needs to have a null byte
        ## appended to the end. This is likely for the game engine's parser.
        encodedText += b'\x00'
        encodedLength = len(encodedText)
        encodedLine += struct.pack("<l", encodedLength)
        encodedLine += encodedText
        i += 1
        
        

    
    return encodedLine
