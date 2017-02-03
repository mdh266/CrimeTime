import pytest
from datetime import datetime
import pickle
import pandas as pd


#################################################################
# Tests for CrimeMappper
#################################################################
from backend.CrimeMapper import CrimeMapper


def test_find_precinct():
	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("29 E. 109th St. Manhattan, NY")
	assert CM.prec == 23

def test_restamp():
	CM = CrimeMapper(production_mode = True)
	result = CM.restamp("01/09/2006 12:00:00 AM")
	assert result.isoformat() == '2006-01-09'

def test_get_precinct_info():
	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("29 E. 109th St. Manhattan, NY")
	precinct_info = CM.get_precinct_info()
	assert precinct_info['name'] == "23rd Precinct"
	assert precinct_info['address'] == "162 East 102nd Street"
	assert precinct_info['tele'] == "(212) 860-6411"

def test_get_address():
	rvalue = "29, East 109th Street, East Harlem, Manhattan, "
	rvalue += "New York County, NYC, New York, 10029, United States of America"
	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("29 E. 109th St. Manhattan, NY")
	assert rvalue == CM.get_address()

def test_get_crime_data():
	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("29 E. 109th St. Manhattan, NY")
	CM.get_crime_data("Assault")
	result_df = pickle.load(open("tests/assault_df.p", "rb"))
	test_dates = CM.crime_df['DATE']
	result_dates = result_df['DATE']

	# test same size
	assert result_dates.shape[0] == test_dates.shape[0]

	# now see if the dates are the same
	same_date = True
	for i in range(result_dates.shape[0]):
		if result_dates[i] != test_dates[i]:
			same_dates = False

	assert same_date


def test_make_time_series():
	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("29 E. 109th St. Manhattan, NY")
	CM.get_crime_data("Burglary")
	CM.make_time_series()
	result_ts = pickle.load(open("tests/burglary_ts.p", "rb"))
		
	# test same size
	assert result_ts.shape[0] == CM.ts.shape[0]

	# now see if the dates are the same
	same_numbers = True
	for i in range(result_ts.shape[0]):
		if result_ts['Crimes'][i] != CM.ts['Crimes'][i]:
			same_numbers = False

	assert same_numbers


def test_get_all_crime_data():
	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("45 W. 25th St. Manhattan, NY")
	CM.get_all_crime_data()
	result_ts = pickle.load(open("tests/all_crime_robbery_trend.p", "rb"))
		
	# test same size
	assert result_ts.shape[0] == CM.robbery_ts.shape[0]

	# now see if the dates are the same
	same_numbers = True
	for i in range(result_ts.shape[0]):
		if result_ts['Crimes'][i] != CM.robbery_ts['Crimes'][i]:
			same_numbers = False

	assert same_numbers


def test_percent_day():
	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("45 W. 25th St. Manhattan, NY")
	CM.get_crime_data("Larceny")
	CM.percent_per_day()
	result_ts = pickle.load(open("tests/Crimes_of_day.p", "rb"))
		
	# test same size
	assert result_ts.shape[0] == CM._DAYS_OF_CRIME.shape[0]

	# now see if the dates are the same
	same_numbers = True
	for i in range(result_ts.shape[0]):
		if result_ts[i] != CM._DAYS_OF_CRIME[i]:
			same_numbers = False

	assert same_numbers


def test_percent_hour():

	CM = CrimeMapper(production_mode = True)
	CM.find_precinct("45 W. 25th St. Manhattan, NY")
	CM.get_crime_data("Larceny")
	CM.percent_per_hour()
	result_ts = pickle.load(open("tests/Crimes_of_hour.p", "rb"))
		
	# test same size
	assert result_ts.shape[0] == CM._CRIME_HOURS.shape[0]

	# now see if the dates are the same
	same_numbers = True
	for i in range(result_ts.shape[0]):
		if result_ts[i] != CM._CRIME_HOURS[i]:
			same_numbers = False

	assert same_numbers