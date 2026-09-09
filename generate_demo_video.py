import os
import cv2
import numpy as np

def create_synthetic_border_video(output_path="data/demo_videos/sample_border.mp4", duration_sec=25, fps=25):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 960, 540
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps

    # Scenario:
    # Frame 0 - 50: Quiet empty border fence
    # Frame 50 - 250: Person walking across from left (x=50) to right (x=450), enters Restricted Zone at x=300
    # Frame 250 - 450: Person loiters inside the zone
    # Frame 450 - 625: Vehicle drives from right (x=900) to left (x=100) with simulated license plate

    person_x = 50
    person_y = 320
    vehicle_x = 900
    vehicle_y = 380

    for frame_idx in range(total_frames):
        # Base scene: surveillance dusk/night view
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (28, 32, 38) # Dark tactical background

        # Ground / terrain
        cv2.rectangle(frame, (0, 300), (width, height), (38, 44, 52), -1)
        # Road lane
        cv2.rectangle(frame, (0, 360), (width, 480), (45, 52, 60), -1)
        # Dashed lane markings
        for lx in range(0, width, 60):
            cv2.line(frame, (lx, 420), (lx + 30, 420), (120, 130, 140), 2)

        # Border Fence (vertical posts and cross wire)
        for fx in range(20, width, 40):
            cv2.line(frame, (fx, 220), (fx, 310), (70, 75, 80), 2)
        cv2.line(frame, (0, 240), (width, 240), (80, 85, 90), 1)
        cv2.line(frame, (0, 280), (width, 280), (80, 85, 90), 1)

        # Static text / Watermark
        cv2.putText(frame, "IBVAP DEMO SURVEILLANCE FEED - CAM 01 [SECTOR NORTH]", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 190, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, f"FRAME: {frame_idx:05d} | REC", (width - 240, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 0), 1, cv2.LINE_AA)

        # 1. Animate Person (frame 50 to 450)
        if 50 <= frame_idx < 450:
            if frame_idx < 260:
                person_x = int(50 + (frame_idx - 50) * 1.6) # walking towards zone
            else:
                # Slight loitering jitter
                person_x = 386 + int(5 * np.sin(frame_idx * 0.1))
                person_y = 320 + int(3 * np.cos(frame_idx * 0.1))

            # Draw recognizable person figure: head, torso, legs
            # Head
            cv2.circle(frame, (person_x, person_y - 45), 10, (180, 180, 190), -1)
            # Torso (jacket)
            cv2.rectangle(frame, (person_x - 12, person_y - 35), (person_x + 12, person_y), (140, 90, 40), -1)
            # Legs
            leg_offset = int(4 * np.sin(frame_idx * 0.4)) if frame_idx < 260 else 0
            cv2.line(frame, (person_x - 6, person_y), (person_x - 8 + leg_offset, person_y + 35), (80, 80, 90), 4)
            cv2.line(frame, (person_x + 6, person_y), (person_x + 8 - leg_offset, person_y + 35), (80, 80, 90), 4)

        # 2. Animate Vehicle (frame 400 to total_frames)
        if frame_idx >= 400:
            vehicle_x = int(950 - (frame_idx - 400) * 4.5)
            if -200 < vehicle_x < width + 100:
                # Car body
                cv2.rectangle(frame, (vehicle_x, vehicle_y), (vehicle_x + 160, vehicle_y + 55), (160, 50, 40), -1)
                # Cabin
                cv2.rectangle(frame, (vehicle_x + 35, vehicle_y - 30), (vehicle_x + 125, vehicle_y), (120, 150, 170), -1)
                # Wheels
                cv2.circle(frame, (vehicle_x + 35, vehicle_y + 55), 14, (30, 30, 30), -1)
                cv2.circle(frame, (vehicle_x + 125, vehicle_y + 55), 14, (30, 30, 30), -1)
                # Headlight beam
                pts = np.array([[vehicle_x, vehicle_y + 20], [vehicle_x - 120, vehicle_y - 20], [vehicle_x - 140, vehicle_y + 60]], np.int32)
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], (180, 220, 240))
                cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
                # License plate
                cv2.rectangle(frame, (vehicle_x + 5, vehicle_y + 22), (vehicle_x + 55, vehicle_y + 40), (240, 240, 240), -1)
                cv2.putText(frame, "WB-24", (vehicle_x + 8, vehicle_y + 36),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (10, 10, 10), 1, cv2.LINE_AA)

        out.write(frame)

    out.release()
    print(f"Generated synthetic border demo video at: {output_path} ({total_frames} frames)")

if __name__ == "__main__":
    create_synthetic_border_video()
