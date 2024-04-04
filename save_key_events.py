from key_clipper.keyclipwriter import KeyClipWriter
from picamera2 import Picamera2
import argparse
import datetime
import time
import imutils
import cv2
import bucket

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1640, 922)}))
picam2.start()

def upload_pic(bucket_name, file_path, blob_name='screenshot'):
    print(bucket.upload_to_bucket(bucket_name, blob_name, file_path, no_cache=True))
    print(f'Uploaded {file_path} to {bucket_name}')

backSub = cv2.createBackgroundSubtractorMOG2()
def mov_detect(frame,avg):
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    if avg is None:
        print("calculando background")
        avg = gray.copy().astype("float")
    cv2.accumulateWeighted(gray,avg,0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    frameDelta = cv2.GaussianBlur(frameDelta, (25, 25), 0)
    frameDelta = cv2.erode(frameDelta, None, iterations=11)
    thresh = cv2.threshold(frameDelta, 5,255,cv2.THRESH_BINARY)[1]
    #thresh = cv2.dilate(thresh, None, iterations=10)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    #cv2.imshow("frameDelta",thresh)
	# loop over the contours
    text="no"
    i=0
    for c in cnts:
        i+=1
		# and update the text
        if cv2.contourArea(c) < 500:
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        print("movimiento")
        text = "Occupied"
    #cv2.imshow("frame",frame)
    return avg,i,thresh
    # frame=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # frame=cv2.GaussianBlur(frame, (31, 31), 0) 
    # fg_mask = backSub.apply(frame)

    # retval, mask_tresh = cv2.threshold(fg_mask, 180, 255, cv2.THRESH_BINARY)
    
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    # mask_eroded = cv2.morphologyEx(mask_tresh, cv2.MORPH_OPEN, kernel)

    # contours, hierarchy = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # #cv2.imshow("mask", fg_mask)
    # min_contour_area = 700
    # large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
    # frame_out = frame.copy()
    # count = 0
    # for cnt in large_contours:
    #     x, y, w, h = cv2.boundingRect(cnt)
    #     frame_out = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 200), 3)
    #     count += 1

    # return count, mask_tresh

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="output",
	help="path to output directory")
ap.add_argument("-f", "--fps", type=int, default=20,
	help="FPS of output video")
ap.add_argument("-c", "--codec", type=str, default="mp4v",
    help="codec of output video")
ap.add_argument("-b", "--buffer-size", type=int, default=32,
	help="buffer size of video clip writer")
args = vars(ap.parse_args())

print("[INFO] starting video stream...")
#vs = VideoStream(src=2).start()
vs=cv2.VideoCapture(2)
time.sleep(2.0)

kcw = KeyClipWriter(bufSize=args["buffer_size"])
consecFrames = 0
start_time = time.time()+12
i = 1
avg = None
p=None
while True:
    _, frame = vs.read()
    original_frame = frame.copy()
    avg, count, dect_frame = mov_detect(frame,avg)
    updateConsecFrames = True

    current_time = time.time()

    if count > 1 and current_time - start_time >= 15:
        print("guarda")
        updateConsecFrames = False
        consecFrames = 0
        if not kcw.recording:
            timestamp = datetime.datetime.now()
            p = "{}/{}.mp4".format(args["output"], timestamp)
            i += 1
            #kcw.start(p, cv2.VideoWriter_fourcc(*args["codec"]), args["fps"])
            kcw.start(p, cv2.VideoWriter_fourcc(*'h264'), args["fps"])

    if updateConsecFrames:
        consecFrames += 1
    
    kcw.update(original_frame)

    if kcw.recording and consecFrames == args["buffer_size"]:
        start_time = time.time()
        kcw.finish()
        leaf = picam2.capture_array()
        cv2.imwrite("output/leaf.jpg",leaf)
        upload_pic('test-aiden-user-upload', "output/leaf.jpg", 'image.jpg')
        upload_pic('test-img-aiden', p, 'video')

    #cv2.imshow("Frame", dect_frame)
    #if count > 0:
        #print("[INFO] Motion Detected. Squares = ", count)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if kcw.recording:
	kcw.finish()

cv2.destroyAllWindows()
vs.release()
#vs.stop()