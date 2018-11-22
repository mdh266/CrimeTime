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

class Seasonal_ARIMA:
	"""
  	This class builds a seasonal based ARIMA model using 
	`StatsModels <http://statsmodels.sourceforge.net/0.6.0/generated/statsmodels.tsa.arima_model.ARIMA.html>`_.
	
	**CT** is the ( :class:`backend.CrimeMapper.CrimeMapper` ) object that 
	has the crime data for this precinct.  

	**Note:** make_time_series() needs to have been called before.
		
	:attributes:
		
		**training_date_list** (list) :
			Training date set, contains months from 1/2006 - 12/2014.

		**validation_date_list** (list) :
			Validation date set, contains months from 1/2014 - 12/2014.

		**test_date_list** (list) :
			Test date set, contains months from 1/2015 - 12/2015.

		**forecast_date_list** (list) :
			Forecasting date set, contains months from 1/2016 - 12/2017.


		**params** (list)
			The p,d,q,P,D,Q values in the Seasonal ARIMA model.

		**test_error** (float)
			The root mean square error in our model.
		
		**training** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_)
			The training set recorded and predicted monthly crime rates.

		**validation** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_)
			The validation set recorded and predicted monthly crime rates.

		**test** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_)
			The test set recorded and predicted monthly crime rates.

	:methods:
	--------
	"""

	def __init__(self, CT):
		"""
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
		self._errors = []
		
		## Grid search (p,q,d) and (P, Q, D) values for the model 
		self._PDQ_vals = []
		
		## The p values in ARIMA
		self._p = None
		
		## The q values in ARIMA
		self._q = None

		## The d values in ARIMA
		self._d = None

		## The P values in ARIMA
		self._P = None

		## The D values in ARIMA
		self._D = None

		## The Q values in ARIMA
		self._Q = None

		## List of the [p,d,q,P,D,Q] values for seasonal ARIMA
		self.params = None
		
		## The RMS error on the test
		self.test_error = None

		## Starting index for the training set
		self._training_begin = 0
	
		## Ending index for the training set
		self._training_end   = 96

		## Starting index for the validation set
		self._validation_begin = 96

		## Starting index for the validation set
		self._validation_end   = 108

		## Starting index for the test set
		self._test_begin	    = 108

		## Starting index for the test set
		self._test_end	    = 120

		## Starting index for the forecasting set
		self._forecast_begin = 120

		## Starting index for the forecasting set
		self._forecast_end   = 144
			
		## The training set time series data
		self.training  =  pd.DataFrame(index=self.training_date_list,
										columns=['Recorded', 'Predicted'])
		
		self.training['Recorded'] = CT.ts[self._training_begin:self._training_end]


		## The validation set time series data
		self.validation = pd.DataFrame(index=self.validation_date_list,
									   columns=['Recorded','Predicted'])

		self.validation['Recorded'] = CT.ts[self._validation_begin:self._validation_end]

		## The test set time series data
		self.test = pd.DataFrame(index=self.test_date_list,
								columns=['Recorded','Predicted'])

		self.test['Recorded'] = CT.ts[self._test_begin:self._test_end]


	def stationarity(self, timeseries):
		"""
		Performs Dickey-Fuller test for stationarity and plots the results.

		:parameters: (`Pandas <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.html>`_)
			The Pandas Series of the monthly crime data.
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
    
		print('Results of Dickey-Fuller Test:')
		dftest = adfuller(timeseries, autolag='AIC')
		dfoutput = pd.Series(dftest[0:4], index=['Test Statistic','p-value',
					'#Lags Used','Number of Observations Used'])
		for key,value in dftest[4].items():
			dfoutput['Critical Value (%s)'%key] = value
		print(dfoutput)

	def first_diff(self):
		"""
		Obtains the first difference and performs Dickey-Fuller test for stationarity.
		"""
		print("\nFirst Difference:\n")
		self.df['first_diff'] = self.df.Crimes - self.df.Crimes.shift(1)
		self.stationarity(self.df.first_diff.dropna(inplace=False))

	def seasonal_first_diff(self):
		"""
		Obtains the first seasonal difference and performs Dickey-Fuller test for stationarity.
		"""
		print("\nSeasonal First Difference:\n")
		self.df['first_seasonal_diff'] = self.df.first_diff - self.df.first_diff.shift(12)
		self.stationarity(self.df.first_seasonal_diff.dropna(inplace=False))

	def fit(self):
		"""
		Run throught the different values ARIMA parameter values and fit the model
		to the training set.  Collect the error of how it performs on the validation
		set and then find the (p,d,q,P,D,Q) values that give the lowest
		error on the validation set. 

		Then forecast it into 2015 which is the test set, which it has NOT
		seen. Then get the error on this set.  
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
	
							result = self.mod.fit(disp=False)
				
		
							self.validation['Predicted'] = result.predict(	
															start=self._validation_begin,
                        			                        end=self._validation_end,
                                                			dynamic=True)


							self._errors.append( np.sqrt(sum(
                             					 (self.validation['Predicted']-\
                               					self.validation['Recorded'])**2)\
                               					/len(self.validation['Predicted'])))


							values = [p,1,q,P,1,Q]
	
							self._PDQ_vals.append(values)
						except:
							pass

		#####################################################################	
		# Now find the best model and find error on test set
		#####################################################################

		future = pd.DataFrame(index=self.test_date_list,
				      columns=self.training.columns)

		self.training = pd.concat([self.training, future])

		self._index = np.argmin(self._errors)
		
		self._p = self._PDQ_vals[self._index][0]
		self._d = self._PDQ_vals[self._index][1]
		self._q = self._PDQ_vals[self._index][2]
		self._P = self._PDQ_vals[self._index][3]
		self._D = self._PDQ_vals[self._index][4]
		self._Q = self._PDQ_vals[self._index][5]

		self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                              		order=(self._p,self._d,self._q),
                              		seasonal_order=(self._P,self._D,self._Q,12),
                            		enforce_invertibility=False,
                              		enforce_stationarity=False)


		self.results = self.mod.fit(disp=False)

		self.test['Predicted'] = self.results.predict(start = self._test_begin,
                                                	end = self._test_end, 
                                                  	dynamic= True)

		
		self.test_error =  np.sqrt(sum(
                              (self.test['Predicted']-\
                               self.test['Recorded'])**2)\
                               /len(self.test['Predicted']))

		self.params = [self._p, self._d, self._q, self._P, self._D, self._Q]

		#####################################################################	
		# Now train the model on the WHOLE data set
		#####################################################################
		
		self.training['Recorded'][self._test_begin:self._test_end] = self.test['Recorded']


	def forecast(self):
		""" 
		Forecasts the crime rates into 2016 and 2017.
		"""

		forecast = pd.DataFrame(index=self.forecast_date_list, 
					 columns=self.training.columns)

		self.training = pd.concat([self.training, forecast])

		self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                              		order=(self._p,self._d,self._q),
                              		seasonal_order=(self._P,self._D,self._Q,12),
                            		enforce_invertibility=True,
                              		enforce_stationarity=False)


		self.results = self.mod.fit(disp=False)

		self.forecast_results = self.results.predict(start = self._forecast_begin,
                                        		    end = self._forecast_end, 
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
		#plt.plot(self.forecast_results - self.test_error, 'r')
		#plt.plot(self.forecast_results + self.test_error, 'r')
		self.forecast_results.ix[-24:].plot(linewidth=2.5)
		plt.ylabel('Monthlt incidents')
		plt.xlabel('Year')  
        