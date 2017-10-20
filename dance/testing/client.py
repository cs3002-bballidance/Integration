from collections import defaultdict
from Crypto import Random
from Crypto.Cipher import AES

import csv
import logging
import base64
import socket
import sys

logger = logging.getLogger(__name__)
KEY_DIR = '/script/Production/dance/testing/'
RESULTS_DIR = 'data/results.csv'


class client:
	def __init__(self, ip_addr, port_num):
		# Create TCP/IP socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Connect to server
		try:
			server_address = (ip_addr, port_num)
			logger.info('Initiating connection to {} port {}'.format(ip_addr, port_num))
			self.sock.connect(server_address)
		except Exception as e:
			logger.critical('Exception occured: {}'.format(e))
			exit(1)
		logger.info('Connected to {} port {}'.format(ip_addr, port_num))

		# Obtain secret key from local key file
		# TODO: Encode secret_key in key file then perform decode operations
		try:
			with open(KEY_DIR) as key:
				secret_key = key.read()
				key.closed
		except exception as e:
			logger.critical('Exception on reading key: {}'.format(e))
		# ===================================================
		# Uncomment this section for Raspberry Pi integration
		# Obtain secret key from thumbdrive in Raspberry Pi
		'''
		secret_key = ' '
		for root, dirs, files in os.walk(KEY_DIR):
			if 'key' in files:
				if os.access(join(root, 'key'), os.R_OK):
					with open(join(root, 'key')) as key:
						secret_key = key.read()
						key.closed
						break
		'''
		# ===================================================

		# List of actions available
		self.actions = ['logout  ', 'wavehands', 'busdriver', 'frontback', 'sidestep', 'jumping',
						'jumpingjack', 'turnclap', 'squatturnclap', 'windowcleaning', 'windowcleaner360']
		action = ''
		cumulativepower_list = []
		cumulativepower_list_avg = 0

		# Send data until logout action is recieved
		while action != 0:
			#1. Get action, current and voltage from prediction.py
			# TODO: Check if file has changed since previous results if not wait until new file exists
			columns = defaultdict(list)

			try:
				with open(RESULTS_DIR, newline='') as csvfile:
					predicted_results = csv.reader(csvfile, delimiter=',', quotechar='|')
					for row in predicted_results:
						for(col,val) in enumerate(row):
							columns[col].append(val)
			except Exception as e:
				logger.critical('Exception occured on reading results.csv: {}'.format(e))

			action = int(columns[0][len(columns[0])-1])
			current = float(columns[1][len(columns[1])-1])
			voltage = float(columns[2][len(columns[2])-1])
			# Necessary to prevent overflow of msg from being flooded to encrypt
			time.sleep(1)

			#1a. Calculates average power since first reading
			power = voltage * current
			voltage_str = str(voltage)
			current_str = str(current)
			power_str = str(power)
			cumulativepower_list.append(power)
			#logger.debug("cumulativepower List : {}".format(cumulativepower_list))
			cumulativepower_list_avg = float(sum(cumulativepower_list) / len(cumulativepower_list))

			#1b. Assemble message
			msg = b'#' + b'|'.join([self.actions[action].encode(), voltage_str.encode(), current_str.encode(), power_str.encode(), str(cumulativepower_list_avg).encode()]) + b'|'
			logger.debug('unencrypted msg: {}'.format(msg))

			#2. Encrypt readings
			#2a. Apply padding
			length = 16 - (len(msg) % 16)
			msg += bytes([length])*length

			#2b. Apply AES-CBC encryption
			iv = Random.new().read(AES.block_size)
			cipher = AES.new(secret_key.encode(), AES.MODE_CBC, iv)
			encodedMsg = base64.b64encode(iv + cipher.encrypt(msg))
			#logger.debug('encrypted msg: {}'.format(encodedMsg))

			#3. Send data packet over
			logger.info('Sending data to server')
			self.sock.sendall(encodedMsg)

		#4. All done, logout.
		self.sock.close()
		sys.exit()


def createClient(ip_addr, port_num):
	myclient = client(ip_addr, port_num)


def main():
	logger.info('Starting {}'.format(__file__))

	if len(sys.argv) != 3:
	        logger.critical('Invalid number of arguments')
	        #print('python client.py [IP address] [Port]')
	        sys.exit()

	ip_addr = sys.argv[1]
	port_num = int(sys.argv[2])

	try:
		my_client = client(ip_addr, port_num)
	#except TimeoutError:
	#	logger.critical('Timeout error on connection to server')
	except Exception as e:
		logger.critical('Exception occured on connection to server: {}'.format(e))


if __name__ == '__main__':
	main()