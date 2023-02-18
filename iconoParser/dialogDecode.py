import iconoParser.encodingDictionary as encodingDictionary

def decode(textContent):
    '''
    Given a dialog set of bytes, parse the
    decoded strings
    '''

    output = []
    line = ""
    
    textContent
    letterSegments = textContent.decode().strip('\x00').split("|")
    letterSegments
    for i in letterSegments:
        if i in encodingDictionary.TYPE_DICT.keys():
            line = line + encodingDictionary.TYPE_DICT[i]
        else:
            line = line + i
    output = line



    return output