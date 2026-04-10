import ArducamDepthCamera as ac
import cv2
import numpy as np

# 1. Initialize the camera
# Note: On Pi 5, if index 0 fails, try index 8 or check 'libcamera-hello --list-cameras'
cam = ac.ArducamCamera()
#** changed from ac.TOFConnect.CSI to ac.Connection.CSI
if cam.open(ac.Connection.CSI, 0) != 0:
    print("Failed to open camera")
    exit()

# 2. Start the camera
#** changed from ac.TOFOutput.DEPTH to ac.FrameType.DEPTH
cam.start(ac.FrameType.DEPTH)

while True:
    # 3. Capture a frame
    frame = cam.requestFrame(200)
    if frame is not None:
        depth_buf = frame.getDepthData()
        
        # 4. Process depth data for visualization
        # Scale the data to 0-255 for grayscale display
        depth_map = np.clip(depth_buf, 0, 4000) # Limit range to 4 meters
        depth_map = (depth_map / 4000.0 * 255).astype(np.uint8)
        depth_map = cv2.applyColorMap(depth_map, cv2.COLORMAP_JET)

        cv2.imshow("Arducam ToF Depth Map", depth_map)
        
        # Release the frame to prevent memory leaks
        cam.releaseFrame(frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.stop()
cam.close()
cv2.destroyAllWindows()