import numpy as np
from scipy.signal import butter, lfilter, freqz
from matplotlib import pyplot as plt

def shitHotLP(data, cutoff, fs, order):
    b, a = butter_lowpass(cutoff, fs, order)
    v = butter_lowpass_filter(data, cutoff, fs, order)
    return v

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y