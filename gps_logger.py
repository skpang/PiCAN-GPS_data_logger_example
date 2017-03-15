#!/usr/bin/python3
# GPS logger example
# For use with PiCAN-GPS board
# http://skpang.co.uk/catalog/pican-with-gps-canbus-board-for-raspberry-pi-23-p-1520.html
# 
# Serial and GPS routine writern by David Whale
#
# SK Pang 15th March 2017
#
#

import math
import time
import serial

PORT = "/dev/ttyS0"
BAUD = 9600

s = serial.Serial(PORT)
s.baudrate = BAUD
s.parity   = serial.PARITY_NONE
s.databits = serial.EIGHTBITS
s.stopbits = serial.STOPBITS_ONE
s.timeout = 0 # non blocking mode

s.close()
s.port = PORT
s.open()
outfile = open('log.txt','w')

#----- SERIAL PORT READ AND WRITE ENGINE --------------------------------------
line_buffer = ""
rec_buffer = None

def read_waiting():
    """Poll the serial and fill up rec_buffer if something comes in"""
    global rec_buffer
    if rec_buffer != None:
        return True

    line = process_serial()
    if line != None:
        rec_buffer = line
        return True

    return False

def read():
    """Poll the rec_buffer and remove next line from it if there is a line in it"""
    global rec_buffer

    if not read_waiting():
        return None

    rec = rec_buffer
    rec_buffer = None
    ##print("read:" + rec)
    return rec

def process_serial():
    """Low level serial poll function"""
    global line_buffer

    while True:
        data = s.read(1)
        data = data.decode('utf-8')
        #print(data, type(data), len(data))
 
        if len(data) == 0:
            #print("RETURN NONE")
            return None # no new data has been received
        data = data[0]

        if data == '\r':
            #print("RETURN ")
            pass # strip newline

        elif data == '\n':
            #print("NEWLINE ")
            line = line_buffer
            line_buffer = ""
            #print(line)
            return line

        else:
            #print("ADD %s" % data)
            line_buffer += data

#----- ADAPTOR ----------------------------------------------------------------

# This is here, so you can change the concurrency and blocking model,
# independently of the underlying code, to adapt to how your app wants
# to interact with the serial port.

# NOTE: This is configured for non blocking send and receive, but no threading
# and no callback handling.

def send_message(msg):
    """Send a message to the micro:bit.
        It is the callers responsibility to add newlines if you want them.
    """
    ##print("Sending:%s" % msg)

    s.write(msg)

def get_next_message():
    """Receive a single line of text from the micro:bit.
        Newline characters are pre-stripped from the end.
        If there is not a complete line waiting, returns None.
        Call this regularly to 'pump' the receive engine.
    """
    result = read()
    ##if result != None:
    ##    print("get_next_message:%s" % str(result))
    return result

def print_csv(values):
  line = ""
  for v in values:
    if line != "":
      line += ','
    line += str(v)
  print(line,file = outfile) # Save data to file
  #log_file.write(line + '\n')
  #log_file.flush()
  print(line)

REPORT_RATE = 1.0
date = ""

next_report = time.time() + REPORT_RATE

locked = False
date,timestamp, northing, northing_flag, easting, easting_flag = "","","","","",""

try:
  while True:
    now = time.time()

    if now > next_report:
      next_report = now + REPORT_RATE
      values =  date,timestamp,locked,northing, northing_flag, easting, easting_flag
      print_csv(values)

    gps_data = get_next_message()
    if gps_data is not None:
      parts = gps_data.split(',')
      rec_type = parts[0]
      if rec_type == "$GPRMC":
        date = parts[9]
        #print(date)
      if rec_type == "$GPGSA":
        lock_flag = parts[1]
        if lock_flag == 'A':
          #print("GPS LOCKED")
          locked = True
        else:
          #print("NO GPS LOCK:%s" % lock_flag)
          locked = False

      elif rec_type == "$GPGGA":
        if locked:
          timestamp, northing, northing_flag, easting, easting_flag = parts[1:6]
        else:
          timestamp, northing, northing_flag, easting, easting_flag = "","","","",""

except KeyboardInterrupt:
  #Catch keyboard interrupt
  outfile.close()
  #os.system("sudo /sbin/ip link set can0 down")
  print('\n\rKeyboard interrtupt')
      


