
import keyboard
import threading
from PIL import ImageGrab

class Dota2AICommentatorController:
    def __init__(self, start_callback, stop_callback):
        self.capture_interval = 0.5  # Set to 0.5 seconds between captures
        self.is_running = False
        self.thread = None
        self.start_callback = start_callback
        self.stop_callback = stop_callback

    def start_capture(self):
        self.start_callback()

    def stop_capture(self):
        self.stop_callback()

    def listen_for_keys(self):
        keyboard.add_hotkey('s', self.start_capture)
        keyboard.add_hotkey('space', self.stop_capture)
        print("Listening for 's' to start and 'Space' to stop.")
        keyboard.wait('esc')  # Use 'esc' to exit the program

def start_listening(start_callback, stop_callback):
    controller = Dota2AICommentatorController(start_callback, stop_callback)
    controller.listen_for_keys()