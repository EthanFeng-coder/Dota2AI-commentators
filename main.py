from IPython.display import display, Image, Audio
import cv2  # We're using OpenCV to read video, to install !pip install opencv-python
import base64
from openai import OpenAI
import os
import time
import requests
import pygame
import base64
import cv2
import numpy as np
import threading
import time
from PIL import ImageGrab
from controller import start_listening
import queue
tts_queue = queue.Queue()
tts_thread = None


base64Frames = []  # This will store the base64-encoded frames
capture_thread = None  # This will be the handle for our capturing thread
is_capturing = False  # This flag will control the start/stop of capturing
api_key ="your api key"
client = OpenAI(api_key= api_key)
lock = threading.Lock()
is_audio_playing = False
is_processing = False

def capture_frames():
    global base64Frames, is_capturing
    while is_capturing:
        screenshot = ImageGrab.grab()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame)
        # Ensure thread-safe operation on the frames list
        with lock:
            # Store the latest two frames
            if len(base64Frames) == 2:
                base64Frames.pop(0)
            base64Frames.append(base64.b64encode(buffer).decode('utf-8'))
        time.sleep(0.5)  # Capture every 0.5 seconds



def play_audio(file_path):
    global is_audio_playing
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    is_audio_playing = True

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    is_audio_playing = False

pygame.init()
pygame.mixer.init()

def process_tts_queue():
    global is_audio_playing
    while is_capturing or not tts_queue.empty():
        # Check if audio is currently playing
        if not is_audio_playing and not tts_queue.empty():
            text = tts_queue.get()

            response = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": "tts-1-1106",
                    "input": text,
                    "voice": "onyx",
                },
            )

            if response.status_code == 200:
                audio = response.content
                with open("output_audio.mp3", "wb") as file:
                    file.write(audio)
                play_audio("output_audio.mp3")
            else:
                print("Failed to generate audio:", response.text)

            time.sleep(0.1)

def send_to_gpt4_vision():
    global base64Frames, is_capturing
    while is_capturing:
        with lock:
            if len(base64Frames) == 2:
                # Prepare the prompt for GPT-4 Vision
                prompt_messages = [
                    {
                        "role": "user",
                        "content": [
                            "These are frames of a video about a game called Dota 2. Tell me what is happening and explain. If there is a previous video, try to connect it.",
                            *map(lambda x: {"image": x, "resize": 768}, base64Frames),
                        ],
                    },
                ]
                params = {
                    "model": "gpt-4-vision-preview",
                    "messages": prompt_messages,
                    "max_tokens": 300,
                }

                # Send the frames to GPT-4 Vision for analysis
                result = client.chat.completions.create(**params)
                print(result.choices[0].message.content)

                tts_queue.put(result.choices[0].message.content)
                base64Frames.clear()
            time.sleep(1)



def start_capture():
    global is_capturing, capture_thread
    if not is_capturing:
        is_capturing = True
        # Start the capturing thread
        capture_thread = threading.Thread(target=capture_frames)
        capture_thread.start()
        # Start the GPT-4 Vision sending thread
        threading.Thread(target=send_to_gpt4_vision).start()
        print("Capture started.")


def stop_capture():
    global is_capturing
    if is_capturing:
        is_capturing = False
        capture_thread.join()  # Wait for the capturing thread to finish
        print("Capture stopped.")
        print(f"{len(base64Frames)} frames captured and encoded.")

# This function is defined in your controller.py
# The start_listening function initializes the key listeners and starts the thread
threading.Thread(target=start_listening, args=(start_capture, stop_capture)).start()


