#!/usr/bin/env/python

from collections import Counter

from datetime import datetime
from dateutil.relativedelta import relativedelta

import matplotlib.pyplot as plt

import statsmodels.api as sm
import pandas as pd

import numpy as np

class SARIMA_model:
    """
    This class builds a seasonal based ARIMA model for the suppied time seires
    """
    start = datetime.strptime("2015-1-31", "%Y-%m-%d")
    date_list = [start + relativedelta(months=x) for x in range(0,12)]
    
    start2 = datetime.strptime("2006-1-31", "%Y-%m-%d")
    date_list2 = [start2 + relativedelta(months=x) for x in range(0,120)]
    
    def __init__(self, CT):
        """
				input - CT is the CrimeMapper object.
        
        """
				## Errors in the model 
        self.errors = []

				## The PQ values for the
        self.PDQ_Values = []

				## The time series for the 
        self.ts = CT.ts.Crimes
        
        self.temp = pd.DataFrame(index=self.date_list,
                                 columns=['Recorded',
                                          'Predicted'])
        
        self.temp['Recorded'] = self.ts[105:117].values
        
        self.pred_vs_record = pd.DataFrame(index=self.date_list2,
                                 columns=['Recorded',
                                          'Predicted'])

        self.pred_vs_record['Recorded'] = self.ts.values
        #print self.pred_vs_record
        

    def fit(self):
        """
        Fit the model to the data and tries to find the optimal p,q,P,Q values
        """
        for P in range(0,2):
            for Q in range(0,2):
                self.mod = sm.tsa.SARIMAX(self.ts, 
                                        order=(1,1,0),
                                        seasonal_order=(P,1,Q,12),
                                        enforce_invertibility=False,
                                        enforce_stationarity=False)
                
                result = self.mod.fit()

                self.temp['Predicted'] = result.predict(start=105,
                                                       end=117,
                                                       dynamic=True)
                values = [1,0,P,Q]
            
                self.errors.append( np.sqrt(sum(
                                    (self.temp['Predicted']-\
                                    self.temp['Recorded'])**2)\
                                    /len(self.temp['Predicted'])))
                
                self.PDQ_Values.append(values)
                
          
        
        for P in range(0,2):
            for Q in range(0,2):
                self.mod = sm.tsa.SARIMAX(self.ts, 
                                        order=(0,1,1),
                                        seasonal_order=(P,1,Q,12),
                                        enforce_invertibility=False,
                                        enforce_stationarity=False)
                
                result = self.mod.fit()

                self.temp['Predicted'] = result.predict(start=105,
                                                       end=117,
                                                       dynamic=True)
                #values = [p,1,q]
            
                self.errors.append( np.sqrt(sum(
                                    (self.temp['Predicted']-\
                                    self.temp['Recorded'])**2)\
                                    /len(self.temp['Predicted'])))
            

                values = [0,1,P,Q]
                self.PDQ_Values.append(values)
        
        for p in range(1,3):
            for q in range(1,3):
                for P in range(0,3):
                    for Q in range(0,3):
                        self.mod = sm.tsa.SARIMAX(self.ts, 
                                        order=(p,1,q),
                                        seasonal_order=(P,1,Q,12),
                                        enforce_invertibility=False,
                                        enforce_stationarity=False)
                
                        result = self.mod.fit()

                        self.temp['Predicted'] = result.predict(
                                                    start=105,
                                                    end=117,
                                            dynamic=True)

            
                        self.errors.append( np.sqrt(sum(
                                    (self.temp['Predicted']-\
                                     self.temp['Recorded'])**2)\
                                    /len(self.temp['Predicted'])))
                        
                        values = [0,1,P,Q]
                        self.PDQ_Values.append(values)
            
        self.index = np.argmin(self.errors)
        self.best_values = self.PDQ_Values[self.index]
        
        p = self.best_values[0]
        q = self.best_values[1]
        P = self.best_values[2]
        Q = self.best_values[3]
        
        self.mod = sm.tsa.SARIMAX(self.ts, 
                                order=(p,1,q),
                                seasonal_order=(P,1,Q,12),
                                enforce_invertibility=False,
                                enforce_stationarity=False)
        
        self.results = self.mod.fit()
        
        self.pred_vs_record['Predicted'] = self.results.predict(
                                                    start = 93,
                                                    end = 117, 
                                                    dynamic= True)
        
#        future = pd.DataFrame(index=self.date_list2, columns= df.columns)
#        df = pd.concat([df, future])
        
    def plot(self):
        """
				Plots the predicted and recorded crime values
        """
        self.pred_vs_record[['Predicted',
                             'Recorded']].plot(figsize=(8,4),linewidth=3)   
        
