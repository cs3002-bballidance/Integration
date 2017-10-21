import multiprocessing as mp
import logging
import os
import sys
import time
import mega_pi_integrated
import prediction
import client

FILENAME = 'log/bballi.log'
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
logger = logging.getLogger(__name__)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 	#supress debugging output

SERVER_IP = '172.17.18.8'
SERVER_PORT = 8888

def serialPiProcess(l, q):
	l.acquire()
	try:
		logger.debug('serialPiProcess')
		serialPiHandler = mega_pi_integrated.serialPiMgr()
		init_result = serialPiHandler.run()
	except Exception as e:
		logger.critical('Exception occured at serialPiProc: {}'.format(e))
		init_result = False
	finally:
		q.put(init_result) # this statement should return status of serialPiHandler true / false
		l.release()

	if init_result:
		logger.info('Collecting sensor data')
		# runs collection of sensor data
		serialPiHandler.sensorCollection()
	else:
		sys.exit(1)


def piPredictionProcess(l, q):
	l.acquire()
	try:
		cont = q.get()
		if cont:
			logger.debug('piPredictionProcess can continue.')
			# Figure out how to get result before running the whole process
			piPredictionHandler = prediction.predictionMgr()
			init_result = piPredictionHandler.status();
		else:
			logger.critical('piPredictionProcess - Error in serialPiProcess. Unable to continue.')
			init_result = cont
	finally:
		logger.debug('prediction: {}'.format(init_result))
		q.put(init_result)
		l.release()

	if init_result:
		logger.info('Continuing with prediction')
		time.sleep(1)
		# runs prediction
		piPredictionHandler.run()
		# figure out how to loop forever while returning value to pass to client through queue
	else:
		sys.exit(1)


def piClientProcess(l,q):
	l.acquire()
	try:
		cont = q.get()
		logger.debug('piClientProcess: {}'.format(cont))
		if not cont:
			logger.critical('piClientProcess - Error in serialPiProcess. Unable to continue.')
	finally:
		l.release()

		if cont:
			logger.info('Continuing with client')
			# run main client process
			myclient = client.client(SERVER_IP,SERVER_PORT)
		else:
			sys.exit(1)


def main():
	logger.info('Starting {}'.format(__file__))

	jobs = []
	q = mp.Queue()
	lock = mp.Lock()

	p = mp.Process(target=serialPiProcess, args=(lock, q,))
	jobs.append(p)
	p.start()

	p = mp.Process(target=piPredictionProcess, args=(lock, q,))
	jobs.append(p)
	p.start()

	p = mp.Process(target=piClientProcess, args=(lock, q,))
	jobs.append(p)
	p.start()

	for proc in jobs:
		proc.join()


if __name__ == '__main__':
	main()
