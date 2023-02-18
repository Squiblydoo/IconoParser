import os
import struct

import iconoParser.types as types
import iconoParser.dialogDecode as iconoDecode

FILE_MAGIC = 0x109a302e31525241

def parse(path):

    output = []
    f = open(path, 'rb')
    f.seek(0, os.SEEK_END)
    end = f.tell()
    f.seek(0, os.SEEK_SET)

    magic = struct.unpack(types.uint64, f.read(8))[0]
    if magic != FILE_MAGIC:
        raise Exception("Invalid file")
    version = struct.unpack(types.uint16,f.read(2))[0]
 
    while (end - f.tell()) > 0:    
        dialogChunk = struct.unpack(types.uint32, f.read(4))[0]
        for i in range(int(dialogChunk)):
            unk1 = struct.unpack(types.uint32, f.read(4))[0]
            unk2 = struct.unpack(types.uint32, f.read(4))[0]
            textSize = struct.unpack(types.uint32, f.read(4))[0]
            content = f.read(textSize)
            output.append([i, textSize, iconoDecode.decode(content)])
    
    return output
