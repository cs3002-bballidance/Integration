import RPi.GPIO as GPIO
import serial
import time
import numpy
import csv
import sys
import struct
import logging
import pandas as pd

class serialPiMgr ():
	def __init__(self):

		self.name = "serialPi"
		self.logger = logging.getLogger(self.name)
		self.logger.info('Initializing {} ({})'.format(self.name,__file__))
		self.columns = ['acc1x', 'acc1y', 'acc1z',
			'acc2x', 'acc2y', 'acc2z',
			'acc3x', 'acc3y', 'acc3z',
			'curr', 'volt']
		self.df = pd.DataFrame(columns=self.columns)
		self.df = self.df.set_index('acc1x')
		self.SERIAL_PORT = '/dev/ttyAMA0'
		self.CSV_DIR = 'data/mega_data.csv'


	def run(self):
		#constants
		self.HANDSHAKE_PKT = bytes.fromhex("DD1C")
		self.ACK_PKT = bytes.fromhex("DDCC")
		self.ERR_PKT = bytes.fromhex("DDFD")
		self.RESET_PIN = 17
		self.DURATION = 120
		self.BAUDRATE = 57600

		#instantiate GPIO
		self.logger.info('Initializing GPIO')
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		GPIO.setup(self.RESET_PIN,GPIO.OUT)
		GPIO.output(self.RESET_PIN,GPIO.HIGH) # pull low then back to high to reset arduino

		#instantiate serial
		try:
			self.logger.info('Initializing serial interface')
			self.ser = serial.Serial(self.SERIAL_PORT,self.BAUDRATE)
		except serial.serialutil.SerialException:
			self.logger.critical('Unable to open serial port: {}'.format(self.SERIAL_PORT))
			return False
		except Exception as e:
			self.logger.critical('Exception occured: {}'.format(e))
			return False
		finally:
			return True


	def sensorCollection(self):
		GPIO.output(self.RESET_PIN,GPIO.LOW)
		self.ser.flushInput() # flush any existing serial buffer
		self.logger.info('Resetting arduino before resuming')
		time.sleep(1) # sleep for 1 second before pulling the pin back to high
		GPIO.output(self.RESET_PIN,GPIO.HIGH)

		# pandas dataframe might be faster. look at how it is implemented in sample_eval_server.py
		with open(self.CSV_DIR, 'w') as csvfile:
		    self.fieldnames = ['acc1x', 'acc1y', 'acc1z', 'acc2x', 'acc2y', 'acc2z', 'acc3x', 'acc3y', 'acc3z', 'curr', 'volt']
		    writer = csv.DictWriter(csvfile, extrasaction='ignore', fieldnames=self.fieldnames)
		    writer.writeheader()
		    csvfile.close()

		    #initialize communications
		    self.hasReplied = False
		    while(not self.hasReplied):
		        #1. send a handshake
		        self.logger.info('Sending handshake to arduino')
		        self.ser.write(self.HANDSHAKE_PKT)
		        #2. wait for input then check
		        time.sleep(1)
		        self.logger.info('Waiting for acknowledgement from arduino')
		        bytesToRead = self.ser.inWaiting()
		        response = self.ser.read(bytesToRead)
		        #3. send an ACK if right
		        if response == self.ACK_PKT:
		            self.logger.info('Acknowledgement received')
		            self.hasReplied = True
		            self.ser.write(self.ACK_PKT)
		        else:
		            time.sleep(1)

		    #start timer
		    #startTime = time.time()
		    #endTime = time.time()

		    #self.count = 0
		    #wait for data
		    while True: #(endTime - startTime) < DURATION: #True :
		        #1. wait until the entire packet arrives
		        if (self.ser.inWaiting() >= 26) :
		            packet_type = bytearray(self.ser.read(2))
		            (checksum,) = struct.unpack(">h", bytearray(self.ser.read(2)))

		            #2. read data and convert to appropriate values
		            #>h big endian, signed int (2 bytes)
		            (acc1x,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc1y,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc1z,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc2x,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc2y,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc2z,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc3x,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc3y,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (acc3z,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (curr,) = struct.unpack(">h", bytearray((self.ser.read(2))))
		            (volt,) = struct.unpack(">h", bytearray((self.ser.read(2))))

		            self.calcChecksum = acc1x ^ acc1y ^ acc1z ^ acc2x ^ acc2y ^ acc2z ^ acc3x ^ acc3y ^ acc3z ^ curr ^ volt

		            if (checksum == self.calcChecksum) :
		                self.ser.write(self.ACK_PKT)
		                with open(self.CSV_DIR, 'a') as csvfile:
		                    writer = csv.DictWriter(csvfile, extrasaction='ignore', fieldnames=self.fieldnames)
		                    writer.writerow({'acc1x': acc1x,
		                                     'acc1y': acc1y,
		                                     'acc1z': acc1z,
		                                     'acc2x': acc2x,
		                                     'acc2y': acc2y,
		                                     'acc2z': acc2z,
		                                     'acc3x': acc3x,
		                                     'acc3y': acc3y,
		                                     'acc3z': acc3z,
		                                     'curr':  curr,
		                                     'volt':  volt
		                                     })
		                    csvfile.close()
		            else:
		                self.logger.warn('Packet error')
		                self.ser.write(self.ERR_PKT)
		            #self.count = self.count + 1
		            #3. update timer
		            #endTime = time.time()
		            #self.logger.debug('1 data per: {} '.format(endTime - startTime))
		            #startTime = endTime
		    # logger.debug('startTime: {}'.format(startTime))
		    # logger.debug('endTime: {}'.format(endTime))
		    # logger.debug('duration: {} secs'.format(int(endTime - startTime)))
		    #self.logger.debug('data collected: {}'.format(count))

		#All done
		self.ser.close()
		self.logger.info('Exiting {}'.format(__file__))
		sys.exit()


def main():
	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
	logger = logging.getLogger("serialPi")
	logger.warn('You should initiate this script as a module')
	sys.exit(1)

if __name__ == '__main__':
	main()
