import os

CURRENT_SKIN = "default"

def get_sprite_path():
    return f"assets/skins/{CURRENT_SKIN}/sprites"

def set_skin(name):
    global CURRENT_SKIN
    if os.path.exists(f"assets/skins/{name}"):
        CURRENT_SKIN = name
        return True
    return False
