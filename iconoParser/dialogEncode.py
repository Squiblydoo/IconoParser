import iconoParser.encodingDictionary as encodingDictionary

def get_key(val):
    for key, value in encodingDictionary.TYPE_DICT.items():
        if val == value:
            return key


def encode(textContent):
    '''
    Given a dialog set of bytes, parse the
    decoded strings
    '''
    ## We are going to return a bytes object. Prepare that object.
    line = b''
    
    ## We will use a for-loop to convert the characters to the
    ## appropriate format and add the appropriate separators
    textContent = textContent.strip('"')
    i = 0
    ## For each character in the decoded text, loop through
    ## the following encoding process.
    while i < len(textContent):
        ## If the character is in the dictionry:
        ## (If it is not the first character) add the pipe |
        ## then decode the character based on the key.
        if textContent[i] in encodingDictionary.TYPE_DICT.values():
            if i != 0:
                line = line + b'|'
            line += bytes(get_key(textContent[i]), "utf-8")
            i += 1

        ## If the character is not in the dictionary:
        ## (If it is not the first character) add the pipe |
        ## then add the raw byte.
        else:
            if i != 0:
                line = line + b'|'
            line += bytes(textContent[i], "utf-8")
            i += 1
            ## If the iterator matches the length: stop.
            if i == len(textContent):
                break

            ## Write any characters until the end of the next
            ## character that is not in the encoding dictionary,
            ## then add that character.
            else:
                while textContent[i] != "}":
                    line += bytes(textContent[i],"utf-8")
                    i += 1
                if textContent[i] not in encodingDictionary.TYPE_DICT.values():
                    line += bytes(textContent[i], "utf-8")
                    i += 1
            




    return line