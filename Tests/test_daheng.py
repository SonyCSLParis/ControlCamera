from ControlCamera import ControlCamera
import cv2
import os


# Define test configuration file and parameters

CAM_PARAMS = {"TriggerMode": "On", #off
             "TriggerSource": "Line0",
              "SensorHeight":2048,
                "SensorWidth":2448} #Software
CONFIG_FILE = "MMconfig/Daheng.json"

# Initialize the camera controller
camera = ControlCamera(CONFIG_FILE, CAM_PARAMS)

# Test parameter update and retrieval
camera.update_param("TriggerMode", "Off")
print("Updated Exposure:", camera.get_param("TriggerMode"))

# Test snapping an image
camera.snap_image()
cv2.imshow("Snapped Image", cv2.normalize(camera.image, None, 255, 0, cv2.NORM_MINMAX, cv2.CV_8UC1))
cv2.waitKey(0)
cv2.destroyAllWindows()

# Test continuous streaming (press 'q' to quit)
print("Starting Continuous Streaming...Press q to exit")
camera.continuous_stream()

# Test video capture
print("Capturing Video...")
camera.snap_video(10)

# Save video
SAVE_PATH = "test_output"
os.makedirs(SAVE_PATH, exist_ok=True)
camera.save_video(SAVE_PATH)

print("Test Completed Successfully!")