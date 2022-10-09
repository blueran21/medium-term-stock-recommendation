import pandas as pd
import time
import json
import numpy as np
import matplotlib.pyplot as plt
import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from keras.preprocessing.sequence import TimeseriesGenerator
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
# In[ ]:


class Stockprediction():
    def __init__(self, symbol, features_num, t_samples, next_days, epoch_num, batch_num):
        self.symbol = symbol
        self.features_num = features_num
        self.t_samples = t_samples
        self.next_days = next_days
        self.epoch_num = epoch_num
        self.batch_num = batch_num

    def calculate(self):
        stock = pd.read_csv('data/{}.csv'.format(self.symbol)) # import data

        X_r = stock.iloc[:, 1: 6]
        Y_r = stock.loc[:, ['Close']]
        min_max_scale1 = MinMaxScaler() # scale features' data
        X = min_max_scale1.fit_transform(X_r)
        min_max_scale2 = MinMaxScaler() # scale target data
        Y = min_max_scale2.fit_transform(Y_r)
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2, shuffle = False) # split train and test
        X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
        X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
        y_train = y_train.reshape(y_train.shape[0], 1, y_train.shape[1])
        y_test = y_test.reshape(y_test.shape[0], 1, y_test.shape[1])
        train_days = []
        train_target = []
        test_days = []
        test_target = []
        # build data input for LSTM
        for i in range(self.t_samples + self.next_days, X_train.shape[0]):
            train_days.append(X_train[(i - (self.t_samples + self.next_days)): (i - self.next_days), 0])
            train_target.append(y_train[(i - self.next_days): i, 0])
        for j in range(self.t_samples + self.next_days, X_test.shape[0]):
            test_days.append(X_test[(j - (self.t_samples + self.next_days)): (j - self.next_days), 0])
            test_target.append(y_test[(j - self.next_days): j, 0])

        train_days = np.array(train_days)
        train_target = np.array(train_target)
        test_days = np.array(test_days)
        test_target = np.array(test_target)

        train_target = np.reshape(train_target, (train_target.shape[0], train_target.shape[1]))
        test_target = np.reshape(test_target, (test_target.shape[0], test_target.shape[1]))

        # build model
        model = Sequential()
        model.add(LSTM(units=128, return_sequences=True, input_shape=(self.t_samples, self.features_num)))
        model.add(LSTM(units=64, return_sequences=True))
        model.add(Dropout(0.4))
        model.add(LSTM(units=32))
        model.add(Dropout(0.4))
        model.add(Dense(self.next_days))
        ADAM = keras.optimizers.Adam(0.0005, beta_1=0.9, beta_2=0.999, amsgrad=False)
        model.compile(loss='mean_squared_error', optimizer=ADAM)
        # train model
        history = model.fit(train_days, train_target, epochs=self.epoch_num, batch_size=self.batch_num, validation_data=(test_days, test_target), verbose=0, shuffle=False)
        # predict test
        yhat = model.predict(test_days)
        # reverse predicted value to initial value before scaled
        yhat_r = min_max_scale2.inverse_transform(yhat)
        # reverse actual value to initial value before scaled
        real_r = min_max_scale2.inverse_transform(test_target)
        #calculate root of mean square error
        rmse = np.sqrt(mean_squared_error(real_r, yhat_r))
        #calculate rmse for specific day
        rmse_0 = np.sqrt(mean_squared_error(real_r[:, 0], yhat_r[:, 0]))
        rmse_30 = np.sqrt(mean_squared_error(real_r[:, 29], yhat_r[:, 29]))
        rmse_45 = np.sqrt(mean_squared_error(real_r[:, 44], yhat_r[:, 44]))
        rmse_60 = np.sqrt(mean_squared_error(real_r[:, 59], yhat_r[:, 59]))
        #calculate r square
        predict = yhat_r[:, 0]
        actual = real_r[:, 0]
        r2_0 = r2_score(yhat_r[:, 0], real_r[:, 0])
        r2 = r2_score(yhat_r, real_r)
        #calculate r square for specific day
        r2_30 = r2_score(yhat_r[:, 29], real_r[:, 29])
        r2_45 = r2_score(yhat_r[:, 44], real_r[:, 44])
        r2_60 = r2_score(yhat_r[:, 59], real_r[:, 59])
        #find the date stamp of testing data
        test_date = stock.iloc[-(len(real_r) + 60): -60][['Date']]
        test_date = test_date['Date'].tolist()

        #translate testing to list format
        predict = predict.tolist()
        actual = actual.tolist()

        #calculate future days
        last_days = X[-self.t_samples: ]
        last_days = last_days.reshape(1, self.t_samples, self.features_num)
        future = model.predict(last_days)
        future = min_max_scale2.inverse_transform(future)
        future = future[0].tolist()
        
        days = {}
        element = {}
        element['rmse_0'], element['rmse_30'], element['rmse_45'], element['rmse_60'] = rmse_0, rmse_30, rmse_45, rmse_60
        element['r2_30'], element['r2_45'], element['r2_60'] = r2_30, r2_45, r2_60
        element['predict'], element['actual'], element['date'] = predict, actual, test_date
        element['rmse'], element['r2'], element['r2_0'], element['future'] = rmse, r2, r2_0, future
        days[self.symbol] = element
        with open('predict60/{}.json'.format(self.symbol), 'w') as fp:
            json.dump(days, fp)
 #       return rmse, r2, r2_real, future

