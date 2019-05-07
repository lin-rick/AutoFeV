import serial
import lib.roomba.Bytes as b
import lib.roomba.Roomba as Roomba
import time


# Open a serial connection to Roomba
ser = serial.Serial(port='/dev/serial0', baudrate=115200)

# Assuming the robot is awake, start safe mode so we can hack.
ser.write(b'\x83')
time.sleep(.1)

# Program a five-note start song into Roomba.
ser.write(b'\x8c\x00\x05C\x10H\x18J\x08L\x10O\x20')

# Play the song we just programmed.
ser.write(b'\x8d\x00')
time.sleep(1.6)  # wait for the song to complete

ser.write(b.Commands.read + b.Sensors.LB_ARRAY[0])
read = ser.read(2)
print(read)

# Leave the Roomba in passive mode; this allows it to keep
#  running Roomba behaviors while we wait for more commands.
time.sleep(10)
ser.write(b'\x80')

# Close the serial port; we're done for now.
ser.close()

