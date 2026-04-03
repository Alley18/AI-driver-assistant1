import cv2

def start_vision():
    # Index 0 works for most built-in webcams and Pi cameras
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not detect a camera.")
        return

    print("--- ADAMS Vision Node Initialized ---")
    print("Action: Press 'q' to close the window.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # This is where the ML team will eventually add the EAR and Emotion logic
        cv2.putText(frame, "ADAMS: Monitoring Active", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow('ADAMS Driver Feed (Dev Mode)', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_vision()