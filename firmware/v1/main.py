#!/usr/bin/sudo python

import lib.roomba.Roomba as Roomba
import lib.roomba.Bytes as Bytes
import time
import socket
import threading
import RPi.GPIO as GPIO
import json


EXIT_FLAG = 0

def process_cmd():
    global EXIT_FLAG
    while True:
        time.sleep(0.2)
        try: command = conn.recv(1).decode()
        except: command = None
        if command == 'r':
            LB = roomba.read_LB()
            print(LB)

        # Loopback test for testing socket connection
        elif command == 't':
            conn.send('t'.encode())

        elif command == 'q':
            print('quit')
            roomba.send_command(Bytes.Commands.power_down)
            time.sleep(0.2)
            roomba.send_command(Bytes.Commands.stop)
            conn.close()
            EXIT_FLAG = 1  # Exit program
            break

        elif command == 'x':
            roomba.play_song()
            conn.send('x'.encode())

        elif command is not None:
            print(command)
            roomba.process_move_cmd(command)
            roomba.process_radius_cmd(command)


def periodic_events():
    global EXIT_FLAG
    while True:
        if EXIT_FLAG:
            break
        GPIO.output(17, False)
        time.sleep(1)
        GPIO.output(17, True)

        time.sleep(10)


def read_stream():
    global EXIT_FLAG
    # pin settings for ultrasonic sensors
    TRIG, ECHO = Roomba.Roomba.ultraSetup(roomba)
    while True:
        time.sleep(0.1)
        if EXIT_FLAG:
            break
        packet = roomba.read_stream_packet()
        # getting distance from ultrasonics sensors
        distance = Roomba.Roomba.ultraDistance(roomba, TRIG, ECHO)
        # print(angle, distanceLeft, distanceRight, direction)
        if distance > 255:
            distance = 255
        direction = roomba.CURRENT_DIRECTION
        packet += bytes([distance, ord(direction)])
        # conn.send('<'.encode())
        # conn.send(bytes([len(packet)]))
        # conn.send('>'.encode())
        conn.sendall(packet)


def send_dict(data_dict):
    serialized = json.dumps(data_dict)
    num_bytes = len(serialized)
    conn.send('<'.encode())
    conn.send(bytes([num_bytes]))
    conn.send('>'.encode())
    conn.sendall(serialized.encode())


if __name__ == "__main__":
    time.sleep(5)
    global EXIT_FLAG
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('192.168.4.1', 1024))
    server.listen(5)
    conn, addr = server.accept()
    conn.setblocking(False)

    roomba = Roomba.Roomba('/dev/serial0', 115200)

    GPIO.setmode(GPIO.BCM)  # BCM for GPIO numbering
    GPIO.setup(17, GPIO.OUT)  # Make pin 17 (which is hooked up to the BRC pin) an output
    GPIO.output(17, False)
    time.sleep(1)
    GPIO.output(17, True)

    roomba.send_command(Bytes.Commands.oi_start)
    roomba.send_command(Bytes.Commands.safe_mode)
    time.sleep(0.2)
    roomba.ser.write(b'\x8c\x00\x05C\x10H\x18J\x08L\x10O\x20')
    time.sleep(0.2)
    roomba.ser.write(b'\x8d\x00')
    time.sleep(2)
    packet_ids = Bytes.Sensors.BAT_LIST
    roomba.req_open_stream(packet_ids)

    cmd_thread = threading.Thread(target=process_cmd)
    periodic_thread = threading.Thread(target=periodic_events)
    stream_thread = threading.Thread(target=read_stream)
    cmd_thread.setDaemon(True)
    periodic_thread.setDaemon(True)
    stream_thread.setDaemon(True)

    cmd_thread.start()
    periodic_thread.start()
    stream_thread.start()

    while True:
        if EXIT_FLAG:
            raise SystemExit()


