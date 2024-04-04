from key_clipper.keyclipwriter import KeyClipWriter
from imutils.video import VideoStream
import argparse
import datetime
import time
import cv2

backSub = cv2.createBackgroundSubtractorMOG2()

def mov_detect(frame):
    fg_mask = backSub.apply(frame)

    retval, mask_tresh = cv2.threshold(fg_mask, 180, 255, cv2.THRESH_BINARY)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_eroded = cv2.morphologyEx(mask_tresh, cv2.MORPH_OPEN, kernel)

    contours, hierarchy = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_contour_area = 700
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
    frame_out = frame.copy()
    count = 0
    for cnt in large_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        frame_out = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 200), 3)
        count += 1

    return count, frame_out

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="output",
	help="path to output directory")
ap.add_argument("-f", "--fps", type=int, default=20,
	help="FPS of output video")
ap.add_argument("-c", "--codec", type=str, default="MJPG",
	help="codec of output video")
ap.add_argument("-b", "--buffer-size", type=int, default=32,
	help="buffer size of video clip writer")
args = vars(ap.parse_args())

print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

kcw = KeyClipWriter(bufSize=args["buffer_size"])
consecFrames = 0
start_time = time.time()
i = 1

while True:
    frame = vs.read()
    original_frame = frame.copy()
    count, dect_frame = mov_detect(frame)
    updateConsecFrames = True

    current_time = time.time()

    if count > 0 and current_time - start_time >= 2:
        updateConsecFrames = False
        consecFrames = 0
        if not kcw.recording:
            timestamp = datetime.datetime.now()
            p = "{}/{}.avi".format(args["output"], f"test_{i}")
            i += 1
            kcw.start(p, cv2.VideoWriter_fourcc(*args["codec"]), args["fps"])

    if updateConsecFrames:
        consecFrames += 1
    
    kcw.update(original_frame)

    if kcw.recording and consecFrames == args["buffer_size"]:
        kcw.finish()

    # cv2.imshow("Frame", dect_frame)
    if count > 0:
        print("[INFO] Motion Detected. Squares = ", count)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if kcw.recording:
	kcw.finish()

cv2.destroyAllWindows()
vs.stop()
