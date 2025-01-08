import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

class NNModel:
    def __init__(self, nn_model=None, input_dim=None):
        self._model = nn_model if nn_model else create_default_model(input_dim)

    @staticmethod
    def create_default_model(input_dim):
	    model = Sequential()
	    model.add(Dense(64, input_dim=input_dim, activation='relu'))
	    model.add(Dropout(0.5))
	    model.add(Dense(128, activation='relu'))
	    model.add(Dropout(0.5))
	    model.add(Dense(64, activation='relu'))
	    model.add(Dropout(0.5))
	    model.add(Dense(1, activation='sigmoid'))  # Для бинарной классификации
	    
	    custom_adam = Adam(learning_rate=0.000075)
	    model.compile(optimizer=custom_adam, loss='binary_crossentropy', metrics=['accuracy'])
	    
	    return model

    def fit(self, X, y):
        self._model.fit(X, y)

    def predict(self, X):
        return (self._model.predict(X, verbose=0) > 0.5).astype('int32')
