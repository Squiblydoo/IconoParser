## UI Libraries
from tkinter import *
from tkinter import ttk
import tkinter.scrolledtext as st
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
import re

def frame_type(frame):
    frame_type = frame[5][3].decode("utf-8").rstrip('\x00')
    if frame_type == "set_time":
        return "set_time"
    elif frame_type == "pos":
        return "set_position"

def parse_animation(animation):
    
    animation = animation.split(",")
    anim_iterator = iter(animation)
    anim_dict = {}
    for anim in anim_iterator:
        if anim.startswith("#X") or anim.startswith("X"):
            char_x = next(anim_iterator, None)
            anim_dict["X"] = char_x
        if anim.startswith("#Y") or anim.startswith("Y"):
            char_y = next(anim_iterator, None)
            anim_dict["Y"] = char_y
        if anim.startswith("#Animation") or anim.startswith("Animation"):
            char_anim = next(anim_iterator, None)
            anim_dict["Animation"] = char_anim
        if anim.startswith("#Direction") or anim.startswith("Direction"):
            char_dir = next(anim_iterator, None)
            anim_dict["Direction"] = char_dir
        if anim.startswith("#MultiY") or anim.startswith("MultiY"):
            char_multi_y = next(anim_iterator, None)
            anim_dict["MultiY"] = char_multi_y

    return anim_dict




def animate_single_frame(frame):

    root = Tk()
    canvas_width = 400
    canvas_height = 400
    canvas = Canvas(root, width=canvas_width, height=canvas_height)
    canvas.pack()

    target = frame[5][3].decode("utf-8").rstrip('\x00')
    if target.startswith("edit"): # This indicates it is a object (player or NPC)
        target_number = frame[6][3].decode("utf-8").rstrip('\x00')
        if target_number == "0":
            pass # This is the player
        animation = frame[7][3].decode("utf-8").rstrip('\x00')  

    #current_animation = canvas.create_circle(50, 50, 150, fill="blue")
    anim = parse_animation(animation)
    current_entity = canvas.create_rectangle(int(anim["X"]), int(anim["Y"]), int(anim["X"]) + 10, int(anim["Y"]) + 10, fill="blue")

    def move_current_animation():
        canvas.move(current_entity, 10, 0)


    button = Button(root, text="Move Right", command=move_current_animation)
    button.pack()


    root.mainloop()
    pass