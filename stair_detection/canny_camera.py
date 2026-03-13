import cv2 #install opencv-python
import numpy as np
import threading as thr

#// SETTINGS
camName="Stair Detection Camera"

#// AUTOMATIC VARIABLES
#// do not touch these pls, 
# or you'll ruin the program
cursorPos=(0,0)

#// DEFINITION: Callback event for mouse movement in the cv2 window.
def mousePos(event:int,x:int,y:int,flags:int,param:Any|None):
    global cursorPos
    if event==cv2.EVENT_MOUSEMOVE:
        cursorPos=(x,y)

def mousePos_putText(imgP:cv2.typing.MatLike,textP:str,pos:tuple[int,int]):
    cv2.putText(img=imgP,text=textP,org=pos,fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.5,color=(255,255,255),thickness=1,lineType=cv2.LINE_AA)

#// DEFINITION: Loop module for the camera's active detection program.
def cameraMod():
    global camName
    # ___________ CAMERA_VIEW2 INITIALIZATION ___________ #
    #// This window must exist for other callbacks to work below.
    cv2.namedWindow(winname=camName)
    cv2.setMouseCallback(
        window_name=camName,
        on_mouse=mousePos)
    camera=cv2.VideoCapture(index=0)
    if not camera.isOpened():
        exit()
    while True:

        # ___________ CAMERA CAPTURE ___________ #
        working,frame=camera.read()
        #// Ensures that program doesn't run when camera fails to capture.
        if not working:
            break 
        grayFrame=cv2.cvtColor(src=frame,code=cv2.COLOR_BGR2GRAY)
        blurredFrame=cv2.GaussianBlur(src=grayFrame,ksize=(5,5),sigmaX=0)
        
        #_______________________________________________________#
        # --------------- C A N N Y   E D G E S --------------- #
        #_______________________________________________________#
        #// Used to avoid lighting issues when captured in a dark/light room.
        median=np.median(blurredFrame)
        sigma=.33 #// Automatic constant
        lowThresh=int(max(0,(1.0-sigma)*median))
        highThresh=int(min(255,(1.0+sigma)*median))
        cannyEdges=cv2.Canny(image=blurredFrame,
                             threshold1=lowThresh,
                             threshold2=highThresh)
        
        #_______________________________________________________#
        # --------------- H O U G H   L I N E S --------------- #
        #_______________________________________________________#
        houghLines=cv2.HoughLinesP(image=cannyEdges,rho=1,theta=np.pi/180,
                                   threshold=100,minLineLength=100,maxLineGap=10)
        horizCount=0 #// How many horizontal lines have we counted?
        if houghLines is not None:
            for line in houghLines:
                x1,y1,x2,y2=line[0] #// Slope points
                rise=y2-y1 #// Distance in height
                run=x2-x1 #// Distance in length
                angle=np.abs(np.degrees(np.arctan2(rise,run)))
                if angle<5 or abs(angle-180)<5:
                    horizCount+=1
                    cv2.line(img=cannyEdges,pt1=(x1,y1),pt2=(x2,y2),
                             color=(0,255,120),thickness=2)
        if horizCount>=2: #// We have detected potential stairs!
            cv2.putText(img=cannyEdges,text="Hey! stairs omg",
                        org=(50,50),fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=1,color=(0,255,120),thickness=1)
            
        # ___________ MOUSE LABELING ___________ #
        localX,localY=cursorPos[0],cursorPos[1]
        mousePos_putText(imgP=cannyEdges,textP=f"X: {localX}px",pos=(20,30))
        mousePos_putText(imgP=cannyEdges,textP=f"Y: {localY}px",pos=(20,50))

        # ___________ FRAME DISPLAY ___________ #
        cv2.imshow(winname=camName,mat=cannyEdges)
        
        # ___________ INPUT CAPTURE ___________ #
        if cv2.waitKey(delay=1) & 0xFF==ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()

cameraT=thr.Thread(target=cameraMod)
cameraT.start()
cameraT.join()