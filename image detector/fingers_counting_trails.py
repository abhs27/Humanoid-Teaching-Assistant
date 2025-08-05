import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Finger tip landmark indices
finger_tips_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky

def count_fingers(hand_landmarks):
    count = 0
    # Thumb: check if tip is to the right of its joint (for right hand)
    if hand_landmarks.landmark[finger_tips_ids[0]].x < hand_landmarks.landmark[finger_tips_ids[0]-1].x:
        count += 1
    # Other fingers: check if tip is above PIP joint
    for tip_id in finger_tips_ids[1:]:
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
            count += 1
    return count

def get_finger_count_with_timer(duration=3):
    cap = cv2.VideoCapture(0)
    start_time = None
    detected_fingers = None
    final_count = None

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                fingers = count_fingers(hand_landmarks)
                if detected_fingers != fingers:
                    detected_fingers = fingers
                    start_time = time.time()
                if start_time and (time.time() - start_time) > duration:
                    final_count = detected_fingers
                    cv2.putText(frame, f'Fingers: {final_count}', (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)
        else:
            start_time = None
            detected_fingers = None
            final_count = None

        cv2.imshow('Finger Counting', frame)

        if final_count is not None:
            # Show count for 2 seconds then exit
            if time.time() - (start_time + duration) > 2:
                break

        if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
            final_count = None
            break

    cap.release()
    cv2.destroyAllWindows()
    return final_count

# Example usage:
if __name__ == "__main__":
    count = get_finger_count_with_timer(3)
    print(f"Final counted fingers: {count}")
