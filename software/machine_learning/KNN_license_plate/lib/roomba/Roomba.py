import serial
import Jetson.GPIO as GPIO
import time
import math
import lib.roomba.Bytes as b



class Roomba:
    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=0.5, inter_byte_timeout=0.1,
                                 bytesize=serial.EIGHTBITS)
        self.pwmL = 0  # PWM value -255 to 255 for forward and reverse
        self.pwmR = 0
        self.PWM_LIMIT = 230
        self.PWM_INCR = 25
        self.velocity = 0
        self.radius = 0
        self.DEFAULT_RADIUS = 100  # 10 cm turn radius
        self.DEFAULT_VELOCITY = 150  # moving at speed of 15cm/s
        self.battery = {'Battery State': 0, 'Battery Temperature': 0, 'Battery Level': 0, 'Battery Capacity': 1}

    def send_command(self, command):
        if self.ser.isOpen() is True:
            self.ser.write(command)
        else:
            print('Error: Serial not Open')

    def drive_pwm(self):
        if self.ser.isOpen() is True:
            self.ser.write(b.Commands.drive_pwm + b.motor_bytes(self.pwmR) + b.motor_bytes(self.pwmL))
        else:
            print('Error: Serial not Open')

    def drive_radius(self):
        if self.ser.isOpen() is True:
            self.ser.write(b.Commands.drive_radius + b.motor_bytes(self.velocity) + b.motor_bytes(self.radius))
        else:
            print('Error: Serial not Open')

    def req_packet(self, packetID, numBytes):
        if self.ser.isOpen() is True:
            self.ser.write(b.Commands.read + packetID)

            while self.ser.inWaiting() == 0:
                pass

            return self.ser.read(numBytes)
        else:
            print('Error: Serial not Open')
            return -1


    def req_open_stream(self, packetIDList):
        if self.ser.isOpen() is True:
            self.ser.write(b.Commands.open_stream + bytes([len(packetIDList)]) + packetIDList)
            return 0
        else:
            print('Error: Serial not Open')
            return -1

    def read_stream_packet(self):
        while self.ser.read(1) != b.Sensors.STRM_PACKET_HEADER:
            pass
        num_bytes = int.from_bytes(self.ser.read(1), byteorder='big', signed=False)
        packet = self.ser.read(num_bytes)
        return packet

# controlling with radius
    def process_radius_cmd(self, command):
        if command == 'j':
            self.radius = -self.DEFAULT_RADIUS
            self.velocity = self.DEFAULT_VELOCITY
            self.drive_radius()
            print('Left')
        elif command == 'l':
            self.radius = self.DEFAULT_RADIUS
            self.velocity = self.DEFAULT_VELOCITY
            self.drive_radius()
            print('Right')
        elif command == 'k':
            self.radius = 0
            self.velocity = 0
            self.drive_radius()
            print('Stop')
        elif command == 'i':
            self.radius = 0
            self.velocity = self.DEFAULT_VELOCITY
            self.drive_radius()
            print('Forward')
        else:
            pass


# controlling with PWM
    def process_move_cmd(self, command):
        if command == 'w':
            if self.pwmL == self.pwmR and self.pwmL < self.PWM_LIMIT and self.pwmR < self.PWM_LIMIT:
                self.pwmL += self.PWM_INCR
                self.pwmR += self.PWM_INCR
            else:
                if self.pwmR < self.pwmL < self.PWM_LIMIT:
                    self.pwmL = self.pwmR
                elif self.pwmR < self.PWM_LIMIT:
                    self.pwmR = self.pwmL
            print('Left Motor: ', self.pwmL, 'Right Motor: ', self.pwmR)
            self.drive_pwm()

        elif command == 'a':
            '''
            if self.pwmR < self.PWM_LIMIT:
                self.pwmR += self.PWM_INCR
            if self.pwmR > self.PWM_LIMIT:
                self.pwmL -= self.PWM_INCR
            '''
            self.pwmL = -35
            self.pwmR = 35
            print('Left Motor: ', self.pwmL, 'Right Motor: ', self.pwmR)
            self.drive_pwm()

        elif command == 'd':
            '''
            if self.pwmL < self.PWM_LIMIT:
                self.pwmL += self.PWM_INCR
            if self.pwmL > self.PWM_LIMIT:
                self.pwmR -= self.PWM_INCR
            '''
            self.pwmR = -35
            self.pwmL = 35
            print('Left Motor: ', self.pwmL, 'Right Motor: ', self.pwmR)
            self.drive_pwm()

        elif command == 's':
            if self.pwmL == self.pwmR and -self.PWM_LIMIT < self.pwmL <= 0:
                self.pwmL -= self.PWM_INCR
                self.pwmR -= self.PWM_INCR
            else:
                self.pwmL = 0
                self.pwmR = 0
            print('Left Motor: ', self.pwmL, 'Right Motor: ', self.pwmR)
            self.drive_pwm()

        else:
            pass

    def read_LB (self):
        LB = []
        for i in range(0, len(b.Sensors.LB_ARRAY)):
            read = self.req_packet(b.Sensors.LB_ARRAY[i], 2)
            LB.append(int.from_bytes(read, byteorder='big', signed=False))

        return LB

    def monitor_battery(self):
        read = self.req_packet(b.Sensors.CHG_STATE, 1)
        self.battery['Battery State'] = int.from_bytes(read, byteorder='big', signed=False)
        read = self.req_packet(b.Sensors.BAT_TEMP, 1)
        self.battery['Battery Temperature'] = int.from_bytes(read, byteorder='big', signed=True)
        read = self.req_packet(b.Sensors.BAT_CAP, 2)
        self.battery['Battery Capacity'] = int.from_bytes(read, byteorder='big', signed=False)
        read = self.req_packet(b.Sensors.CHG_LEVEL, 2)
        self.battery['Battery Level'] = int.from_bytes(read, byteorder='big', signed=False)*1.0

    def ultraSetup(self):
        # setting up ultrasonic sensors
        # uses board pin numbers
        GPIO.setmode(GPIO.BOARD)

        # defining variables
        distanceRight = 0.0
        distanceLeft = 0.0
        timeRight = 0.0
        timeLeft = 0.0
        angle = 0.0

        # set distance between sensors in cm
        d = 13.5

        # pin setup
        TRIG_R = 11
        ECHO_R = 13

        TRIG_L = 19
        ECHO_L = 21

        GPIO.setup(TRIG_L, GPIO.OUT)
        GPIO.setup(TRIG_R, GPIO.OUT)

        GPIO.setup(ECHO_L, GPIO.IN)
        GPIO.setup(ECHO_R, GPIO.IN)

        # waiting for pins to become low
        GPIO.output(TRIG_R, GPIO.LOW)
        GPIO.output(TRIG_L, GPIO.LOW)
        time.sleep(2)

        return TRIG_L, TRIG_R, ECHO_L, ECHO_R, d

    def ultraDistance(self, TRIG_L, TRIG_R, ECHO_L, ECHO_R, d):
        # right ultrasonic sensor
        GPIO.output(TRIG_R, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(TRIG_R, GPIO.LOW)
        startLeft = 0
        startRight = 0
        endLeft = 0
        endRight = 0

        while GPIO.input(ECHO_R) == False:
            startRight = time.time()
        while GPIO.input(ECHO_R) == True:
            endRight = time.time()

        timeRight = endRight - startRight

        # left ultrasonic sensor
        GPIO.output(TRIG_L, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(TRIG_L, GPIO.LOW)

        while GPIO.input(ECHO_L) == False:
            startLeft = time.time()
        while GPIO.input(ECHO_L) == True:
            endLeft = time.time()

        timeLeft = endLeft - startLeft

        # calculating distance
        distanceLeft = timeLeft*34300/2
        distanceRight = timeRight*34300/2

        if distanceRight > distanceLeft:
            angle = math.degrees(math.atan2((distanceRight-distanceLeft), d))
            direction = 1  # 1 == left
        else:
            angle = math.degrees(math.atan2((distanceLeft - distanceRight), d))
            direction = 0  # 0 == right

        return int(angle), int(distanceRight), int(distanceLeft), int(direction)