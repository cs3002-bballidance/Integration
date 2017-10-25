import logging
import csv
import client
import sys
import pandas as pd
import numpy as np
import butterworth
from collections import deque
from io import StringIO
from time import sleep
from scipy.stats import kurtosis, skew
from keras.models import load_model
from keras.models import Sequential

class predictionMgr():
	def __init__(self):
		self.name = 'piPrediction'
		self.logger = logging.getLogger(self.name)
		self.logger.info('Initializing {} ({})'.format(self.name,__file__))

		self.DATAPATH = 'data/mega_data.csv' #mega_data.csv
		self.RESULT_DATAPATH = 'data/results.csv'
		self.MODELPATH = 'data/trained_nn_model.h5'
		self.SAMPLING_RATE = 50
		self.WINDOW_SIZE = 2
		self.WINDOW_READINGS = int(self.WINDOW_SIZE * self.SAMPLING_RATE)
		self.WAITING_TIME = 1 #50% OVERLAPPING
		self.PREDICTION_THRESHOLD = 0.8
		self.NATURAL_MOVE = 0
		self.CLOSING_MOVE = 11

		self.ORDER = 3
		self.CUTOFF = 7
		self.FILTER_SAMPLING_RATE = 20

		self.SEND_TO_SERVER = False
		self.RESULT = 0
		self.MEAN_VOLTAGE = 0
		self.MEAN_CURRENT = 0
		self.COUNT = 0


	def status(self):
		self.logger.info('status: True')
		return True


	def run(self, out2ServerQ):
		self.model = self.get_model(self.MODELPATH)
		# model = init(self.MODELPATH)
		sleep(self.WINDOW_SIZE)
		while True:
			try:
				sleep(self.WAITING_TIME)
				data, power_data = self.get_data(self.DATAPATH, self.WINDOW_READINGS)
				#with pd.option_context('display.max_rows', None, 'display.max_columns', 3):
					#logger.debug(data)
				filtered_data = self.apply_filter(data, self.CUTOFF, self.FILTER_SAMPLING_RATE, self.ORDER)
				#X = feature_selection(filtered_data)MEAN_VOLTAGE
				X = self.reshape_data(filtered_data)
				y = self.model.predict(X)
				is_result_good, results = self.check_results(y)
				if is_result_good:
					results = self.prepare_results(results, power_data)
					out2ServerQ.put(results)
					self.logger.debug("out2ServerQ contents: {}".format(results))
					#break #remove in actual code
			except Exception as e:
				self.logger.critical('Exception occured: {}'.format(e))


	def get_data(self, filename, numlines):
		size = sum(1 for l in open(filename))
		self.logger.debug("file size: {}".format(size))
		data = pd.read_csv(filename, nrows=numlines, skiprows=range(0, size-numlines-1))
		return data.iloc[:, 0:9], data.iloc[:, 9:11]


	def get_model(self, modelname):
		return load_model(modelname)


	def apply_filter(self, data, cutoff, readings, order):
		# Function to be called if you wanna use this Shit Hot Filter. Can u handle it?
		filteredResult = butterworth.shitHotLP(data, cutoff, readings, order)
		return filteredResult


	def normalize_data(self, data):
		data_norm = (data - data.mean()) / (data.max() - data.min())
		return np.array(data_norm)


	def magnitude(self, x, y, z):
		x_sq = np.power(x, 2)
		y_sq = np.power(y, 2)
		z_sq = np.power(z, 2)

		xyz_sq = x_sq + y_sq + z_sq

		xyz_mag = np.sqrt(xyz_sq)
		return xyz_mag


	def rms(self, x, axis=None):
		return np.sqrt(np.mean(np.power(x, 2), axis=axis))


	def feature_extraction(self, x, y, z):
		#'''
		#mean, std
		features = [np.mean(x), np.mean(y), np.mean(z), np.std(x), np.std(y), np.std(z)]
		#Median Absolute Deviation
		features.extend((np.mean(abs(x - features[0])), np.mean(abs(y - features[1])), np.mean(abs(z - features[2]))))
		#Jerk Signals mean, std, mad
		features.extend((np.mean(np.diff(x)), np.mean(np.diff(y)), np.mean(np.diff(z)), np.std(np.diff(x)), np.std(np.diff(y)), np.std(np.diff(z))))
		features.extend((np.mean(abs(np.diff(x) - features[9])), np.mean(abs(np.diff(y) - features[10])), np.mean(abs(np.diff(y) - features[11]))))
		#max, min
		features.extend((max(x), max(y), max(z), min(x), min(y), min(z)))
		#correlation
		features.extend((np.correlate(x, y)[0], np.correlate(x, z)[0], np.correlate(y, z)[0]))
		#energy
		features.extend((np.dot(x,x)/len(x), np.dot(y,y)/len(y), np.dot(z,z)/len(z)))
		#iqr
		#features.extend((np.subtract(*np.percentile(x, [75, 25])), np.subtract(*np.percentile(y, [75, 25])), np.subtract(*np.percentile(z, [75, 25]))))
		#Root Mean Square
		features.extend((rms(x), rms(y), rms(z)))
		#Skew, Kurtosis
		features.extend((skew(x), skew(y), skew(z), kurtosis(x), kurtosis(y), kurtosis(z)))
		#'''

		'''
		#Old Feature Extractionself.
		features = [np.mean(x), np.mean(y), np.mean(z), np.std(x), np.std(y), np.std(z)]
		#Median Absolute Deviation
		features.extend((np.mean(abs(x - features[0])), np.mean(abs(y - features[1])), np.mean(abs(z - features[2]))))
		#Jerk Signals
		features.extend((np.mean(np.diff(x)), np.mean(np.diff(y)), np.mean(np.diff(z)), np.std(np.diff(x)), np.std(np.diff(y)), np.std(np.diff(z))))
		features.extend((np.mean(abs(np.diff(x) - features[9])), np.mean(abs(np.diff(y) - features[10])), np.mean(abs(np.diff(y) - features[11]))))
		features.extend((skew(x), skew(y), skew(z), kurtosis(x), kurtosis(y), kurtosis(z)))
		features.extend((max(x), max(y), max(z), min(x), min(y), min(z)))
		'''
		return features


	def reshape_data(self, data):
		return data.reshape(1, data.shape[0], data.shape[1])


	def feature_selection(self, X):
		if X.ndim < 3:
			X = self.reshape_data(X)

		data = []
		for i in range(X.shape[0]):
			features = []
			for j in range(0, X.shape[2], 3):
				x = [X[i][u][j] for u in range(X.shape[1])]
				y = [X[i][u][j+1] for u in range(X.shape[1])]
				z = [X[i][u][j+2] for u in range(X.shape[1])]
				features.append(feature_extraction(x, y, z))
			data.append(features)
		return np.array(data)


	def check_results(self, y):
		np.set_printoptions(formatter={'float_kind':'{:f}'.format})
		self.logger.info("Probabilities: {}".format(y))
		y_pred = np.argmax(y, axis=1)[0]
		#logger.debug('Predicted output: ', y_pred)
		send_result = (self.RESULT == y_pred) and (y_pred != self.NATURAL_MOVE) and (y[0][y_pred] > self.PREDICTION_THRESHOLD)
		self.RESULT = y_pred
		return send_result, y_pred


	def prepare_results(self, result, power_data):
		power_data = np.mean(power_data)
		self.MEAN_VOLTAGE = power_data[0]
		self.MEAN_CURRENT = power_data[1]
		self.SEND_TO_SERVER = True
		self.logger.info("Count: {} Results: {} {} {}".format(self.COUNT, self.RESULT, self.MEAN_VOLTAGE, self.MEAN_CURRENT))
		self.COUNT = self.COUNT + 1

		results = [self.RESULT, self.MEAN_VOLTAGE, self.MEAN_CURRENT]
		return results
		# with open(self.RESULT_DATAPATH, 'w') as csvfile:
		# 	w = csv.writer(csvfile)
		# 	w.writerow(results)


	def send_server(self):
		#result, mean voltage, mean current`
		return self.RESULT, self.MEAN_VOLTAGE, self.MEAN_CURRENT

	#
	# def init(self, modelname):
	# 	return get_model(modelname)


def main():
	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
	logger = logging.getLogger('dancePrediction')
	logger.warn('You should initiate this script as a module')
	sys.exit(1)


if __name__ == '__main__':
	main()
