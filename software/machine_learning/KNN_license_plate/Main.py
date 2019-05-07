# Main.py

import cv2
import numpy as np
import os
import struct

import DetectChars
import DetectPlates
import PossiblePlate
import socket
import time
import math
import msvcrt
import json
import threading
import cv2

# module level variables ##########################################################################
SCALAR_BLACK = (0.0, 0.0, 0.0)
SCALAR_WHITE = (255.0, 255.0, 255.0)
SCALAR_YELLOW = (0.0, 255.0, 255.0)
SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)
EXIT_FLAG = 0
showSteps = False
LICENSE_PLATE = "824LXW"

#for control algorithm
pixelError = 35
angleError = 20
frameWidth = 512
distanceError = 10

plateWeight = 0.2
platePositionWeight = 0.2
sensorWeight = 0.2
angleWeight = 0.4

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
    'Angle': 0,
    'Distance Left': 0,
    'Distance Right': 0,
    'Direction': 0,
    'Current Movement': ord('k')
}


def unpack_dict(data_dict):
    for key in data_dict.keys():
        roomba_data[key] = data_dict[key]


def command_loop():
    global EXIT_FLAG

    if msvcrt.kbhit():
        key = msvcrt.getch().decode('UTF-8')
        print(key)
        if key:
            client.send(key.encode())
            if key == 'q':
                client.close()
                EXIT_FLAG = 1


def video_grabber():
    global EXIT_FLAG
    global frames
    cap = cv2.VideoCapture('http://192.168.4.1/html/cam_pic_new.php?')
    while True:
        ret, frame = cap.read()
        frames.put(frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')) or EXIT_FLAG == 1:
            EXIT_FLAG = 1
            cv2.destroyAllWindows()
            break


def video_loop():
    global EXIT_FLAG
    cap = cv2.VideoCapture('http://192.168.4.1/html/cam_pic_new.php?')
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Our operatoins on the frame come here
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Display the resulting frame
        cv2.imshow('frame', frame)
        # Quit procedure
        if (cv2.waitKey(1) & 0xFF == ord('q')) or EXIT_FLAG == 1:
            EXIT_FLAG = 1
            cv2.destroyAllWindows()
            break


def recieve_loop(client):
    # Receive data dict
    try: recv = client.recv(1).decode()
    except:
        return 0
    if recv == '<':
        client.setblocking(True)
        #num_bytes = int.from_bytes(client.recv(1), byteorder='big', signed=False)
        num_bytes = ord(client.recv(1))
        recv = client.recv(1).decode()
        if recv == '>':
            packet = client.recv(num_bytes)
            roomba_data['Battery State'] = ord(packet[1])
            roomba_data['Battery Temperature'] = ord(packet[3])
            #roomba_data['Battery Capacity'] = int.from_bytes(packet[5:7], byteorder='big', signed=False)
            #roomba_data['Battery Level'] = int.from_bytes(packet[8:10], byteorder='big', signed=False)
            capacity = struct.unpack("<H", packet[5:7])[0]
            roomba_data['Battery Level'] = struct.unpack("<H", packet[8:10])[0] * 100 / capacity
            roomba_data['Angle'] = ord(packet[10])
            roomba_data['Distance Left'] = ord(packet[11])
            roomba_data['Distance Right'] = ord(packet[12])
            roomba_data['Direction'] = ord(packet[13])
            print(roomba_data)
            client.setblocking(False)

###################################################################################################
def main():
    global EXIT_FLAG
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('192.168.4.1', 1024))
    client.setblocking(False)

    blnKNNTrainingSuccessful = DetectChars.loadKNNDataAndTrainKNN()         # attempt KNN training
    if blnKNNTrainingSuccessful == False:                               # if KNN training was not successful
        print("\nerror: KNN traning was not successful\n")  # show error message
        return                                                          # and exit program
    # end if
    # cap = cv2.VideoCapture('licPlateVideo/IMG_0326.MOV')
    cap = cv2.VideoCapture('http://192.168.4.1/html/cam_pic_new.php?')
    plateLocationX = 0
    while(cap.isOpened()):
        starttime = cv2.getTickCount()
        ret, imgOriginalScene = cap.read()
        endtime = cv2.getTickCount()
        time = (endtime-starttime)/cv2.getTickFrequency()
        if time > 0.015:
            #print("Cap.read time: " + str(time))
            pass
        plateLocationX_result,listChar = readPlate(imgOriginalScene)
        recieve_loop(client)

        if plateLocationX_result is not 0:
            plateLocationX = plateLocationX_result
            plateLocationX = plateLocationX - (frameWidth / 2)
            #print(plateLocationX)
        # reads the location of the license plate

        #recieve_loop(client)
        cv2.imshow('output', imgOriginalScene)


############################################################################################
        # test control algorithm
        angle, distanceRight, distanceLeft, direction = roomba_data['Angle'], roomba_data['Distance Right'], roomba_data['Distance Left'], roomba_data['Direction']

        #define weights
        #resets every loop
        rightWeight = 0
        leftWeight = 0
        distanceAverage = (distanceLeft + distanceRight)/2


        # get lead vehicle angle

        # NON WEIGHTED PRELIMINARY ALGORITHM
        # checks both the average value and the range of the distance sensed

        prev_move = roomba_data['Current Movement']

       # if (plateLocationX >= pixelError) or ((angle >= 10 and direction == 0) and 0):
       #  roomba_data['Current Movement'] = ord('l')
       #      if prev_move is not roomba_data['Current Movement']:
       #          client.send("d")  # turn right
       #          print("right")
       #      pass
       #  elif (plateLocationX <= -pixelError) or ((angle >= 10 and direction == 1) and 0):
       #      roomba_data['Current Movement'] = ord('j')
       #      if prev_move is not roomba_data['Current Movement']:
       #          client.send("a")  # turn left
       #          print("left")
       #      pass
       #
       #  elif distanceAverage > 35 and abs(distanceRight - distanceLeft) <= distanceError:
       #      roomba_data['Current Movement'] = ord('i')
       #      if prev_move is not roomba_data['Current Movement']:
       #          client.send("i")  # drive forward
       #          print("forward")
       #      pass
       #  elif (distanceAverage <= 35 or distanceAverage >= 60) and abs(distanceRight - distanceLeft) <= distanceError:
       #      roomba_data['Current Movement'] = ord('k')
       #      if prev_move is not roomba_data['Current Movement']:
       #          client.send("k")  # stop
       #          print("stop")
       #      pass
       #
       #  # else if a license plate is not detected
       #  else:
       #      roomba_data['Current Movement'] = ord('k')
       #      if prev_move is not roomba_data['Current Movement']:
       #          client.send("k")  # stop
       #          print("stop")
       #      pass

        ###########################################################
         # WEIGHTED ALGORITHM


         # weights

        # if plate if detected
         if plateLocationX != 0:
             rightWeight = rightWeight + plateWeight
             leftWeight = leftWeight + plateWeight

        # plate location to determine direction
         if plateLocationX >= pixelError:
             rightWeight = rightWeight + platePositionWeight
         elif plateLocationX <= pixelError:
             leftWeight = leftWeight + platePositionWeight

        # sensors to determine direction
         if distanceRight < distanceLeft and abs(distanceRight - distanceLeft) >= distanceError:
             rightWeight = rightWeight + sensorWeight
         elif distanceRight > distanceLeft and abs(distanceRight - distanceLeft) >= distanceError:
             leftWeight = leftWeight + sensorWeight

        # # weight of angle from machine learning
        #  if angle > angleError and angle < 90:  # 90 is upper limit for turning right
        #      rightWeight = rightWeight + angleWeight
        #  elif angle < (360 - angleError) and angle > 270: # 270 is upper limit for turning left
        #      leftWeight = leftWeight + angleWeight


         if distanceAverage >= 20 and abs(distanceRight - distanceLeft) <= distanceError:
             if prev_move is not roomba_data['Current Movement']:
                 client.send("i")  # drive forward
                 print("forward")
             pass
         elif distanceAverage <= 15 and abs(distanceRight - distanceLeft) <= distanceError:
            if prev_move is not roomba_data['Current Movement']:
                client.send("k")  # stop
                print("stop")
            pass
         #if rightWeight > leftWeight:
             #turn right
         #elif leftWeight > rightWeight:
             #turn left
        print("rightWeight")
        print("leftWeight")


################################################################################################
        key = chr(cv2.waitKey(1) & 0xFF)
        if ord(key) is not 255:
            print(key)
            client.send(key.encode())
        elif (key == 'q') or EXIT_FLAG == 1:
            print("quit")
            client.send(key.encode())
            EXIT_FLAG = 1
            cv2.destroyAllWindows()
            client.close()

        if EXIT_FLAG == 1:
            raise SystemExit()
        else:
            pass
    return

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
    imgReduceSearchArea = imgOriginalScene
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
    if (len(listOfPossiblePlates) != 0):                          # if no plates were found
                                                       # else
                # if we get in here list of possible plates has at least one plate

                # sort the list of possible plates in DESCENDING order (most number of chars to least number of chars)

        listOfPossiblePlates.sort(key = lambda possiblePlate: len(possiblePlate.strChars), reverse = True)


                # suppose the plate with the most recognized chars (the first plate in sorted by string length descending order) is the actual plate
        licPlate = listOfPossiblePlates[0]
        ((intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight),fltCorrectionAngleInDeg) = licPlate.rrLocationOfPlateInScene
        listChar = licPlate.listChar
        num_chars = len(licPlate.strChars)
        if num_chars is not 0:
            char_width = intPlateWidth/num_chars
            index = licPlate.strChars.find(LICENSE_PLATE)
            if index is not -1:
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
                drawRedRectangleAroundPlate(imgOriginalScene, licPlate, SCALAR_RED)             # draw red rectangle around plate
            #    print("\nlicense plate read from image = " + licPlate.strChars + "\n")  # write license plate text to std out
            #    print("----------------------------------------")
                writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)           # write license plate text on the image
                #cv2.imshow("imgOriginalScene", imgOriginalScene)                # re-show scene image
            #    cv2.imwrite("imgOriginalScene.png", imgOriginalScene)           # write image out to file
                cv2.circle(imgOriginalScene, (int(intPlateCenterX), int(intPlateCenterY)), 10, (0, 255, 0), 2)
            else:
                intPlateCenterX = 0
    # end if else

    #print('finish the program')
    endtime=cv2.getTickCount()
    time = (endtime - starttime) / cv2.getTickFrequency()
    if time > 0.010:
        #print("Read Plate Time:" + str(time))
        pass
    #cv2.waitKey(0)					# hold windows open until user presses a key


    return intPlateCenterX,listChar
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

















