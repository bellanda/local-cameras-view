import random
import time

import cv2
import numpy as np

start = time.time()

# Create an 8 colors 100 random squares
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255), (255, 255, 255), (0, 0, 0)]
list_of_frames = []

# Create 100 frames, each with one random square
for i in range(100):
    # Create a new frame for each iteration
    frame = np.zeros((1000, 1000, 3), dtype=np.uint8)
    color = random.choice(colors)
    x = random.randint(0, 900)
    y = random.randint(0, 900)
    cv2.rectangle(frame, (x, y), (x + 100, y + 100), color, -1)
    list_of_frames.append(frame.copy())  # Use .copy() to avoid reference issues

while True:
    for frame in list_of_frames:
        cv2.imshow("frame", frame)
        time.sleep(0.01)  # Increased delay to make animation more visible

        if cv2.waitKey(1) & 0xFF == ord("q"):
            exit()
