# makeScooterDemoVideo.py --  Combine images from scooter with output file 
#                         to create video for customer demo
#
# makeScooterDemoVideo.py inputFolder 



import os
import cv2, sys
import numpy as np
import time

# define image classifier thresholds for sidewalk detection
sw_thresh = 0.6
street_thresh = 0.6
cw_thresh = 0.6
bk_thres = 0.6
sw_filt_len = 6
odo_scale = 15/600

# Define raw data and output file formats 
rawf = {'frame' : 0,	'time' : 1, 'gps' : 2, 'imu' : 8, 'odo' : 17, 'annotate' : 19}
outf = {'frame' : 0, 'label' : 1, 'class' : 2, 'swFlag' : 8, 'pos' : 9, 'vel' : 12}

# define image classes, these must be alphabetical to match keras API 
label_dict = {'bike_lane' : 0, 'crosswalk' : 1, 'side' : 2, 'street' : 3}


print("\n\nPress 'q' to quit, or <space> to pause/continue\n\n")

# Check command line arguments
if len(sys.argv) > 1:
    dirIn = sys.argv[1]
else:
    raise Exception('Input Folder Missing')
    
classFlag = 1
    
# load files into arrays
try:
    out = np.genfromtxt(dirIn + '/out_data.txt', delimiter=',')
except:
    raise Exception('Data Output File not found')
if os.path.exists(dirIn + '/raw_data.txt'):    
    raw = np.genfromtxt(dirIn + '/raw_data.txt', delimiter=',')
else:
    raw = np.zeros((len(out),rawf['annotate']+1))

# pull data from arrays
img_nums = out[:, outf['frame']]
img_pre = img_nums[0]//1e5 * 1e5
cw_scores = out[:, outf['class'] + label_dict['crosswalk']]
sw_scores = out[:, outf['class'] + label_dict['side']]
street_scores = out[:, outf['class'] + label_dict['street']]
bike_scores = out[:, outf['class'] + label_dict['bike_lane']]
speed = raw[:,rawf['odo']] * odo_scale
    
# Define the codec and create VideoWriter object for output video
videoFileOut=dirIn + '/' + os.path.basename(dirIn) + '.mp4'
fps=5.0;
(w,h) = (640,480)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
videoOut = cv2.VideoWriter(videoFileOut,fourcc, fps, (w,h))
font = cv2.FONT_HERSHEY_SIMPLEX

# get list of images in input folder
fnames = sorted([fname for fname in os.listdir(dirIn)])

# loop through images
ix = 0
for file in fnames:
    print(file)
    if file[-4:] != '.jpg':
        continue
    frame=cv2.imread(dirIn + '/' + file)
    try:
        frame = cv2.resize(frame, (w,h), interpolation = cv2.INTER_AREA)
    except:
        print('Bad frame: %s' % file[-9:-4])
        continue
 
    # find image data in output file
    try:
        img_num = int(file[-19:-13] + file[-12:-10] + file[-9:-4])            
    except:
        img_num = int(file[-9:-4])   # get image prefix from dir name 
    try:
        ix=np.where(img_nums == img_num)[0][0]
    except:
        ix = -1
    
    # add boxes to image
    if ix > 0:
        ixfilt = range(ix - sw_filt_len + 1, ix + 1) 
        if classFlag:
            if np.mean(cw_scores[ixfilt]) > cw_thresh:
                cv2.rectangle(frame, (20,20), (w-20,h-20), (0,255,255), 3) # yellow box
            elif np.mean(street_scores[ixfilt]) > street_thresh:
                cv2.rectangle(frame, (20,20), (w-20,h-20), (0,255,0), 3) # green box
            elif np.mean(sw_scores[ixfilt]) > sw_thresh:
                cv2.rectangle(frame, (20,20), (w-20,h-20), (0,0,255), 3) # red box
            elif np.mean(bike_scores[ixfilt]) > bk_thresh:
                cv2.rectangle(frame, (20,20), (w-20,h-20), (255,0,0), 3) # blue box
            

    # add scooter speed to image  
    cv2.rectangle(frame,(w-160,25),(w-25,54),(255,100,0),cv2.FILLED)
    msg = 'MPH=%d' % max(0, round(speed[ix]))
    cv2.putText(frame, msg, (w-160,50), font, 1.0, (255,255,255), 2, cv2.LINE_AA)

    # write image to video
    videoOut.write(frame)
    cv2.imshow('frame',frame)
    
    # check for user pause or quit
    key=cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # quit
        break
    elif key == ord(' '):  #pause
        cv2.waitKey(0)
    time.sleep(0.05)

videoOut.release()
cv2.destroyAllWindows()