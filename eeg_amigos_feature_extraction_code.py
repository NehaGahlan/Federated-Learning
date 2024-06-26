# -*- coding: utf-8 -*-
"""EEG_Amigos_Feature_Extraction_code.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/168st6Oc5O_a6bjZj9TsoqSfUpLnrzy4E
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
path = pd.read_csv('/content/drive/MyDrive/Datasets/Amigos/Mat_toCSV/User22/short_videos/14_channels/5120/vid_1.csv')

#path.isnull()
path.isna().any()
#path[path.isna().any(axis=1)]

!pip install antropy

import numpy as np
import pandas as pd
from collections import OrderedDict
import random
import antropy as ant

from scipy.integrate import simps
from scipy import signal
from scipy.signal import welch

import pywt

"""# 1. Helper Functions for Time, Frequency and Time-Frequency Features"""

def time_features(sample, NUM_CHANNELS, SAMPLING_FREQUENCY, WINDOW_SIZE):
    '''
    Computes the following features for all the channels of an EEG signal
    # Entropy:
        1. Hjorth Mobility and Complextiy
    # Fractal Dimenstions:
        1. Higuchi FD
        2. Petrosian
    @params:
        sample: EEG signal sample of shape (NUM_CHANNELS, SAMPLING_FREQUENCY * WINDOW_SIZE)
        NUM_CHANNELS: # of EEG channels
        SAMPLING_FREQUENCY: EEG sampling frequency
        WINDOW_SIZE: sliding window size (# of rows)
    @returns:
        features_for_sample: 1D list of all time features
    '''
    features_for_sample = []
    for i in range(NUM_CHANNELS):
        (h_mobility, h_complexity) = ant.hjorth_params(sample[i])

        higuchi_fd = ant.higuchi_fd(sample[i])
        petrosian = ant.petrosian_fd(sample[i])

        features = [h_mobility, h_complexity, higuchi_fd, petrosian]
        features_for_sample.extend(features)
    return features_for_sample

def bandpower(data, sf, band, window_sec=None, relative=False):
    """Compute the average power of the signal x in a specific frequency band.

    Parameters
    ----------
    data : 1d-array
        Input signal in the time-domain.
    sf : float
        Sampling frequency of the data.
    band : list
        Lower and upper frequencies of the band of interest.
    window_sec : float
        Length of each window in seconds.
        If None, window_sec = (1 / min(band)) * 2
    relative : boolean
        If True, return the relative power (= divided by the total power of the signal).
        If False (default), return the absolute power.

    Return
    ------
    bp : float
        Absolute or relative band power.
    """
    
    band = np.asarray(band)
    low, high = band

    # Define window length
    if window_sec is not None:
        nperseg = window_sec * sf
    else:
        nperseg = (2 / low) * sf

    # Compute the modified periodogram (Welch)
    freqs, psd = welch(data, sf, nperseg=nperseg)

    # Frequency resolution
    freq_res = freqs[1] - freqs[0]

    # Find closest indices of band in frequency vector
    idx_band = np.logical_and(freqs >= low, freqs <= high)

    # Integral approximation of the spectrum using Simpson's rule.
    bp = simps(psd[idx_band], dx=freq_res)

    if relative:
        bp /= simps(psd, dx=freq_res)
    return bp

def frequency_features(sample, NUM_CHANNELS, SAMPLING_FREQUENCY, WINDOW_SIZE):
    '''
    Computes the following features for all the channels of an EEG signal
    # Entropy:
        1. Spectral Entropy
        2. SVD Entropy
        3. Sample Entropy
    @params:
        sample: EEG signal sample of shape (SAMPLING_FREQUENCY * WINDOW_SIZE, NUM_CHANNELS)
        NUM_CHANNELS: # of EEG channels
        SAMPLING_FREQUENCY: EEG sampling frequency
        WINDOW_SIZE: sliding window size (# of rows)
    @returns:
        features_for_sample: 1D list of all frequency features
    '''
    features_for_sample = []
    for i in range(NUM_CHANNELS):
        spectral = ant.spectral_entropy(sample[i], sf=SAMPLING_FREQUENCY, method='welch', normalize=True)
        svd = ant.svd_entropy(sample[i], normalize=True)
        samp = ant.sample_entropy(sample[i])

        theta_bandpower = bandpower(sample[i], SAMPLING_FREQUENCY, [4, 8], window_sec=5, relative=True)
        alpha_bandpower = bandpower(sample[i], SAMPLING_FREQUENCY, [8, 12], window_sec=5, relative=True)
        beta_bandpower = bandpower(sample[i], SAMPLING_FREQUENCY, [12, 35], window_sec=5, relative=True)
        gamma_bandpower = bandpower(sample[i], SAMPLING_FREQUENCY, [35, 45], window_sec=5, relative=True)

        features = [spectral, svd, samp, theta_bandpower, alpha_bandpower, beta_bandpower, gamma_bandpower]
        features_for_sample.extend(features)
    return features_for_sample

"""# 2. Load Data"""

PATH_TO_DATASET = "/content/drive/MyDrive/Datasets/Amigos/Mat_toCSV/User23/short_videos/14_channels/5120/"
SEED = 200

# LABEL = 0 # Valence
# LABEL = 1 # Arousal
# LABEL = 2 # Dominance

import numpy as np
import pandas as pd
import _pickle as cPickle
import random
import tensorflow as tf
from sklearn.model_selection import train_test_split

def get_data(vid_id):
    path = PATH_TO_DATASET + 'vid_%d.csv' % (vid_id)
    df = pd.read_csv(path)
    sub_data = np.array(df)
    return sub_data

sub_data = {}
# sub_labels = {}

for vid_id in range(1, 17):
    data = get_data(vid_id)
    sub_data[vid_id] = np.transpose(data)
    print(f"Video = {vid_id}, Shape = {sub_data[vid_id].shape}")

WINDOW_SECONDS = 5
SAMPLING_FREQUENCY = 128
WINDOW_SIZE = SAMPLING_FREQUENCY * WINDOW_SECONDS
START_TIMESTAMP = 0
NUM_CHANNELS = 14
STEP_SIZE = SAMPLING_FREQUENCY * 3

train_data = []
test_data = []
train_labels = []
test_labels = []

for vid_id in range(1, 17):
    data = sub_data[vid_id]
    DATA_LEN = data.shape[1]
    vid_features = []
    print(f"---\nVideo {vid_id}")
    for j in range(START_TIMESTAMP, DATA_LEN - WINDOW_SIZE, STEP_SIZE):
        print(f"Video {vid_id} / 16: ({j} - {j + WINDOW_SIZE}) / {DATA_LEN} ; Channels = {data.shape[0]}")
        sample = data[:, j : j + WINDOW_SIZE]
        print(sample.shape)
        features = time_features(sample, NUM_CHANNELS, SAMPLING_FREQUENCY, WINDOW_SIZE)
        features.extend(frequency_features(sample, NUM_CHANNELS, SAMPLING_FREQUENCY, WINDOW_SIZE))
        
        features = np.array(features)
        
        print("Features shape = ", features.shape)
        vid_features.append(features)

    train_data.extend(vid_features)
    
train_data = np.array(train_data)

train_data = np.array(train_data)
train_data.shape

df=pd.DataFrame(train_data)
df.to_csv("/content/drive/MyDrive/Datasets/Amigos/Mat_toCSV/User22/short_videos/14_channels/eeg_features/Data22.csv")