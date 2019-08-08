class Commands:
    # Start and stop commands
    oi_start = bytes([128])  # Start Open Interface
    reset = bytes([7])  # Full reset. Must send oi_start to start again
    stop = bytes([173])  # Stop OI. Use this when finished

    # Mode commands
    safe_mode = bytes([131])  # Enter safe mode to enable actuator control
    full_mode = bytes([132])
    power_down = bytes([133])  # Enter passive mode. Disables manual actuator control. Enables low-power after 5min

    # Cleaning commands
    clean = bytes([135])
    spot = bytes([134])
    seek_dock = bytes([143])

    # Actuators
    drive_pwm = bytes([146])  # Follow with [RightPWMhighbyte][RightPWMlowbyte][LeftPWMhighbyte][LeftPWMlowbyte]
    drive_radius = bytes([137])  # Follow with [VelocityHighByte][VelocityLowByte][RadiusHighByte][RadiusLowByte]

    # Sensors
    read = bytes([142])  # Follow with [PacketID]
    read_list = bytes([149])  # Follow with [# of Packets][PacketID1][PacketID2]...
    open_stream = bytes([148])  # Follow with [# of Packets][PacketID1][PacketID2]...
    pause_stream = bytes([150, 0])
    resume_stream = bytes([150, 1])

    # LEDs
    led_toggle = bytes([139])  # Follow with [LEDBits][PowerColor][PowerIntensity]
    seg_ascii_toggle = bytes([164])  # [Digit3ASCII][Digit2ASCII][Digit1ASCII][Digit0ASCII]

    # Sound
    add_song = b'\x8c\x00\x05C\x10H\x18J\x08L\x10O\x20'  # [140][SongNumber][SongLength][NoteNumber1][NoteDuration1]...
    play_song = b'\x8d\x00'  # [141][SongNumber]


class Led:
    # LED bits
    CHECK_ROBOT = bytes([8])
    HOME = bytes([4])
    SPOT = bytes([2])
    DEBRIS = bytes([1])
    # Syntax for bitwise manipulation ie. bytes([x[0] | y[0]]) = 6, where x = home, y = spot.


class Sensors:
    # Packet IDs for sensor packet requests
    BUMP_WHEEL = bytes([7])  # Returns 1 byte with bits regarding each sensor
    DISTANCE = bytes([19])  # Returns 2 byte signed distance travelled since last requested in millimeters
    ANGLE = bytes([20])  # Returns 2 byte signed angles rotated since last requested in degrees
    ENC_L = bytes([43])
    ENC_R = bytes([44])

    CHG_STATE = bytes([21])  # Returns 1 byte number range 0-5 for charge state
    VOLT_LEVEL = bytes([22])  # Returns 2 bytes, voltage level mV
    CURRENT = bytes([23])  # Returns 2 bytes signed, current mA
    BAT_TEMP = bytes([24])  # Returns 1 byte signed, temp in C
    CHG_LEVEL = bytes([25])  # Returns 2 bytes, mA remaining
    BAT_CAP = bytes([26])  # Returns 2 bytes unsigned, mAh
    BAT_LIST = CHG_STATE + BAT_TEMP + BAT_CAP + CHG_LEVEL

    CLIF_L = bytes([28])
    CLIF_FL = bytes([29])
    CLIF_FR = bytes([30])
    CLIF_R = bytes([31])

    OI_MODE = bytes([35])
    SONG_PLAYING = bytes([37])
    STRM_NUMPACKETS = bytes([38])
    STRM_PACKET_HEADER = bytes([19])

    LB_BINARY = bytes([45])  # Returns 1 byte unsigned, each bit for a sensor 1 or 0 for detections
    LB_L = bytes([46])  # Distance detected of each light bumper
    LB_FL = bytes([47])
    LB_CL = bytes([48])
    LB_CR = bytes([49])
    LB_FR = bytes([50])
    LB_R = bytes([51])
    LB_ARRAY = LB_L + LB_FL + LB_CL + LB_CR + LB_FR + LB_R


def motor_bytes(number):
    bits = 16
    # Return the 2'complement hexadecimal representation of a number
    if number < 0:
        x = hex((1 << bits) + number)
    elif number == 0:
        x = '0x0000'
    else:
        x = hex(number)[:2] + '00' + hex(number)[2:]
    return bytes.fromhex(x[2:])






