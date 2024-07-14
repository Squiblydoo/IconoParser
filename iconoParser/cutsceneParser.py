import os
import struct

import iconoParser.types as types
import iconoParser.dialogDecode as iconoDecode

FILE_MAGIC = 4275099604767297

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
 
    # The level structure data is consistent across all files
    # This is parsed primarily to ensure we have the right size
    # and arrive at the right part of the file.
    level_section_size = struct.unpack(types.uint32, f.read(4))[0]
    level_data = []
    for i in range(int(level_section_size)):
        level_id = struct.unpack('q', f.read(8))[0]  
        data = struct.unpack('q', f.read(8))[0]  
        level_data.append([level_id, data])
    output.append(level_data)

    unknown_data = []  # Assuming unknown_data is initialized here

    for _ in range(6):  # Changed loop variable to _ since it's not used

        unknown_section_size = struct.unpack(types.uint32, f.read(4))[0]
        current_data = []  # Initialize a new dictionary for this iteration
        for _ in range(int(unknown_section_size)):  # Changed loop variable to _ to avoid shadowing
            unknown_id = struct.unpack('I', f.read(4))[0]
            unk_type = struct.unpack('I', f.read(4))[0]
            data_len = 0  # Initialize data_len to ensure it's defined even if unk_type != 0x02
            data = b''  # Initialize data to ensure it's defined even if unk_type != 0x02
            if unk_type == 0x02:
                data_len = struct.unpack('I', f.read(4))[0]
                data = f.read(data_len)
            # Use unknown_id as the key and store the rest as values in a list
            current_data.append([unknown_id, unk_type, data_len, data])
        output.append(current_data)  # Append the dictionary to unknown_data at the end of the outer loop
    
    # Animation section
    animation_section_size = struct.unpack(types.uint32, f.read(4))[0]
    animation_data = []
    for i in range(int(animation_section_size)):
        animation_id = struct.unpack(types.uint32, f.read(4))[0]  
        animation_type = struct.unpack(types.uint32, f.read(4))[0]
        if animation_type == 0x02:
                anim_len = struct.unpack(types.uint32, f.read(4))[0]
                anim_data = f.read(anim_len)
        if animation_type == 0x06:
                anim_len = ''
                anim_data = ''
        animation_data.append([animation_id, animation_type, anim_len, anim_data])
    output.append(animation_data)
    unknown_data2 = []  
    for _ in range(7):  
        unknown_section_size = struct.unpack(types.uint32, f.read(4))[0]
        current_data = []  
        for _ in range(int(unknown_section_size)):  
            unknown_id = struct.unpack('I', f.read(4))[0]
            unk_type = struct.unpack('I', f.read(4))[0]
            data_len = 0  
            data = b''  
            if unk_type == 0x02:
                data_len = struct.unpack('I', f.read(4))[0]
                data = f.read(data_len)
            if unk_type == 0x06:
                data_len = ''
                data = ''
            current_data.append([unknown_id, unk_type, data_len, data])
        output.append(current_data)
    
    # Parsing should be complete
    # Return the arrays as one object:
    return output, level_section_size