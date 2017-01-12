#!/usr/bin/env/python

from collections import Counter

from datetime import datetime
from dateutil.relativedelta import relativedelta

import matplotlib.pyplot as plt

import statsmodels.api as sm
import pandas as pd

import numpy as np

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
		"""
		
		training_start = datetime.strptime("2006-1-31","%Y-%m-%d")
		self.training_date_list = [training_start 
													+ relativedelta(months=x) for x in range(0,108)]

		validation_start = datetime.strptime("2014-1-31","%Y-%m-%d")
		self.validation_date_list = [validation_start 
													+ relativedelta(months=x) for x in range(0,12)]

		test_start = datetime.strptime("2015-1-31","%Y-%m-%d")
		self.test_date_list = [test_start 
													+ relativedelta(months=x) for x in range(0,12)]

			
		# errors in the model
		self.errors = []
		
		# PQD values for the mdoel
		self.PDQ_vals = []
	
		self.p = None
		self.q = None
		self.P = None
		self.Q = None
		
		self.test_error = None

		self.training_begin = 0
		self.training_end   = 108

		self.validation_begin = 96
		self.validation_end   = 108
		
		self.test_begin			= 108
		self.test_end				= 120


		# make the training set time series from CrimeMapper object
		self.training = pd.DataFrame(index=self.training_date_list,
																columns=['Recorded',
																				'Predicted'])

		self.training['Recorded'] = CT.ts[self.training_begin:self.training_end]


		# make the validation set time series from CrimeMapper object
		self.validation = pd.DataFrame(index=self.validation_date_list,
																columns=['Recorded',
																				'Predicted'])

		self.validation['Recorded'] = CT.ts[self.validation_begin:self.validation_end]

		# make the test set
		self.test = pd.DataFrame(index=self.test_date_list,
																columns=['Recorded',
																				'Predicted'])

		self.test['Recorded'] = CT.ts[self.test_begin:self.test_end]


	def fit(self):
		"""
		Run throught the different values ARIMA parameter values and fit the model
		to the training set.  Collect the error of how it performs on the validation
		set and then find the (p,d,q,P,D,Q) values that give the lowest
		error on the validation set. 

		Then forecast it into 2015 which is the test set, which it has NOT
		seen.  Then get the error on this set.  
		"""
		for P in range(0,2):
			for Q in range(0,2):

				self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                                  order=(1,1,0),
																	#trend='n',
                                  seasonal_order=(P,1,Q,12),
    	                            enforce_invertibility=True,
                                  enforce_stationarity=False)
				result = self.mod.fit()

				self.validation['Predicted'] = result.predict(
																								start=self.validation_begin,
                                                end=self.validation_end,
                                                dynamic=True)

				values = [1,1,0,P,1,Q]

				self.errors.append( np.sqrt(sum(
                            (self.validation['Predicted']-\
                            	self.validation['Recorded'])**2)\
                              /len(self.validation['Predicted'])))

				self.PDQ_vals.append(values)

		for P in range(0,2):
			for Q in range(0,2):

				self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                                  order=(0,1,1),
																	#trend='n',
                                  seasonal_order=(P,1,Q,12),
    	                            enforce_invertibility=True,
                                  enforce_stationarity=False)
				result = self.mod.fit()

				self.validation['Predicted'] = result.predict(
																								start=self.validation_begin,
                                                end=self.validation_end,
                                                dynamic=True)

				values = [0,1,1,P,1,Q]

				self.errors.append( np.sqrt(sum(
                            (self.validation['Predicted']-\
                            	self.validation['Recorded'])**2)\
                              /len(self.validation['Predicted'])))

				self.PDQ_vals.append(values)


		for p in range(1,3):
			for q in range(1,3):
				for P in range(0,2):
					for Q in range(0,2):
						self.mod = sm.tsa.SARIMAX(self.training['Recorded'], 
                                      order=(p,1,q),
																			#trend='n',
                                      seasonal_order=(P,1,Q,12),
                                      enforce_invertibility=True,
                                      enforce_stationarity=False)
	
						result = self.mod.fit()
				
		
						self.validation['Predicted'] = result.predict(
																								start=self.validation_begin,
                                                end=self.validation_end,
                                                dynamic=True)


						self.errors.append( np.sqrt(sum(
                              (self.validation['Predicted']-\
                               self.validation['Recorded'])**2)\
                               /len(self.validation['Predicted'])))


						values = [0,1,1,P,1,Q]
	
						self.PDQ_vals.append(values)

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
                            	enforce_invertibility=True,
                              enforce_stationarity=False)


		self.results = self.mod.fit()

		self.test['Predicted'] = self.results.predict(start = self.test_begin,
                                                	end = self.test_end, 
                                                  dynamic= True)



		self.test_error =  np.sqrt(sum(
                              (self.test['Predicted']-\
                               self.test['Recorded'])**2)\
                               /len(self.test['Predicted']))

		

	def plot_test(self):
		"""
		Plots the predicted and recorded crime values
		"""
		self.test[[
							'Recorded','Predicted']].ix[-12:].plot(figsize=(8,4),linewidth=3)   
        

        