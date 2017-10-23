import multiprocessing as mp
import logging
import os
import sys
import time
import mega_pi_integrated
import prediction
import client

FILENAME = 'log/bballi.log'
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename=FILENAME,level=logging.DEBUG)
logger = logging.getLogger(__name__)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 	#supress debugging output

SERVER_IP = '192.168.10.97'
SERVER_PORT = 8888


def serialPiProcess(l, genQ):
	l.acquire()
	try:
		logger.debug('serialPiProcess')
		serialPiHandler = mega_pi_integrated.serialPiMgr()
		init_result = serialPiHandler.run()
	except Exception as e:
		logger.critical('serialPiProcess - Exception occured: {}'.format(e))
		init_result = False
	finally:
		genQ.put(init_result) # this statement should return status of serialPiHandler true / false
		l.release()

	if init_result:
		logger.info('serialPiProcess - Collecting sensor data')
		# runs collection of sensor data
		try:
			serialPiHandler.sensorCollection()
		except KeyboardInterrupt:
			sys.exit(0)
	else:
		sys.exit(1)


def piPredictionProcess(l, genQ, out2ServerQ):
	l.acquire()
	try:
		cont = genQ.get()
		if cont:
			logger.debug('piPredictionProcess - Starting')
			# Figure out how to get result before running the whole process
			piPredictionHandler = prediction.predictionMgr()
			init_result = piPredictionHandler.status();
		else:
			logger.critical('piPredictionProcess - Error in serialPiProcess. Unable to start.')
			init_result = cont
	finally:
		logger.debug('piPredictionProcess - {}'.format(init_result))
		genQ.put(init_result)
		l.release()

	if init_result:
		logger.info('piPredictionProcess - Waiting for server connection')
		time.sleep(1)

		# runs prediction
		connStat = out2ServerQ.get()
		if connStat:
			try:
				piPredictionHandler.run(out2ServerQ)
			except KeyboardInterrupt:
				sys.exit(0)
		else:
			logger.debug('piPredictionProcess - connStat: {}'.format(connStat))
	sys.exit(1)


def piClientProcess(l, genQ, out2ServerQ):
	l.acquire()
	try:
		cont = genQ.get()
		logger.debug('piClientProcess: {}'.format(cont))
		if not cont:
			logger.critical('piClientProcess - Error in serialPiProcess. Unable to continue.')
	finally:
		l.release()

	if cont:
		logger.info('piClientProcess - Starting')
		# initialize client process
		try:
			myclient = client.clientMgr()
			connStat = myclient.conn(SERVER_IP,SERVER_PORT,out2ServerQ)
		except Exception as e:
			logger.critical('piClientProcess - Exception occured: {}'.format(e))
			sys.exit(1)

		finally:
			out2ServerQ.put(connStat)
	else:
		sys.exit(1)

	time.sleep(1)
	try:
		myclient.run(out2ServerQ)
	except KeyboardInterrupt:
		sys.exit(0)
	except Exception as e:
		logger.debug('piClientProcess - Exception occured: {}'.format(e))
		sys.exit(1)


def main():
	logger.info('Starting {}'.format(__file__))

	jobs = []
	genQ = mp.Queue()	# used for process startup status check and data from serialPi to piPrediction
	out2ServerQ = mp.Queue()	# queue for passing message from piPrediction to piClient

	lock = mp.Lock()

	p = mp.Process(target=serialPiProcess, args=(lock, genQ,))
	jobs.append(p)
	p.start()

	p = mp.Process(target=piPredictionProcess, args=(lock, genQ, out2ServerQ))
	jobs.append(p)
	p.start()

	p = mp.Process(target=piClientProcess, args=(lock, genQ, out2ServerQ))
	jobs.append(p)
	p.start()

	for proc in jobs:
		proc.join()


if __name__ == '__main__':
	main()
