
import pandas as pd
import numpy as np
import butterworth
from collections import deque
from io import StringIO
from time import sleep
from scipy.stats import kurtosis, skew
from keras.models import load_model
from keras.models import Sequential





data_filepath = 'data/sample_data_format.csv' #mega_data.csv
model_filepath = 'data/har_rnn_lstm.h5'
readings = 128 #change to 40
waiting_time = 0.4 #0.4 seconds
prediction_threshold = 0.7
neutral_position = 0 
order = 6       # Order 6
fs = 40       # sample rate, Hz
cutoff = 5    # desired cutoff frequency of the filter in Hz (take max/60)


def get_data(filename, numlines):
	size = sum(1 for l in open(filename))
	return np.array(pd.read_csv(filename, nrows=numlines, skiprows=range(0, size-numlines)))


def get_model(modelname):
	return load_model(modelname)


def apply_filter(data):
	# Function to be called if you wanna use this Shit Hot Filter. Can u handle it?
	filteredResult = butterworth.shitHotLP(data, cutoff, fs, order)
	return filteredResult


def feature_extraction(x, y, z):
	#mean, std
	features = [np.mean(x), np.mean(y), np.mean(z), np.std(x), np.std(y), np.std(z)]
	#Median Absolute Deviation
	features.extend((np.mean(abs(x - features[0])), np.mean(abs(y - features[1])), np.mean(abs(z - features[2]))))
	#Jerk Signals
	features.extend((np.mean(np.diff(x)), np.mean(np.diff(y)), np.mean(np.diff(z)), np.std(np.diff(x)), np.std(np.diff(y)), np.std(np.diff(z))))
	features.extend((np.mean(abs(np.diff(x) - features[9])), np.mean(abs(np.diff(y) - features[10])), np.mean(abs(np.diff(y) - features[11]))))
	#skew, kurtosis, max, min
	features.extend((skew(x), skew(y), skew(z), kurtosis(x), kurtosis(y), kurtosis(z)))
	features.extend((max(x), max(y), max(z), min(x), min(y), min(z)))
	return features


def feature_selection(X):
	if X.ndim < 3:
		X = X.reshape(1, X.shape[0], X.shape[1])

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
	np.set_printoptions(formatter={'float_kind':'{:f}'.format})
	print('Probabilities')
	print(y)
	y_pred = np.argmax(y, axis=1)
	print('Predicted output: ', y_pred)
	return ((y_pred != neutral_position) and (y[0][y_pred] > prediction_threshold)), y_pred


def send_server(results):
	# Results should contain action, current and voltage data
	# Save results in .csv file for client.py to read
	#
	# List of actions available in client.py
	# Send an integer to invoke the following actions:
	# 0 - logout
	# 1 - wavehands
	# 2 - busdriver
	# 3 - frontback
	# 4 - sidestep
	# 5 - jumping
	# 6 - jumpingjack
	# 7 - turnclap
	# 8 - squatturnclap
	# 9 - windowcleaning
	# 10 - windowcleaner360
	pass

def init(modelname):
	return get_model(modelname)

def main_loop():
	model = init(model_filepath)
	sleep(0.8)
	while True:
		sleep(waiting_time)
		data = get_data(data_filepath, readings)
		with pd.option_context('display.max_rows', None, 'display.max_columns', 3):
			print(data)
		filtered_data = apply_filter(data)
		X = feature_selection(filtered_data)
		y = model.predict(X)
		is_result_good, results = check_results(y)
		if is_result_good:
			send_server(results)
		break #remove in actual code










