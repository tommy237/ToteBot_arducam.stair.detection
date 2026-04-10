import cv2 #install opencv-python
import numpy as np
import threading as thr
from line_data import Line,Point
from typing import Any,List


#// ============ SETTINGS ============ //#
camName:str = "Stair Detection Camera"

detTxt:str =     "stairs omg!1!"
detFont:int =    cv2.FONT_HERSHEY_SIMPLEX
detClr =         (0,0,255) #/ B, G, R
ndetClr =        (170,255,0)
txtPadding:int = 10
blurThick:int  = 7

quitKeyCode:chr = 'q'


#// ============ AUTO VARS ============ //#
#// do not touch these pls, 
# or you'll ruin the program
cursorPos = (0,0)  #/ Automatic Point
sigma =     .25    #/ Constant
horizDeg  = 5



# _____________________________________________________________________
#// DEFINITION: Callback event for mouse movement in the cv2 window. //
def mousePos(event:int,x:int,y:int,flags:int,param:Any|None):
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

        #               _________________________               #
        #_______________| S O B E L   O P E R S |_______________#
        #|_____________________________________________________|#
        blurredFrame=cv2.GaussianBlur(src=grayFrame,ksize=(blurThick,blurThick),sigmaX=0)
        sobelY=cv2.Sobel(src=blurredFrame,ddepth=cv2.CV_64F,dx=0,dy=1,ksize=3)
        sobelYabsolute=np.absolute(sobelY)
        sobel8u=np.uint8(sobelYabsolute)
        binarySobel=cv2.threshold(sobel8u,120,255,cv2.THRESH_BINARY)[1]
        
        #               _________________________               #
        #_______________| C A N N Y   E D G E S |_______________#
        #|_____________________________________________________|#
        #// Used to avoid lighting issues when captured in a dark/light room.
        # median=np.median(binarySobel)
        # lowThresh=int(max(0,(1.0-sigma)*median))
        # highThresh=int(min(255,(1.0+sigma)*median))
        # cannyEdges=cv2.Canny(image=blurredFrame,
        #                      threshold1=lowThresh,
        #                      threshold2=highThresh)
        
        #               _________________________               #
        #_______________| H O U G H   L I N E S |_______________#
        #|_____________________________________________________|#
        #           rho:  distance resolution in pixels.
        #         theta:  angle resolution in radians.
        #     threshold:  amount of randomized points needed to form a line.
        # minlineLength:  amount of pixels needed to validate the line.
        #    maxLineGap:  the allowed gap between points in the same line.
        houghLines=cv2.HoughLinesP(image=binarySobel,rho=1,theta=np.pi/180,
                                   threshold=100,minLineLength=100,maxLineGap=20)
        horizCount:int=0 #// How many horizontal lines have we counted?
        preLines=[]
        lines:List[Line]=[]
        detLines:List[Line]=[]
        if (houghLines is not None):
            for hLine in houghLines:
                x1,y1,x2,y2=hLine[0] #// Slope points

                #// Offsets the line y-positions to align with detected edges.
                #// Because camera should only capture bottom 60%, an offset must be added.
                y1Offset:int=y1+startHeight
                y2Offset:int=y2+startHeight
                
                rise:float=y2Offset-y1Offset #// Distance in height
                run:float=x2-x1              #// Distance in length
                angle:float=np.abs(np.degrees(np.arctan2(rise,run)))
                #// Are we sure these lines are close to purely horizontal?
                if (angle<horizDeg or abs(angle-180)<horizDeg):
                    
                    #// TODO: Make short, broken-up lines combine into a single long line.
                    slope=(rise/run) if run!=0 else 999
                    yIntercept=y1Offset-slope*x1
                    if abs(slope)<0.1:
                        preLines.append({
                            "slope":slope,
                            "yInt":yIntercept,
                            "x1":x1,"y1":y1Offset,
                            "x2":x2,"y2":y2Offset
                            })
                    #// End TODO

        preLines.sort(key=lambda x: x['yInt'])
        if preLines:
            currentLine=preLines[0]
            for i in range(1,len(preLines)):
                nextLine=preLines[i]
                inThreshold:bool=abs(nextLine["yInt"]-currentLine["yInt"])<20
                if inThreshold:
                    currentLine["x1"]=min(currentLine["x1"],nextLine["x1"])
                    currentLine["x2"]=max(currentLine["x2"],nextLine["x2"])
                    currentLine["y1"]=(currentLine["y1"]+nextLine["y1"])//2
                    currentLine["y2"]=currentLine["y1"]
                else:
                    lines.append(Line(
                        pt1=Point(currentLine["x1"],currentLine["y1"]),
                        pt2=Point(currentLine["x2"],currentLine["y2"])))
                    currentLine=nextLine
            lines.append(Line(
                    pt1=Point(currentLine["x1"],currentLine["y1"]),
                    pt2=Point(currentLine["x2"],currentLine["y2"])))
                
        upstairPoints:int=0
        downstairPoints:int=0

        #// If there are more than 2 lines in general.
        if (len(lines)>2):
            #// Sorted array of lines that reach the closest to top of the viewport.
            lines.sort(key=lambda x:x.getMidpoint(),reverse=True)
            lastGap=0
            lastLen=0
            for i in range(len(lines)):

                # ___________ GAP-CHECKING ___________ #
                currentLine:Line=lines[i-1]
                nxtLine:Line=lines[i]
                cLm=currentLine.getMidpoint()
                nLm=nxtLine.getMidpoint()

                #// distance between both lines using the midpoint.
                gapDist:int=np.sqrt((nLm.x-cLm.x)**2+(nLm.y-cLm.y)**2)  
                #// difference between the line lengths (signs determines stair direction).
                lenDiff:int=nxtLine.getLength()-currentLine.getLength()

                #// TODO: Expand this section
                #// This helps determine if gaps 
                # geometrically increase/decrease.
                if (gapDist<lastGap*1.1):
                    lengthMargin=lenDiff-lastLen
                    if (lengthMargin>0):
                        upstairPoints+=1
                    elif (lengthMargin<0):
                        downstairPoints+=1
                    if (abs(lenDiff)>5):
                        if currentLine not in detLines:
                            detLines.append(currentLine)
                        detLines.append(nxtLine)

                lastGap=gapDist
                lastLen=lenDiff
                #// End TODO

        #// A threshold for good stairs require 
        # more than 2 horizontal lines detecting 
        # stair nosings.
        isUpstairs:bool=(upstairPoints>2)
        isDownstairs:bool=(downstairPoints>2)
        isStairs:bool=(isUpstairs or isDownstairs)

        #// If there's potential upstairs or downstairs.
        if isStairs:

            # ___________ DETECTED LINES DISPLAYING ___________ #
            for line in lines:
                isDetected=line in detLines #// If that line is detected for stairs.
                color=detClr if isDetected else ndetClr
                point1=line.Point1.toTuple()
                point2=line.Point2.toTuple()
                cv2.line(img=frame,pt1=point1,
                         pt2=point2,color=color,
                         thickness=2)
            
            # ___________ TEXT-BOX LABELING ___________ #
            (txtWidth,txtHeight),baseline=cv2.getTextSize(text=detTxt,
                                                          fontFace=detFont,
                                                          fontScale=1,thickness=3)
            txtPosX,txtPosY=(frameWidth-txtWidth)-15,(frameHeight)-15
            boxMin=((txtPosX)-txtPadding,(txtPosY-txtHeight)-txtPadding)         #// Upper left point
            boxMax=((txtPosX+txtWidth)+txtPadding,(txtPosY+baseline)+txtPadding) #// Bottom right point
            cv2.rectangle(img=frame,pt1=boxMin,pt2=boxMax,color=(0,0,0),thickness=-1)
            cv2.putText(img=frame,text=detTxt,org=(txtPosX,txtPosY),fontFace=detFont,
                        fontScale=1,color=detClr,thickness=3)
            
        else:

            # ___________ LINES DISPLAYING ___________ #
            for line in lines:
                cv2.line(img=frame,pt1=line.Point1.toTuple(),
                         pt2=line.Point2.toTuple(),color=ndetClr,
                         thickness=3)

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