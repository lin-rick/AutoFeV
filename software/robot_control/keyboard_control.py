import socket
import time
import msvcrt
import json
import threading
import cv2
import queue


EXIT_FLAG = 0
frames = queue.Queue(10)
roomba_data = {
    'Battery State': 0,
    'Battery Temperature': 0,
    'Battery Capacity': 0,
    'Battery Level': 0
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


def recieve_loop():
    # Receive data dict
    try: recv = client.recv(1).decode()
    except:
        return 0
    if recv == '<':
        client.setblocking(True)
        num_bytes = int.from_bytes(client.recv(1), byteorder='big', signed=False)
        recv = client.recv(1).decode()
        if recv == '>':
            packet = client.recv(num_bytes)
            roomba_data['Battery State'] = packet[1]
            roomba_data['Battery Temperature'] = packet[3]
            roomba_data['Battery Capacity'] = int.from_bytes(packet[5:7], byteorder='big', signed=False)
            roomba_data['Battery Level'] = int.from_bytes(packet[8:10], byteorder='big', signed=False)
            print(roomba_data)
            client.setblocking(False)


if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('192.168.4.1', 1024))
    client.setblocking(False)
    #cmd_thread = threading.Thread(target=command_loop)
    #rcv_thread = threading.Thread(target=recieve_loop)
    #vid_thread = threading.Thread(target=video_loop)
    #grab_thread = threading.Thread(target=video_grabber)
    #cmd_thread.setDaemon(True)
    #rcv_thread.setDaemon(True)
    #vid_thread.setDaemon(True)
    #grab_thread.setDaemon(True)
    #rcv_thread.start()
    #cmd_thread.start()
    #vid_thread.start()
    #grab_thread.start()
    cap = cv2.VideoCapture('http://192.168.4.1/html/cam_pic_new.php?')
    count = 0
    while True:
        #command_loop()
        #if count == 20:
        recieve_loop()
        #    count = 0
        ret, frame = cap.read()
        cv2.imshow('frame', frame)
        #count = count + 1

        key = chr(cv2.waitKey(1) & 0xFF)
        if (key == 'q') or EXIT_FLAG == 1:
            print("quit")
            client.send(key.encode())
            EXIT_FLAG = 1
            cv2.destroyAllWindows()
            client.close()
        elif ord(key) is not 255:
            print(key)
            client.send(key.encode())

        if EXIT_FLAG == 1:
            raise SystemExit()
        else:
            pass
