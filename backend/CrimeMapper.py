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


from statsmodels.tsa.seasonal import seasonal_decompose
import sys
import os.path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

class CrimeMapper(object):
	"""
  This is the main class for CrimeTime. It will deal with all the back end
	data management and interacting with the database.
	"""    
	geolocator = Nominatim()
    
	def __init__(self):
		"""
		Constructor just makes a geopandas dataframe based off the police precincts.
		"""
		
		## Police precinct geopandas dataframe
		self.geo_df     = gpd.read_file("./data/NYC_Police_Precincts.geojson")
		#self.geo_df = gpd.read_file("../data/NYC_Police_Precincts.geojson")
	
		# other data members
		self.prec_found    = None
		self.location      = None
		self.address       = None 
		self.prec 			   = None
		self.crime_name    = None
		self.crime_df			 = None
		self.ts						 = None
		self.DAYS_OF_CRIME = None
		self.CRIME_HOURS   = None
		self.sql_query		 = None

	def find_precinct(self, address):
		""" 
		Takes in address and finds the police precint the address belongs to.
		Returns a Boolean of whether the precinct of address is found.
		"""

		## Boolean of whether the precinct of address is found	
		self.prec_found = False
		## location of the address
		self.location = self.geolocator.geocode(address)
		if(self.location == None):
			return self.prec_found
		else:
			## Address of the location 
			self.address = self.location.address
	
			# Get the longitude and latitude of the address
			point =  Point(self.location.longitude, self.location.latitude)

			## Central coordinates for NYC
			self.nyc_coor = [40.7128,-74.0059]

 			# Loop through all the NYC precincts geometries and
			# find which precinct the address is in.
			N = self.geo_df.shape[0]
			for i in range(0,N):
	 			if(point.within(self.geo_df.loc[i,'geometry'])):
					## Precinct of the address
 					self.prec = int(self.geo_df.loc[i,'precinct'])
					self.prec_found = True

			return self.prec_found



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

			#conn = sqlite3.connect('../data/CrimeTime.db')
			conn = sqlite3.connect('./data/CrimeTime.db')

			## The crime dataframe for the selected police precint.
			self.crime_df = pd.read_sql_query(self.sql_query, conn)
			conn.close()
        
	def restamp(self, row):
		"""
		Rewrite the date into an appropriate 
		formate for pandas time series.
		"""
		return datetime.strptime(row, '%m/%d/%Y %I:%M:%S %p').date()
    
	def make_timeseries(self):
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
