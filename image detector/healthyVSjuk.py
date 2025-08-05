import cv2
import numpy as np
import detector  # Your camera input module
import random
import os
import tkinter as tk

# --- Game Configuration ---
POINTS_TO_WIN = 5
WINDOW_NAME = "Healthy vs. Junk Food Game"
SCALE_FACTOR = 0.5 # Makes window 1/4 of screen area

# --- Food Item Database ---
# Add your own items here. The code will handle them automatically.
FOOD_ITEMS = [
    {"name": "Apple", "type": "healthy", "image": os.path.join("images", "apple.jpg")},
    {"name": "Broccoli", "type": "healthy", "image": os.path.join("images", "broccoli.jpg")},
    {"name": "Carrot", "type": "healthy", "image": os.path.join("images", "carrot.jpg")},
    {"name": "Pizza", "type": "junk", "image": os.path.join("images", "pizza.jpg")},
    {"name": "Burger", "type": "junk", "image": os.path.join("images", "burger.jpg")},
    {"name": "Donut", "type": "junk", "image": os.path.join("images", "donut.jpg")},
]

def get_screen_dimensions():
    """Uses tkinter to get the primary screen's width and height."""
    root = tk.Tk()
    root.withdraw() # Hide the empty tkinter window
    return root.winfo_screenwidth(), root.winfo_screenheight()

def display_message(image, text, color=(0, 255, 0)):
    """Displays a feedback message (e.g., 'Correct!') on the image."""
    font_scale = image.shape[1] / 500
    cv2.putText(image, text, (int(image.shape[1] * 0.1), int(image.shape[0] * 0.8)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 4)
    cv2.imshow(WINDOW_NAME, image)
    cv2.waitKey(1500) # Show message for 1.5 seconds

def main_game():
    """The main function to run the game loop."""
    screen_width, screen_height = get_screen_dimensions()
    win_width = int(screen_width * SCALE_FACTOR)
    win_height = int(screen_height * SCALE_FACTOR)

    score = 0
    random.shuffle(FOOD_ITEMS)
    food_queue = FOOD_ITEMS.copy()

    while score < POINTS_TO_WIN:
        if not food_queue:
            food_queue = FOOD_ITEMS.copy()
            random.shuffle(food_queue)
        
        item = food_queue.pop(0)
        item_name = item["name"]
        item_type = item["type"]
        image_path = item["image"]

        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Warning: Could not load image '{image_path}'. Skipping.")
            continue

        frame = cv2.resize(frame, (win_width, win_height))

        font_scale_score = win_width / 800
        font_scale_name = win_width / 700

        cv2.putText(frame, f"Score: {score}/{POINTS_TO_WIN}", (int(win_width * 0.02), int(win_height * 0.08)), cv2.FONT_HERSHEY_SIMPLEX, font_scale_score, (0, 0, 0), 2)
        cv2.putText(frame, item_name, (int(win_width * 0.02), int(win_height * 0.18)), cv2.FONT_HERSHEY_SIMPLEX, font_scale_name, (0, 0, 0), 3)
        cv2.imshow(WINDOW_NAME, frame)
        cv2.waitKey(1)

        print("\n-------------------------")
        print(f"Is '{item_name}' a healthy food?")
        print("Show your placard to the camera...")
        
        user_answer = detector.get_input()

        correct = False
        if user_answer == "yes" and item_type == "healthy":
            correct = True
        elif user_answer == "no" and item_type == "junk":
            correct = True

        if correct:
            score += 1
            print(f"Correct! Your score is now: {score}")
            display_message(frame, "Correct!", (0, 255, 0))
        elif user_answer is None:
            print("Input cancelled. Exiting game.")
            break
        else:
            print(f"Incorrect. Your score is still: {score}")
            display_message(frame, "Incorrect!", (0, 0, 255))
            
    end_screen = np.zeros((win_height, win_width, 3), dtype=np.uint8)
    font_scale_title = win_width / 400
    font_scale_subtitle = win_width / 800

    if score >= POINTS_TO_WIN:
        print("\nCongratulations! You reached 5 points!")
        cv2.putText(end_screen, "YOU WIN!", (int(win_width*0.25), int(win_height*0.5)), cv2.FONT_HERSHEY_TRIPLEX, font_scale_title, (50, 200, 50), 3)
    else:
        cv2.putText(end_screen, "Game Over", (int(win_width*0.2), int(win_height*0.5)), cv2.FONT_HERSHEY_TRIPLEX, font_scale_title, (200, 200, 200), 3)

    cv2.putText(end_screen, "Press any key to exit", (int(win_width*0.25), int(win_height*0.7)), cv2.FONT_HERSHEY_SIMPLEX, font_scale_subtitle, (255, 255, 255), 2)
    cv2.imshow(WINDOW_NAME, end_screen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main_game()