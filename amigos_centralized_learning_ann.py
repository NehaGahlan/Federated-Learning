# -*- coding: utf-8 -*-
"""AMIGOS_Centralized_learning_ANN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PMFcbzSLT_cUJOW1NHKBDleuMBLA78Y6

Importing Libraries
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from keras.models import Sequential

"""Loading Dataset"""

X = pd.read_csv('/content/drive/MyDrive/Datasets/AMIGOS/Global_Data/X.csv')
y = pd.read_csv('/content/drive/MyDrive/Datasets/AMIGOS/Global_Data/y.csv')
y = y.drop(['Users','Arousal','Valence','Video'], axis = 1)

y[y['Dominance'] <= 4.5] = 0
y[y['Dominance'] > 4.5] = 1

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

train_features = pd.read_csv('/content/drive/MyDrive/Datasets/AMIGOS/Global_Data/X_train.csv') # train features data
train_labels = pd.read_csv('/content/drive/MyDrive/Datasets/AMIGOS/Global_Data/y_train.csv') # train labels data
test_features = pd.read_csv('/content/drive/MyDrive/Datasets/AMIGOS/Global_Data/X_test.csv') # test features data
test_labels = pd.read_csv('/content/drive/MyDrive/Datasets/AMIGOS/Global_Data/y_test.csv') # test labels data

X_train = np.array(X_train).reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = np.array(X_test).reshape(X_test.shape[0], X_test.shape[1], 1)

"""### Without FL, Centralized Model """

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Define the Attention layer
class Attention(layers.Layer):
    def __init__(self, hidden_dim):
        super(Attention, self).__init__()
        self.hidden_dim = hidden_dim
        self.attention_weights = layers.Dense(hidden_dim, activation='tanh')
        self.attention_values = layers.Dense(1)
    
    def call(self, inputs):
        attention_score = self.attention_weights(inputs)
        attention_weights = tf.nn.softmax(self.attention_values(attention_score), axis=1)
        context_vector = attention_weights * inputs
        context_vector = tf.reduce_sum(context_vector, axis=1)
        return context_vector

# Define the model architecture
model = keras.Sequential()
model.add(layers.Dense(128, activation='relu', input_shape=(168,)))
model.add(layers.Dropout(0.2))
model.add(layers.Dense(64, activation='relu'))
model.add(layers.Dropout(0.2))


# Compile the model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(train_features,train_labels, epochs=100, batch_size=2)

#  Evaluate the performance of your model on a test set
test_loss, test_acc = model.evaluate(X_test, y_test)

print("Test loss: {:.3f}, Test accuracy: {:.3f}".format(test_loss, test_acc))