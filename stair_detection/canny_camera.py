import cv2 #install opencv-python
import numpy as np
import threading as thr

#// ============ SETTINGS ============ //#
camName="Stair Detection Camera"
detTxt="stairs omg!1!"
detFont=cv2.FONT_HERSHEY_SIMPLEX
detClr=(0,0,255) #// B, G, R
ndetClr=(170,255,0)
quitKeyCode='q'

#// ============ AUTO VARS ============ //#
#// do not touch these pls, 
# or you'll ruin the program
cursorPos=(0,0)  #/ Automatic Point
sigma=.33        #/ Constant

# _____________________________________________________________________
#// DEFINITION: Callback event for mouse movement in the cv2 window. //
def mousePos(event:int,x:int,y:int,flags:int,param):
    global cursorPos
    if (event==cv2.EVENT_MOUSEMOVE):
        cursorPos=(x,y)

def mousePos_putText(imgP:cv2.typing.MatLike,textP:str,pos:tuple[int,int]):
    cv2.putText(img=imgP,text=textP,org=pos,fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.5,color=(255,255,255),thickness=1,lineType=cv2.LINE_8)

# _______________________________________________________________________
#// DEFINITION: Loop module for the camera's active detection program. //
def cameraMod():
    global camName,sigma
    # ___________ OPENCV INITIALIZATION ___________ #
    #// This window must exist for other callbacks to work below.
    cv2.namedWindow(winname=camName)
    cv2.setMouseCallback(
        window_name=camName,
        on_mouse=mousePos)
    camera=cv2.VideoCapture(index=1,apiPreference=cv2.CAP_DSHOW)
    if (not camera.isOpened()):
        exit()
    while True:

        # ___________ CAMERA CAPTURE ___________ #
        working,frame=camera.read()
        #// Ensures that program doesn't run when camera fails to capture.
        if (not working):
            break 
        frameHeight,frameWidth=frame.shape[:2] #// Dimensions of cv2 window
        startHeight=int(frameHeight*0.4)       #// Frame cropping (new y-origin)
        roi=frame[startHeight:,:]              #// Region Of Interest
        grayFrame=cv2.cvtColor(src=roi,code=cv2.COLOR_BGR2GRAY)
        blurredFrame=cv2.GaussianBlur(src=grayFrame,ksize=(5,5),sigmaX=0)
        
        #               _________________________               #
        #_______________| C A N N Y   E D G E S |_______________#
        #|_____________________________________________________|#
        #// Used to avoid lighting issues when captured in a dark/light room.
        median=np.median(blurredFrame)
        lowThresh=int(max(0,(1.0-sigma)*median))
        highThresh=int(min(255,(1.0+sigma)*median))
        cannyEdges=cv2.Canny(image=blurredFrame,
                             threshold1=lowThresh,
                             threshold2=highThresh)
        
        #               _________________________               #
        #_______________| H O U G H   L I N E S |_______________#
        #|_____________________________________________________|#
        houghLines=cv2.HoughLinesP(image=cannyEdges,rho=1,theta=np.pi/180,
                                   threshold=100,minLineLength=100,maxLineGap=10)
        horizCount=0 #// How many horizontal lines have we counted?
        lines={}
        if (houghLines is not None):
            for hLine in houghLines:
                x1,y1,x2,y2=hLine[0] #// Slope points
                rise=y2-y1           #// Distance in height
                run=x2-x1            #// Distance in length
                angle=np.abs(np.degrees(np.arctan2(rise,run)))
                #// Are we sure these lines are close to purely horizontal?
                if (angle<5 or abs(angle-180)<5):
                    #// Offsets the line y-positions to align with detected edges.
                    #// Because camera should only capture bottom 60%, an offset must be added.
                    y1Offset=y1+startHeight
                    y2Offset=y2+startHeight
                    length=np.sqrt(((x2-x1)**2)+((y2Offset-y1Offset)**2))
                    avgY=(y1Offset+y2Offset)//2
                    lines[horizCount]={
                        'Point1':(x1,y1Offset),
                        'Point2':(x2,y2Offset),
                        'Midpoint':avgY,
                        'Length':length
                    }
                    horizCount+=1
                    color=detClr if True else ndetClr
                    cv2.line(img=frame,pt1=(x1,y1Offset),
                             pt2=(x2,y2Offset),color=color,
                             thickness=3)

        if (len(lines)>=3):
            keys=list(lines.keys())
            sortedIndices=sorted(keys,
                                 key=lambda k:lines[k]['Midpoint'],
                                 reverse=True)
            upPoints=0
            downPoints=0
            gaps=[]
            for i in range(len(sortedIndices)-1):
                currLn=lines[sortedIndices[i]]
                nxtLn=lines[sortedIndices[i+1]]
                gap=(currLn['Midpoint']-nxtLn['Midpoint'])
                lengthDiff=(currLn['Length']-nxtLn['Length'])
                gaps.append({
                    'Distance':gap,
                    'Difference':lengthDiff,
                    'Lines':(currLn,nxtLn)
                    })
                if (gap>10):
                    if (lengthDiff>5): upPoints+=1
                    elif (lengthDiff<-5): downPoints+=1
            isStairs=upPoints>2 or downPoints>2
            if isStairs:
                (txtWidth,txtHeight),baseline=cv2.getTextSize(text=detTxt,
                                                      fontFace=detFont,
                                                      fontScale=1,thickness=3)
                txtPosX,txtPosY=frameWidth-txtWidth-15,frameHeight-15
                boxMin=(txtPosX-10,txtPosY-txtHeight-10)         #// Upper left point
                boxMax=(txtPosX+txtWidth+10,txtPosY+baseline+10) #// Bottom right point
                cv2.rectangle(img=frame,pt1=boxMin,
                            pt2=boxMax,color=(0,0,0),
                            thickness=-1)
                cv2.putText(img=frame,text=detTxt,
                            org=(txtPosX,txtPosY),
                            fontFace=detFont,fontScale=1,
                            color=detClr,thickness=3)

        # ___________ MOUSE LABELING ___________ #
        localX,localY=cursorPos[0],cursorPos[1]
        cv2.rectangle(img=frame,pt1=(10,10),pt2=(95,55),
                      color=(0,0,0),thickness=-1)
        mousePos_putText(imgP=frame,textP=f"X: {localX}px",pos=(15,25))
        mousePos_putText(imgP=frame,textP=f"Y: {localY}px",pos=(15,45))

        # ___________ FRAME DISPLAY ___________ #
        cv2.imshow(winname=camName,mat=frame)
        
        # ___________ INPUT CAPTURE ___________ #
        if (cv2.waitKey(delay=1) & 0xFF==ord(quitKeyCode)):
            break
    camera.release()
    cv2.destroyAllWindows()

#// ============ MAIN PROGRAM ============ //#
cameraT=thr.Thread(target=cameraMod)
cameraT.start()
cameraT.join()