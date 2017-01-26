import pytest
import pickle
import pandas as pd

from backend.CrimeMapper import CrimeMapper
from backend.Forecasting import Seasonal_ARIMA

# test the initialization
def test_initialization():
	CT = CrimeMapper(True)
	CT.find_precinct("45 W. 25th St. Manhattan")
	CT.get_crime_data("Larceny")
	CT.make_time_series()
	model = Seasonal_ARIMA(CT)
	assert model.training_begin == 0
	assert model.training_end == 108
	assert model.validation_begin == 96
	assert model.validation_end == 108
	assert model.test_begin	== 108
	assert model.test_end == 120
	assert model.forecast_begin == 120
	assert model.forecast_end == 144
	

# test the training process
def test_fitting():
	CT = CrimeMapper(True)
	CT.find_precinct("45 W. 25th St. Manhattan")
	CT.get_crime_data("Larceny")
	CT.make_time_series()
	model = Seasonal_ARIMA(CT)
	model.fit()
	assert model.p == 1
	assert model.q == 1
	assert model.d == 1
	assert model.P == 0
	assert model.D == 1
	assert model.Q == 1


# test the forecasting
def test_forecasting():
	CT = CrimeMapper(True)
	CT.find_precinct("45 W. 25th St. Manhattan")
	CT.get_crime_data("Larceny")
	CT.make_time_series()
	model = Seasonal_ARIMA(CT)
	model.fit()
	test_results = pickle.load(open("tests/forecast_larceny.p", "rb"))
	model.forecast()

	# see if same size
	assert model.forecast_results.shape == test_results.shape
	
	# see if have same values
	same_numbers = True
	for i in range(test_results.shape[0]):
		if model.forecast_results[i] != test_results[i]:
			same_numbers = False

	assert same_numbers