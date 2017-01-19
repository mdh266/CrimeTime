#!/usr/bin/env/python
from collections import Counter

from datetime import datetime
from dateutil.relativedelta import relativedelta

import sqlite3
import pandas as pd

from geopy.geocoders import Nominatim
from geopy.distance import great_circle

import geopandas as gpd 
from shapely.geometry import Point

from shapely.geometry import Point, MultiPoint, MultiPolygon
from descartes import PolygonPatch
import matplotlib.pyplot as plt


from statsmodels.tsa.seasonal import seasonal_decompose
import sys
import os.path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
import warnings
warnings.filterwarnings('ignore')

class CrimeMapper(object):
	"""
	This is the main class for CrimeTime. It will deal with all the back end
	data management and interacting with the database.
	"""    
	geolocator = Nominatim()
    
	def __init__(self, production_mode):
		"""
		Constructor just makes a geopandas dataframe based off the police precincts.
		"""
		## Boolean to know to run in production mode, changes location of database
		self.production_mode = production_mode
	
		## Police precinct geopandas dataframe
		self.geo_df = None

		if self.production_mode == True:
			self.geo_df = gpd.read_file("./data/NYC_Police_Precincts.geojson")
		else:
			self.geo_df = gpd.read_file("../data/NYC_Police_Precincts.geojson")
		
		## boolean as to whether the precinct was found in the find_precinct call
		self.prec_found    = None

		## The location dictionary returned by geopy
		self.location      = None

		## Address of the location from geopy
		self.address       = None 

		## Precinct of the address
		self.prec	   = None
		
		## The name crime the user input
		self.crime_name    = None

		## Dataframe which contains all the crime data for precinct and type of crime
		self.crime_df	   = None

		## Dataframe monthly crime data
		self.ts		   = None

		## Dataframe that has all days in the week and the crimes occurring each day
		self.DAYS_OF_CRIME = None

		## Dataframe that has all the hours in the day and the crimes occurring each hour
		self.CRIME_HOURS   = None

		## sql_query to 
		self.sql_query	   = None

	def find_precinct(self, address):
		""" 
		Takes in address and finds the police precint the address belongs to.
		Returns a Boolean of whether the precinct of address is found.
		"""

		## Boolean of whether the precinct of address is found	
		self.prec_found = False
		## location of the address
		try:
			self.location = self.geolocator.geocode(address)
		except:
			pass
		
		if(self.location == None):
			return self.prec_found
		else:
			self.address = self.location.address
	
			# Get the longitude and latitude of the address
			point =  Point(self.location.longitude, self.location.latitude)

			# Central coordinates for NYC
			self.nyc_coor = [40.7128,-74.0059]

 			# Loop through all the NYC precincts geometries and
			# find which precinct the address is in.
			N = self.geo_df.shape[0]
			for i in range(0,N):
	 			if(point.within(self.geo_df.loc[i,'geometry'])):
 					self.prec = int(self.geo_df.loc[i,'precinct'])
					self.prec_found = True

			if self.production_mode:
				return self.prec_found


	def get_all_crime_data(self):
		"""
		Get all the crime data for this police precinct from excluding rape 
		and murder.
		"""
		self.sql_query = 'SELECT * FROM NYC_CRIME WHERE PRECINCT = '\
				+ str(self.prec) + ' AND OFFENSE != \'RAPE\''\
				+ 'AND OFFENSE != \'MURDER & NON-NEGL. MANSLAUGHTE\''

		if self.production_mode == True:
			conn = sqlite3.connect('./data/CrimeTime.db')
		else:
			conn = sqlite3.connect('../data/CrimeTime.db')

		# The crime dataframe for the selected police precint.
		df = pd.read_sql_query(self.sql_query, conn)
		conn.close()
		self.crime_df = df[df.OFFENSE == 'FELONY ASSAULT'] 
		self.make_timeseries()
		self.assault_ts = seasonal_decompose(self.ts,freq=12).trend
		self.crime_df = df[df.OFFENSE == 'ROBBERY'] 
		self.make_timeseries()
		self.robbery_ts  = seasonal_decompose(self.ts,freq=12).trend
		self.crime_df = df[df.OFFENSE == 'GRAND LARCENY'] 
		self.make_timeseries()
		self.larceny_ts  = seasonal_decompose(self.ts,freq=12).trend
		self.crime_df = df[df.OFFENSE == 'BURGLARY'] 
		self.make_timeseries()
		self.burglary_ts  = seasonal_decompose(self.ts,freq=12).trend
		self.crime_df = df[df.OFFENSE == 'GRAND LARCENY OF MOTOR VEHICLE'] 
		self.make_timeseries()
		self.car_ts  = seasonal_decompose(self.ts,freq=12).trend


	def get_crime_data(self, crime_name):
		"""
		Gets the crime data for this police precinct from the SQL Database
		"""
		self.crime_name = crime_name
		dont_continue = False

		if(crime_name == 'Larceny'):
			self.crime_name = 'GRAND LARCENY'
		elif(crime_name == 'Robbery'):
			self.crime_name = 'ROBBERY'
		elif(crime_name == 'Assault'):
			self.crime_name = 'FELONY ASSAULT'
		elif(crime_name == 'Burglary'):
			self.crime_name = 'BURGLARY'
		elif(crime_name == 'Car Theft'):
			self.crime_name = 'GRAND LARCENY OF MOTOR VEHICLE'
		else:
			dont_continue = True
			print "Cant Work With That Crime Type"

		if(dont_continue == False):
			self.sql_query = 'SELECT * FROM NYC_CRIME WHERE PRECINCT = '\
					+ str(self.prec) + ' AND OFFENSE = \'' \
					+ str(self.crime_name) + '\' ' 

			if self.production_mode == True:
				conn = sqlite3.connect('./data/CrimeTime.db')
			else:
				conn = sqlite3.connect('../data/CrimeTime.db')

			# The crime dataframe for the selected police precint.
			self.crime_df = pd.read_sql_query(self.sql_query, conn)
			conn.close()
        
	def restamp(self, row):
		"""
		Rewrite the date into an appropriate 
		formate for pandas time series.
		"""
		return datetime.strptime(row, '%m/%d/%Y %I:%M:%S %p').date()
    
	def make_time_series(self):
		""" 
		Turn the dataframe into a pandas series with daily events.
		"""
		aux = self.crime_df['DATE'].apply(self.restamp)
		temp = pd.Series(Counter(aux))
		## The pandas time series of the monthly number of specified crimes in precinct
		self.ts = temp.to_frame()
		self.ts.reset_index(inplace=True)
		self.ts.columns = ['Date','Crimes']
		self.ts['Date'] = pd.to_datetime(self.ts['Date'])
		self.ts = self.ts.set_index('Date')
		self.ts = self.ts.resample('M').sum()
		if(self.ts.isnull().values.any()):
			self.ts.dropna(inplace=True)           

	def percent_per_day(self):
		"""
		Makes a pandas time series for the number of crimes that occurred in 
		the selected precinct on each day of the week.
		"""
		CRIME_DAYS = 100 * (self.crime_df.groupby('WEEKDAY').size() 
                    /self.crime_df.groupby('WEEKDAY').size().sum())

		#print type(CRIME_DAYS)
    
		days = ['Monday','Tuesday','Wednesday',
						'Thursday','Friday','Saturday','Sunday']
    
		## Time series of the number of crimes that occurred in the day of week
		self.DAYS_OF_CRIME = pd.Series()
		for day in days:
			self.DAYS_OF_CRIME.loc[day] = CRIME_DAYS.loc[day]
    
        
	def percent_per_hour(self):
		""" 
		Makes a pandas time series for the number of crimes that occurred in 
		the selected precinct on hour of the day.
		"""
		self.crime_df['HOUR'] = self.crime_df['HOUR'].astype(int)
		self.CRIME_HOURS =  self.crime_df.groupby('HOUR').size() #\
		self.CRIME_HOURS = 100 * (self.CRIME_HOURS
                          /self.CRIME_HOURS.sum())

	def get_precinct(self):
		"""
		Returns the precinct of the address searched for.
		"""
		return str(self.prec)

	def get_address(self):
		"""
		Returns the address that was searched for.
		"""
		return str(self.address)

	def get_precinct_info(self):
		"""
		Returns the police precinct info for the selected precinct
		"""
		sql_query = 'SELECT * FROM NYC_Precint_Info WHERE Precinct = '\
				+ str(self.prec)

		if self.production_mode == True:		
			conn = sqlite3.connect('./data/CrimeTime.db')
		else:
			conn = sqlite3.connect('../data/CrimeTime.db')

		df = pd.read_sql_query(sql_query, conn)
		conn.close()
	
		precinct_info = {}

		precinct_info['name'] = str(df['Name'][0])
		precinct_info['address'] = str(df['Address'][0])
		precinct_info['tele'] = str(df['Telephone'][0])

		return precinct_info

	def plot_decompose(self):
		"""
		Plots the raw monthly number of crimes, as well as the trend and seasonality
		of crime in the precinct.
		"""
		fig = plt.figure(figsize=(9, 5))
		plt.clf()

		decomp_crime = seasonal_decompose(self.ts,freq=12)
		season_crime = decomp_crime.seasonal
		trend_crime   = decomp_crime.trend
		
		title = 'Decomposition Of Crimes Involving ' + self.crime_name +\
						' in Precinct ' + str(self.prec)

		plt.plot(self.ts, label='Monthly data', linewidth=3)
		plt.plot(season_crime, label='Seasonality', linewidth=3)
		plt.plot(trend_crime, label='Trend', linewidth=3)
		plt.title(title,fontsize=13)
		plt.xlabel('Year', fontsize=13)
		plt.legend()


	def plot_per_day(self):
		"""
		Makes a bar plot of percent of crimes which occur during each day in the week.
		"""
		plt.clf()
		self.percent_per_day()
		
		title = 'Percentage of ' +\
			self.crime_name +' in Precinct ' +\
			str(self.prec) + ' by day of week' 
        
		fig = plt.figure(figsize=(8, 5))
  	      
 		self.DAYS_OF_CRIME.plot(kind='bar')
      
		plt.title(title,fontsize=13)
		plt.yticks(size=14)
 		plt.xticks(rotation=30,size=14)
		plt.ylabel('Percent of crimes', fontsize=13)

	def plot_per_hour(self):
		"""
		Makes a bar plot of percent of crimes which occur during each day in the week.
		"""
		plt.clf()
		self.percent_per_hour()
		title = 'Percentage of ' + self.crime_name +\
			' in Precinct ' + str(self.prec) +\
			' by time of day' 

		fig = plt.figure(figsize=(8, 5))
		self.CRIME_HOURS.plot(kind='bar')
		plt.title(title,fontsize=13)
		plt.yticks(size=14)
		plt.xticks(rotation=45,size=16)
		plt.xlabel('Hour In Day', fontsize=13)
		plt.ylabel('Pecent of crimes', fontsize=13)
