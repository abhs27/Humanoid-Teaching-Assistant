import cv2
import mediapipe as mp
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

finger_tips_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky

def count_fingers_with_status(hand_landmarks):
    """
    Counts the number of raised fingers and returns the count and status for each finger.
    """
    count = 0
    finger_status = [False, False, False, False, False]  # Thumb, Index, Middle, Ring, Pinky
    
    # Thumb: Check based on its x-coordinate relative to the joint below it.
    # This logic works for a flipped camera view (right hand appears as left).
    if hand_landmarks.landmark[finger_tips_ids[0]].x < hand_landmarks.landmark[finger_tips_ids[0] - 1].x:
        count += 1
        finger_status[0] = True
    
    # Other four fingers: Check if the fingertip is above the joint two landmarks below it.
    for i, tip_id in enumerate(finger_tips_ids[1:], 1):
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
            count += 1
            finger_status[i] = True
    
    return count, finger_status

def draw_finger_circles(frame, hand_landmarks, finger_status):
    """
    Draws circles on the tips of any fingers that are detected as being raised.
    """
    height, width, _ = frame.shape
    
    for i, is_raised in enumerate(finger_status):
        if is_raised:
            # Get the normalized coordinates of the fingertip
            tip_landmark = hand_landmarks.landmark[finger_tips_ids[i]]
            # Convert normalized coordinates to pixel coordinates
            tip_x = int(tip_landmark.x * width)
            tip_y = int(tip_landmark.y * height)
            
            # Draw a filled red circle with a white border for visibility
            cv2.circle(frame, (tip_x, tip_y), 15, (0, 0, 255), -1)
            cv2.circle(frame, (tip_x, tip_y), 15, (255, 255, 255), 2)

def get_finger_count_with_timer(duration=2, max_runtime_seconds=10, stop_event=None):
    """
    Opens the camera and exits after max_runtime_seconds or when a gesture is locked.
    """
    cap = cv2.VideoCapture(0)
    window_name = 'Finger Counting'
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return None
    
    start_time = None
    detected_fingers = None
    final_count = None

    # --- TIMER FOR OVERALL RUNTIME ---
    overall_start_time = time.time()

    while True:
        # --- CHECK IF 10 SECONDS HAVE PASSED ---
        if time.time() - overall_start_time > max_runtime_seconds:
            print(f"Timeout: Exiting after {max_runtime_seconds} seconds.")
            break

        # Early exit if this function is part of a larger threaded application
        if stop_event is not None and stop_event.is_set():
            final_count = None
            break

        success, frame = cap.read()
        if not success:
            break

        # Flip the frame horizontally for a more intuitive mirror-like view
        frame = cv2.flip(frame, 1)
        # Convert the BGR image to RGB for Mediapipe processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                fingers, finger_status = count_fingers_with_status(hand_landmarks)
                draw_finger_circles(frame, hand_landmarks, finger_status)
                
                if detected_fingers != fingers:
                    detected_fingers = fingers
                    start_time = time.time()
                
                if start_time and (time.time() - start_time) > duration:
                    final_count = detected_fingers
                    cv2.putText(frame, f'Fingers: {final_count}', (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)
        else:
            if final_count is None:
                start_time = None
                detected_fingers = None

        cv2.imshow(window_name, frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:
            print("ESC key pressed. Exiting.")
            final_count = None 
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("Window closed by user.")
            if final_count is None:
                final_count = None
            break

        if final_count is not None:
            if time.time() - (start_time + duration) > 2:
                break

    # Clean up and release resources
    cap.release()
    cv2.destroyAllWindows()
    return final_count

# Standalone test to run the script directly
if __name__ == "__main__":
    print("Starting finger count detection. The window will automatically close after 10 seconds.")
    # The new max_runtime_seconds parameter is used here
    count = get_finger_count_with_timer(duration=3, max_runtime_seconds=10)
    
    if count is not None:
        print(f"Final counted fingers: {count}")
    else:
        print("No final count was determined.")