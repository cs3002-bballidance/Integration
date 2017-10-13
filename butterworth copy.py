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


# Filter requirements. DEPENDS ON RAHMAN OF NUS CEG
data = ([[  2,   1,   2,   2,   1],
       [  5,   6,   7,   8,   9],
       [ 10,  11,  12,  13,  14],
       [ 15,  16,  17,  18,  19],
       [ 20,  21,  22,  23,  900]])   # Data in Matrix format
order = 6       # Order 6
fs = 40       # sample rate, Hz
cutoff = 5    # desired cutoff frequency of the filter in Hz (take max/60)


# Function to be called if you wanna use this Shit Hot Filter. Can u handle it?
filteredResult = shitHotLP(data, cutoff, fs, order)

print(filteredResult)
