from multiprocessing import Process
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename='bballi.log',level=logging.DEBUG)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 	#supress debugging output

import prediction
import mega_pi_integrated
import client

def mega_process():
	mega_pi_integrated.start_running()

def prediction_process():
	prediction.main_loop()

def client_process():
	client.createClient('172.17.18.8',8888)


if __name__ == '__main__':
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	logger.info('Starting {}'.format(__file__))

	jobs = []

	try: 
		p = Process(target=prediction_process)
		jobs.append(p)
		p.start()

		p = Process(target=client_process)
		jobs.append(p)
		p.start()

		p = Process(target=mega_process)
		jobs.append(p)
		p.start()

		for proc in jobs:
			proc.join()
	except Exception as e:
		logger.critical('Exception occur: {}'.format(e))
	finally:
		logger.info('Exiting process {}'.format(__file__))