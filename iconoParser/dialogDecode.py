import re

TYPE_DICT = {"1":"!",
	"2":" ",
	"8":"\'",
	"13":",",
	"14":"-",
	"15":".",
    "17":"0",
	"18":"1",
	"19":"2",
	"20":"3",
	"21":"4",
	"22":"5",
	"23":"6",
	"24":"7",
	"25":"8",
	"26":"9",
	"27":":",
	"32":"?",
	"34":"A",
	"35":"B",
	"36":"C",
	"37":"D",
	"38":"E",
	"39":"F",
	"40":"G",
	"41":"H",
	"42":"I",
	"43":"J",
	"44":"K",
	"45":"L",
	"46":"M",
	"47":"N",
	"48":"O",
	"49":"P",
	"50":"Q",
	"51":"R",
	"52":"S",
	"53":"T",
	"54":"U",
	"55":"V",
	"56":"W",
	"57":"X",
	"58":"Y",
	"59":"Z",
	"66":"a",
	"67":"b",
	"68":"c",
	"69":"d",
	"70":"e",
	"71":"f",
	"72":"g",
	"73":"h",
	"74":"i",
	"75":"j",
	"76":"k",
	"77":"l",
	"78":"m",
	"79":"n",
	"80":"o",
	"81":"p",
	"82":"q",
	"83":"r",
	"84":"s",
	"85":"t",
	"86":"u",
	"87":"v",
	"88":"w",
	"89":"x",
	"90":"y",
	"91":"z",
	"101":"Í"
    }

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
        if i in TYPE_DICT.keys():
            line = line + TYPE_DICT[i]
        else:
            line = line + i
    output = line



    return output