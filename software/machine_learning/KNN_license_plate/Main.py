# Main.py

import numpy as np
import os
import struct

import DetectChars
import DetectPlates
import PossiblePlate

import math
import json
import threading
import cv2 as cv2
import time
import socket
import angle_detection_function

# module level variables ##########################################################################
SCALAR_BLACK = (0.0, 0.0, 0.0)
SCALAR_WHITE = (255.0, 255.0, 255.0)
SCALAR_YELLOW = (0.0, 255.0, 255.0)
SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)
EXIT_FLAG = 0
showSteps = False
LICENSE_PLATE = "367NVE"

#for control algorithm
pixelError = 60
angleError = 20
frameWidth = 640
distanceError = 30
plateWeight = 0.2
platePositionWeight = 0.2
sensorWeight = 0.2
angleWeight = 0.4

offsetpercentageh =0.5
offsetpercentagew = 0.15

# offset value - use to
yoffset = 200
yoffset2 = 500
xoffset = 200
xoffset2 = 600

# ratio between width and height of plate
maxPlateWHRatio = 3.2

EXIT_FLAG = 0
roomba_data = {
    'Battery State': 0,
    'Battery Temperature': 0,
    'Battery Level': 0,
    'Distance': 0,
    'Direction': 0,
    'Current Movement': ord('k')
}

def gstreamer_pipeline (capture_width=640, capture_height=400, display_width=640, display_height=400, framerate=30, flip_method=0, buffer_size=3) :
    return ('nvarguscamerasrc ! ' 
    'video/x-raw(memory:NVMM), '
    'width=(int)%d, height=(int)%d,'
    'format=(string)NV12, framerate=(fraction)%d/1 ! '
    'nvvidconv flip-method=%d ! '
    'video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! '
    'videoconvert ! '
    'video/x-raw, format=(string)BGR ! appsink max-buffers=(int)%d drop=True'  % (capture_width,capture_height,framerate,flip_method,display_width,display_height,buffer_size))

def recieve_loop(client):
    # Receive data dict
    try:
        packet = client.recv(12)
        roomba_data['Battery State'] = ord(packet[1])
        roomba_data['Battery Temperature'] = ord(packet[3])
        # roomba_data['Battery Capacity'] = int.from_bytes(packet[5:7], byteorder='big', signed=False)
        # roomba_data['Battery Level'] = int.from_bytes(packet[8:10], byteorder='big', signed=False)
        capacity = struct.unpack("<H", packet[5:7])[0]
        roomba_data['Battery Level'] = struct.unpack("<H", packet[8:10])[0] * 100 / capacity
        roomba_data['Distance'] = ord(packet[10])
        roomba_data['Direction'] = ord(packet[11])
        print(roomba_data['Distance'])
    except:
        #print("could not receive data packet")
        return 0

###################################################################################################
def main():
    global EXIT_FLAG
    import time
    import cv2

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('192.168.4.1', 1024))
    client.setblocking(False)

    blnKNNTrainingSuccessful = DetectChars.loadKNNDataAndTrainKNN()         # attempt KNN training
    if blnKNNTrainingSuccessful == False:                               # if KNN training was not successful
        print("\nerror: KNN traning was not successful\n")  # show error message
        return                                                          # and exit program

    angle_detection_function.setup_function()
    # end if
    # cap = cv2.VideoCapture('licPlateVideo/IMG_0326.MOV')
    # cap = cv2.VideoCapture('http://192.168.4.1/html/cam_pic_new.php?')

    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

    plateLocationX = 0


    if (cap.isOpened()):
        window_handle = cv2.namedWindow('CSI Camera', cv2.WINDOW_AUTOSIZE)
    else:
        print("Cap object not opened\n")
        quit()

    while cv2.getWindowProperty('CSI Camera', 0) >= 0:
        ret, imgOriginalScene = cap.read()

        starttime = cv2.getTickCount()
        plateLocationX_result,listChar, angle, confident, image_license_only = readPlate(imgOriginalScene)
        if angle is not "None":
            print(angle)
        endtime = cv2.getTickCount()
        time = (endtime-starttime)/cv2.getTickFrequency()
        # if time > 0.08:
            # print("readPlate time: " + str(time))

        # print("Receive loop \n")
        recieve_loop(client)

        if plateLocationX_result is not 0:
            plateLocationX = plateLocationX_result
            plateLocationX = plateLocationX - (frameWidth / 2)
            #print(plateLocationX)

        else:
            plateLocationX = -1

        cv2.imshow('CSI Camera', imgOriginalScene)
        if image_license_only is not None:
            cv2.imshow('Cropped Plate', image_license_only)


############################################################################################
        # test control algorithm
        distance, direction = roomba_data['Distance'], chr(roomba_data['Direction'])

        #define weights
        rightWeight = 0
        leftWeight = 0


        # get lead vehicle angle

        # NON WEIGHTED PRELIMINARY ALGORITHM
        # checks both the average value and the range of the distance sensed

        prev_move = roomba_data['Current Movement']
        if (plateLocationX >= pixelError) and plateLocationX != -1:
            roomba_data['Current Movement'] = ord('d')
            if prev_move is not roomba_data['Current Movement']:
                client.send("d".encode())
                print("right")
            pass
        elif (plateLocationX <= -pixelError) and plateLocationX != -1:
            roomba_data['Current Movement'] = ord('a')
            if prev_move is not roomba_data['Current Movement']:
                client.send("a".encode())
                print("left")
            pass

        elif distance > distanceError:
            roomba_data['Current Movement'] = ord('w')
            if prev_move is not roomba_data['Current Movement']:
                client.send("w".encode())
                print("forward")
            pass
        elif distance <= distanceError:
            roomba_data['Current Movement'] = ord('s')
            if prev_move is not roomba_data['Current Movement']:
                client.send("s".encode())
                print("stop")
            pass

        # else if a license plate is not detected
        else:
            roomba_data['Current Movement'] = ord('s')
            if prev_move is not roomba_data['Current Movement']:
                #process_cmd(roomba, "s")  # stop
                client.send("s".encode())
                print("stop")
            pass

        ###########################################################
        # # WEIGHTED ALGORITHM
        # if distanceAverage >= 20 and abs(distanceRight - distanceLeft) <= distanceError:
        #     client.send("i")  # drive forward
        # elif distanceAverage <= 15 and abs(distanceRight - distanceLeft) <= distanceError:
        #     client.send("k")  # stop
        #
        # # weights
        #
        # # if plate if detected
        # if plateLocationX != 0:
        #     rightWeight = rightWeight + plateWeight
        #     leftWeight = leftWeight + plateWeight
        #
        # # plate location to determine direction
        # if plateLocationX >= pixelError:
        #     rightWeight = rightWeight + platePositionWeight
        # elif plateLocationX <= pixelError:
        #     leftWeight = leftWeight + platePositionWeight
        #
        # # sensors to determine direction
        # if distanceRight < distanceLeft and abs(distanceRight - distanceLeft) >= distanceError:
        #     rightWeight = rightWeight + sensorWeight
        # elif distanceRight > distanceLeft and abs(distanceRight - distanceLeft) >= distanceError:
        #     leftWeight = leftWeight + sensorWeight
        #
        # # weight of angle from machine learning
        # if angle > angleError and angle < 90:  # 90 is upper limit for turning right
        #     rightWeight = rightWeight + angleWeight
        # elif angle < (360 - angleError) and angle > 270: # 270 is upper limit for turning left
        #     leftWeight = leftWeight + angleWeight
        #
        # if rightWeight > leftWeight:
        #     #turn right
        # elif leftWeight > rightWeight:
        #     #turn left


################################################################################################
        key = chr(cv2.waitKey(20) & 0xFF)
        if key is not 'q' and key is not ('s' or 'w' or 'd' or 'a'):
            pass
        elif (key == 'q') or EXIT_FLAG == 1:
            print("quit")
            client.send('q'.encode())
            #process_cmd(roomba, key.encode())
            EXIT_FLAG = 1
            break
        elif (key == 's' or key == 'w' or key == 'a' or key == 'd'):
            print(key)
            client.send(key.encode())

    cap.release()

# end main
###################################################################################################
def readPlate(imgOriginalScene):
    starttime = cv2.getTickCount()
    #ret, imgOriginalScene  = cap.read()               # open image
    #print('load image:',(cv2.getTickCount()-starttime)/cv2.getTickFrequency())
    #imgOriginalScene = cv2.resize(imgOriginalScene,(800,600))
    #print('resize image:',(cv2.getTickCount()-starttime)/cv2.getTickFrequency())
    #starttime = cv2.getTickCount()


    #if imgOriginalScene is None:                            # if image was not read successfully
    #    print("\nerror: image not read from file \n\n")  # print error message to std out
    #    os.system("pause")                                  # pause so user can see error message
    #    return                                              # and exit program
    imgReduceSearchArea = imgOriginalScene  # not yet implement
    #imgReduceSearchArea = imgOriginalScene[yoffset:yoffset2, xoffset:xoffset2] # limit the searching area to improve reading speed
                                                            # since the vehicle plate only appear at a certain area when
                                                            # following, we can limit search area to 50% area of the
                                                            # frame -> decrease process time significantly
                                                            # NOTE: have too add the off-set value to
    #cv2.imshow('s',imgReduceSearchArea)
    listOfPossiblePlates = DetectPlates.detectPlatesInScene(imgReduceSearchArea)           # detect plates
    # #####################test code#####################################
    #print('location of possible plate:')
    #for i in range(0, len(listOfPossiblePlates)):
    #    print(listOfPossiblePlates[i].rrLocationOfPlateInScene)
    #endtime = cv2.getTickCount()
    #print('process time to get plates list:',(endtime-starttime)/cv2.getTickFrequency())
    #print('end ray test')
    #########################################################################
    listOfPossiblePlates = DetectChars.detectCharsInPlates(listOfPossiblePlates)        # detect chars in plates
    #endtime= cv2.getTickCount()

    #print('finish detect char:',(endtime-starttime)/cv2.getTickFrequency())
    #cv2.imshow("imgOriginalScene", imgOriginalScene)            # show scene image
    intPlateCenterX = 0
    listChar = None
    angle = "None"
    confident=0
    image_license_only = None
    if (len(listOfPossiblePlates) != 0):                          # if no plates were found
                                                       # else
                # if we get in here list of possible plates has at least one plate

                # sort the list of possible plates in DESCENDING order (most number of chars to least number of chars)

        listOfPossiblePlates.sort(key = lambda possiblePlate: len(possiblePlate.strChars), reverse = True)


                # suppose the plate with the most recognized chars (the first plate in sorted by string length descending order) is the actual plate
        licPlate = listOfPossiblePlates[0]
        ((intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight),fltCorrectionAngleInDeg) = licPlate.rrLocationOfPlateInScene
        listChar = licPlate.listChar
        #drawRedRectangleAroundPlate(imgOriginalScene, licPlate, SCALAR_RED)  # draw red rectangle around plate

        #writeLicensePlateCharsOnImage(imgOriginalScene,licPlate)  # write license plate text on the image

        num_chars = len(licPlate.strChars)
        if num_chars is not 0:
            char_width = intPlateWidth/num_chars
            index = licPlate.strChars.find(LICENSE_PLATE)
            if index is not -1:
                #print("got a plate")
                endtime = cv2.getTickCount()
                #print("read KNN time", ((endtime-starttime)/cv2.getTickFrequency()))
                firstCharStart = listChar[index].intBoundingRectX
                firstCharStart = firstCharStart/1.6
                lastCharEnd = listChar[index+5].intBoundingRectX + listChar[index+5].intBoundingRectWidth
                lastCharEnd = lastCharEnd/1.6
                intPlateCenterX = (intPlateCenterX - 0.5 * intPlateWidth) + (lastCharEnd-firstCharStart)*0.5 + firstCharStart

                licPlate.strChars = licPlate.strChars[index:index+6]
                intPlateWidth = lastCharEnd-firstCharStart
                ##################################################3
                #intPlateCenterX+=xoffset
                #intPlateCenterY+=yoffset
                ptPlateCenter = intPlateCenterX, intPlateCenterY
                licPlate.rrLocationOfPlateInScene = (tuple(ptPlateCenter), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg)
            #    cv2.imshow("imgPlate", licPlate.imgPlate)           # show crop of plate and threshold of plate
            #    cv2.imshow("imgThresh", licPlate.imgThresh)
                # if len(licPlate.strChars) == 0:                     # if no chars were found in the plate
                #     print("\nno characters were detected\n\n")  # show message
                #     return                                          # and exit program
                # # end if

                w1 = int((intPlateWidth/2) + intPlateWidth*offsetpercentagew)
                h1 = int((intPlateHeight/2) + intPlateHeight*offsetpercentageh)
                # crop the image of the plate for angle detection function
                image_license_only = imgOriginalScene[
                                     (int(intPlateCenterY-h1)):int((intPlateCenterY+h1)),
                                     (int(intPlateCenterX-w1)):int((intPlateCenterX+w1))]
                image_license_only = image_license_only.copy()
                angle, confident = angle_detection_function.angle_detection_function(image_license_only)
                #drawRedRectangleAroundPlate(imgOriginalScene, licPlate, SCALAR_RED)             # draw red rectangle around plate

                #writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)           # write license plate text on the image

                cv2.circle(imgOriginalScene, (int(intPlateCenterX), int(intPlateCenterY)), 10, (0, 255, 0), 2)
            else:
                intPlateCenterX = 0
    # end if else





    return intPlateCenterX, listChar, angle, confident, image_license_only
    #end ReadPlate function
###################################################################################################
def drawRedRectangleAroundPlate(imgOriginalScene, licPlate, color):

    p2fRectPoints = cv2.boxPoints(licPlate.rrLocationOfPlateInScene)            # get 4 vertices of rotated rect
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), color, 2)         # draw 4 red lines
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), color, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), color, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), color, 2)
# end function

###################################################################################################
def writeLicensePlateCharsOnImage(imgOriginalScene, licPlate):
    ptCenterOfTextAreaX = 0                             # this will be the center of the area the text will be written to
    ptCenterOfTextAreaY = 0

    ptLowerLeftTextOriginX = 0                          # this will be the bottom left of the area that the text will be written to
    ptLowerLeftTextOriginY = 0

    sceneHeight, sceneWidth, sceneNumChannels = imgOriginalScene.shape
    plateHeight, plateWidth, plateNumChannels = licPlate.imgPlate.shape

    intFontFace = cv2.FONT_HERSHEY_SIMPLEX                      # choose a plain jane font
    fltFontScale = float(plateHeight) / 30.0                    # base font scale on height of plate area
    intFontThickness = int(round(fltFontScale * 1.5))           # base font thickness on font scale

    textSize, baseline = cv2.getTextSize(licPlate.strChars, intFontFace, fltFontScale, intFontThickness)        # call getTextSize

            # unpack roatated rect into center point, width and height, and angle
    ( (intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg ) = licPlate.rrLocationOfPlateInScene

    intPlateCenterX = int(intPlateCenterX)              # make sure center is an integer
    intPlateCenterY = int(intPlateCenterY)

    ptCenterOfTextAreaX = int(intPlateCenterX)         # the horizontal location of the text area is the same as the plate

    if intPlateCenterY < (sceneHeight * 0.75):                                                  # if the license plate is in the upper 3/4 of the image
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) + int(round(plateHeight * 1.6))      # write the chars in below the plate
    else:                                                                                       # else if the license plate is in the lower 1/4 of the image
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) - int(round(plateHeight * 1.6))      # write the chars in above the plate
    # end if

    textSizeWidth, textSizeHeight = textSize                # unpack text size width and height

    ptLowerLeftTextOriginX = int(ptCenterOfTextAreaX - (textSizeWidth / 2))           # calculate the lower left origin of the text area
    ptLowerLeftTextOriginY = int(ptCenterOfTextAreaY + (textSizeHeight / 2))          # based on the text area center, width, and height

            # write the text on the image
    cv2.putText(imgOriginalScene, licPlate.strChars, (ptLowerLeftTextOriginX, ptLowerLeftTextOriginY), intFontFace, fltFontScale, SCALAR_YELLOW, intFontThickness)


# end function

###################################################################################################
if __name__ == "__main__":
    main()

















