
import pandas as pd
import numpy as np
import logging, sys
import csv
import butterworth
from collections import deque
from io import StringIO
from time import sleep
from scipy.stats import kurtosis, skew
from keras.models import load_model
from keras.models import Sequential

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


DATAPATH = 'data/mega_data.csv' #mega_data.csv
RESULT_DATAPATH = 'data/results.csv'
MODELPATH = 'data/trained_nn_model.h5'
SAMPLING_RATE = 50
WINDOW_SIZE = 2
WINDOW_READINGS = int(WINDOW_SIZE * SAMPLING_RATE)
WAITING_TIME = 2*0.7 #30% OVERLAPPING
PREDICTION_THRESHOLD = 0.8
NATURAL_MOVE = 0
CLOSING_MOVE = 11 

ORDER = 3
CUTOFF = 7
FILTER_SAMPLING_RATE = 20

SEND_TO_SERVER = False
RESULT = 0
MEAN_VOLTAGE = 0
MEAN_CURRENT = 0
COUNT = 0



def get_data(filename, numlines):
	size = sum(1 for l in open(filename))
	data = pd.read_csv(filename, nrows=numlines, skiprows=range(0, size-numlines-1))
	return data.iloc[:, 0:9], data.iloc[:, 9:11]

def get_model(modelname):
	return load_model(modelname)


def apply_filter(data, cutoff, readings, order):
	# Function to be called if you wanna use this Shit Hot Filter. Can u handle it?
	filteredResult = butterworth.shitHotLP(data, cutoff, readings, order)
	return filteredResult

def normalize_data(data):
	data_norm = (data - data.mean()) / (data.max() - data.min())
	return np.array(data_norm)

def magnitude(x, y, z):
	x_sq = np.power(x, 2)
	y_sq = np.power(y, 2)
	z_sq = np.power(z, 2)

	xyz_sq = x_sq + y_sq + z_sq

	xyz_mag = np.sqrt(xyz_sq)
	return xyz_mag

def rms(x, axis=None):
	return np.sqrt(np.mean(np.power(x, 2), axis=axis))

def feature_extraction(x, y, z):
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
	#Old Feature Extraction
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

def reshape_data(data):
	return data.reshape(1, data.shape[0], data.shape[1])

def feature_selection(X):
	if X.ndim < 3:
		X = reshape_data(X)

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


def check_results(y):
	global RESULT
	np.set_printoptions(formatter={'float_kind':'{:f}'.format})
	logging.debug("Probabilities: {}".format(y))
	#print("Probabilities: {}".format(y))
	y_pred = np.argmax(y, axis=1)[0]
	#logging.debug('Predicted output: ', y_pred)
	#print("Prediction: {}".format(y_pred))
	send_result = (RESULT == y_pred) and (y_pred != NATURAL_MOVE) and (y[0][y_pred] > PREDICTION_THRESHOLD)
	RESULT = y_pred
	#print(send_result)
	return send_result, y_pred

def prepare_results(result, power_data):
	global COUNT
	power_data = np.mean(power_data)
	MEAN_VOLTAGE = power_data[0]
	MEAN_CURRENT = power_data[1]
	SEND_TO_SERVER = True
	#print("Result: {} {} {} {}".format(COUNT, RESULT, MEAN_VOLTAGE, MEAN_CURRENT))
	logging.debug("Result: {} {} {} {}".format(COUNT, RESULT, MEAN_VOLTAGE, MEAN_CURRENT))
	COUNT = COUNT + 1

	results = [RESULT, MEAN_VOLTAGE, MEAN_CURRENT]

	with open(RESULT_DATAPATH, 'a') as csvfile:
		w = csv.writer(csvfile)
		w.writerow(results)

def send_server():
	#result, mean voltage, mean current`
	return RESULT, MEAN_VOLTAGE, MEAN_CURRENT

def init(modelname):
	return get_model(modelname)

def main_loop():
	logging.info('Starting {}'.format(__file__))

	model = init(MODELPATH)
	sleep(WINDOW_SIZE)
	while True:
		sleep(WAITING_TIME)
		data, power_data = get_data(DATAPATH, WINDOW_READINGS)
		#with pd.option_context('display.max_rows', None, 'display.max_columns', 3):
			#logging.debug(data)
		filtered_data = apply_filter(data, CUTOFF, FILTER_SAMPLING_RATE, ORDER)
		#X = feature_selection(filtered_data)
		X = reshape_data(filtered_data)
		y = model.predict(X)
		is_result_good, result = check_results(y)
		if is_result_good:
			prepare_results(result, power_data)		
		#break #remove in actual code

if __name__ == '__main__':
	main_loop()








