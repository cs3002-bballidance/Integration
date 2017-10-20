from multiprocessing import Process
import logging
import os

FILENAME = 'log/bballi.log'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename=FILENAME,level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info('Starting {}'.format(__file__))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 	#supress debugging output

import prediction
import mega_pi_integrated
import client

SERVER_IP = '172.17.18.8'
SERVER_PORT = 8888

def mega_process():
	mega_pi_integrated.start_running()


def prediction_process():
	prediction.main_loop()


def client_process():
	client.createClient(SERVER_IP,SERVER_PORT)


if __name__ == '__main__':
	jobs = []

	try:
		p = Process(target=client_process)
		p.daemon = True
		jobs.append(p)
		p.start()

		p = Process(target=mega_process)
		p.daemon = True
		jobs.append(p)
		p.start()

		p = Process(target=prediction_process)
		p.daemon = True
		jobs.append(p)
		p.start()

		for proc in jobs:
			proc.join()
	except Exception as e:
		logger.critical('Exception occur: {}'.format(e))
	finally:
		logger.info('Exiting process {}'.format(__file__))
