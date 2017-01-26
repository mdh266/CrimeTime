#!/usr/bin/env/python

from collections import Counter

from datetime import datetime
from dateutil.relativedelta import relativedelta

import matplotlib.pyplot as plt

import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import pandas as pd

import numpy as np

#zzimport seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class Seasonal_Arima(object):
	"""
  	This class builds a seasonal based ARIMA model for the suppied time seires
	"""

	def __init__(self, CT):
		"""
		Input = CT is the CrimeMapper object
		training set : 1/2006 - 12/2014
		validation set : 1/2014 - 12/2014
		test set : 1/2015 - 12/2015
		
		The constructor builds the training, validation and test set from the 
		CrimeMapper object and also initializes the data members to be zero.
		"""
		
		training_start = datetime.strptime("2006-1-31","%Y-%m-%d")

		## Dates for the training set time series
		self.training_date_list = [training_start 
				+ relativedelta(months=x) for x in range(0,108)]

		validation_start = datetime.strptime("2014-1-31","%Y-%m-%d")
		## Dates for the validation set time series
		self.validation_date_list = [validation_start 
				+ relativedelta(months=x) for x in range(0,12)]

		test_start = datetime.strptime("2015-1-31","%Y-%m-%d")

		## Dates for the test set time series
		self.test_date_list = [test_start 
				+ relativedelta(months=x) for x in range(0,12)]
	
		forecast_start = datetime.strptime("2016-1-31","%Y-%m-%d")

		## Dates for the forecasting time series
		self.forecast_date_list = [forecast_start 
				+ relativedelta(months=x) for x in range(0,24)]

		## Dataframe for first difference and seasonal first difference
		self.df = pd.DataFrame(data=CT.ts,columns=['Crimes'])

		## Errors in the model in the grid search
		self.errors = []
		
		## Grid search (p,q,d) and (P, Q, D) values for the model 
		self.PDQ_vals = []
		
		## The p values in ARIMA
		self.p = None
		
		## The q values in ARIMA
		self.q = None

		## The d values in ARIMA
		self.d = None

		## The P values in ARIMA
		self.P = None

		## The D values in ARIMA
		self.D = None

		## The Q values in ARIMA
		self.Q = None

		## List of the [p,d,q,P,D,Q] values for seasonal ARIMA
		self.params = None
		
		## The RMS error on the test
		self.test_error = None

		## Starting index for the training set
		self.training_begin = 0
	
		## Ending index for the training set
		self.training_end   = 108

		## Starting index for the validation set
		self.validation_begin = 96

		## Starting index for the validation set
		self.validation_end   = 108

		## Starting index for the test set
		self.test_begin	    = 108

		## Starting index for the test set
		self.test_end	    = 120

		## Starting index for the forecasting set
		self.forecast_begin = 120

		## Starting index for the forecasting set
		self.forecast_end   = 144
			
		## The training set time series data
		self.training  =  pd.DataFrame(index=self.training_date_list,
						columns=['Recorded',	
							 'Predicted'])
		
		self.training['Recorded'] = CT.ts[self.training_begin:self.training_end]


		## The validation set time series data
		self.validation = pd.DataFrame(index=self.validation_date_list,
						columns=['Recorded',
							 'Predicted'])

		self.validation['Recorded'] = CT.ts[self.validation_begin:self.validation_end]

		## The test set time series data
		self.test = pd.DataFrame(index=self.test_date_list,
						columns=['Recorded',
					 	 	 'Predicted'])

		self.test['Recorded'] = CT.ts[self.test_begin:self.test_end]


	def stationarity(self, timeseries):
		"""
		Perform Dickey-Fuller test:
		"""
		# used from 
		#http://www.seanabu.com/2016/03/22/time-series-seasonal-ARIMA-model-in-python/
		#Determing rolling statistics
		rolmean = timeseries.rolling(window=12,center=False).mean()
		rolstd = timeseries.rolling(window=12,center=False).std()
		
		#Plot rolling statistics:
		fig = plt.figure(figsize=(8, 6))
		orig = plt.plot(timeseries, color='blue',label='Original')
		mean = plt.plot(rolmean, color='red', label='Rolling Mean')
		std = plt.plot(rolstd, color='black', label = 'Rolling Std')
		plt.legend(loc='best')
		plt.title('Rolling Mean & Standard Deviation')
		plt.show()
    
		print 'Results of Dickey-Fuller Test:'
		dftest = adfuller(timeseries, autolag='AIC')
		dfoutput = pd.Series(dftest[0:4], index=['Test Statistic','p-value',
					'#Lags Used','Number of Observations Used'])
		for key,value in dftest[4].items():
			dfoutput['Critical Value (%s)'%key] = value
		print dfoutput 

	def first_diff(self):
		"""
		Obtains the first difference and performs Dickey-Fuller test for stationarity.
		"""
		print "\nFirst Difference:\n"
		self.df['first_diff'] = self.df.Crimes - self.df.Crimes.shift(1)
		self.stationarity(self.df.first_diff.dropna(inplace=False))

	def seasonal_first_diff(self):
		"""
		Obtains the first seasonal difference and performs Dickey-Fuller test for stationarity
		"""
		print "\nSeasonal First Difference:\n"
		self.df['first_seasonal_diff'] = self.df.first_diff - self.df.first_diff.shift(12)
		self.stationarity(self.df.first_seasonal_diff.dropna(inplace=False))

	def fit(self):
		"""
		Run throught the different values ARIMA parameter values and fit the model
		to the training set.  Collect the error of how it performs on the validation
		set and then find the (p,d,q,P,D,Q) values that give the lowest
		error on the validation set. 

		Then forecast it into 2015 which is the test set, which it has NOT
		seen.  Then get the error on this set.  
		"""

		#####################################################################	
		# Train the model and get the errors on the validation set
		#####################################################################
		
		for p in range(0,2):
			for q in range(0,2):
				for P in range(0,3):
					for Q in range(0,3):
						try:
							self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                               						order=(p,1,q),
                                      					seasonal_order=(P,1,Q,12),
                                      					enforce_invertibility=True,
                                      					enforce_stationarity=True)
	
							result = self.mod.fit()
				
		
							self.validation['Predicted'] = result.predict(	
									start=self.validation_begin,
                        			                        end=self.validation_end,
                                                			dynamic=True)


							self.errors.append( np.sqrt(sum(
                             					 (self.validation['Predicted']-\
                               					self.validation['Recorded'])**2)\
                               					/len(self.validation['Predicted'])))


							values = [p,1,q,P,1,Q]
	
							self.PDQ_vals.append(values)
						except:
							pass

		#####################################################################	
		# Now find the best model and find error on test set
		#####################################################################

		future = pd.DataFrame(index=self.test_date_list,
				      columns=self.training.columns)

		self.training = pd.concat([self.training, future])

		self.index = np.argmin(self.errors)
		
		self.p = self.PDQ_vals[self.index][0]
		self.d = self.PDQ_vals[self.index][1]
		self.q = self.PDQ_vals[self.index][2]
		self.P = self.PDQ_vals[self.index][3]
		self.D = self.PDQ_vals[self.index][4]
		self.Q = self.PDQ_vals[self.index][5]

		self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                              		order=(self.p,self.d,self.q),
                              		seasonal_order=(self.P,self.D,self.Q,12),
                            		enforce_invertibility=False,
                              		enforce_stationarity=False)


		self.results = self.mod.fit()

		self.test['Predicted'] = self.results.predict(start = self.test_begin,
                                                	      end = self.test_end, 
                                                  	      dynamic= True)

		
		self.test_error =  np.sqrt(sum(
                              (self.test['Predicted']-\
                               self.test['Recorded'])**2)\
                               /len(self.test['Predicted']))

		self.params = [self.p, self.d, self.q, self.P, self.D, self.Q]

		#####################################################################	
		# Now train the model on the WHOLE data set
		#####################################################################
		
		self.training['Recorded'][self.test_begin:self.test_end] = self.test['Recorded']


	def forecast(self):
		""" 
		Forecast the crime rates into 2016 and 2017.
		"""

		forecast = pd.DataFrame(index=self.forecast_date_list, 
					 columns=self.training.columns)

		self.training = pd.concat([self.training, forecast])

		self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                              		order=(self.p,self.d,self.q),
                              		seasonal_order=(self.P,self.D,self.Q,12),
                            		enforce_invertibility=True,
                              		enforce_stationarity=False)


		self.results = self.mod.fit()

		self.forecast_results = self.results.predict(start = self.forecast_begin,
                                        		    end = self.forecast_end, 
                                      			    dynamic= True)

			
	def plot_test(self):
		"""
		Plots the predicted and recorded crime values on the test set.
		"""	
		self.test[['Recorded','Predicted']].ix[-12:].plot(linewidth=3)
		plt.ylabel('Monthlt incidents')
		plt.xlabel('Year')  
	

	def plot_forecast(self):
		"""
		Plots the predicted and recorded crime values on the test set.
		"""
		#plt.clf()
		plt.plot(self.forecast_results - self.test_error, 'r')
		plt.plot(self.forecast_results + self.test_error, 'r')
		self.forecast_results.ix[-24:].plot(linewidth=2.5)
		plt.ylabel('Monthlt incidents')
		plt.xlabel('Year')  
        
