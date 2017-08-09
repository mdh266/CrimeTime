import numpy as np
import re
import pandas as pd
import sqlite3
from bs4 import BeautifulSoup
import urllib2

import sys
import os.path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

class PreProcessor:
	"""
	The PreProcessor class reates a SQLite database for crimes in New York City.  
	It will read in the data from the CSV file, clean it and store it to disk.
	It will also scrape the NYPD's Police Precinct website
	using `beautifulsoup <https://pypi.python.org/pypi/beautifulsoup4>`_ and get each 
	police precinct's name, address and telephone numeber, it will also stored this to disk
	in the same database.

	:attributes:
		**address** (str):
			The address and name of the csv crime database.
		
		**database_name** (str):
			The directory address and name of the to be created database.

	:methods:
	"""
    
	def __init__(self, database_name):
		"""
		Constructor will just create address and column names.
		"""
		## Column names for the database
		self.address = "./data/NYPD_7_Major_Felony_Incident_Map.csv"
		self.database_name = database_name

	def make_NYC_Crime_database(self, table_name):
		"""
		This function is does all the work to make the crime data base and cleans the data.

		:Parameters: table_name (str) :
			The table name of the database to be created.
		"""
		## The csv file of crime data downloaded from NYC Open Data
    
		crime_df = pd.read_csv(self.address,index_col=None)

		cols_to_drop = ['OBJECTID', 'Identifier', 
					    'CompStat Month', 'CompStat Day', 
					    'CompStat Year', 'Jurisdiction', 'Sector']

		crime_df.drop(cols_to_drop,1, inplace=True)
        
		# rename the columns
		crime_df.columns = ['DATE','WEEKDAY','MONTH', 'DAY', 'YEAR','HOUR',
                    		'OFFENSE', 'CLASSIFICATION', 'PRECINCT', 
                  		    'BOROUGH', 'LATITUDE', 'LONGITUDE', 'EXTRA']

		crime_df.dropna(inplace=True)

		# Convert precinct from float value to int value
		crime_df['PRECINCT'] = crime_df['PRECINCT'].astype(int)
		crime_df['YEAR'] = crime_df['YEAR'].astype(int)
        
		# Rewrite the points to get their latitudes and longitudes
		crime_points = crime_df['EXTRA']
		NUM_CRIMES = crime_points.shape[0]

		CRIME_LONGITUDE = np.ndarray(NUM_CRIMES)
		CRIME_LATITUDE = np.ndarray(NUM_CRIMES)

		index=0
		for row in crime_points.iteritems():
			coor = re.findall(r"[-+]?\d*\.\d+|\d+",row[1])
			CRIME_LONGITUDE[index] = coor[1]
			CRIME_LATITUDE[index] = coor[0]
			index = index + 1
       
		crime_df['LONGITUDE'] = CRIME_LONGITUDE
		crime_df['LATITUDE'] = CRIME_LATITUDE
    
		#DROP EXTRA COLUMNS
		crime_df.drop('CLASSIFICATION',1,inplace=True)
		crime_df.drop('EXTRA',1,inplace=True)
        
		crime_df = crime_df[crime_df.YEAR >= 2006]
        
		conn = sqlite3.connect(self.database_name)
		crime_df.to_sql(table_name, conn,flavor='sqlite',index=False)
		conn.close()

	def extract_precinct(self, string):
		"""
		For extracting the precinct number from the name of the precinct.
		Ex: input = 14th precinct, output = 14

		:parameters: string (str):
			The name of the precinct.

		:returns: The precinct number.

		:rtype: int
		"""
		return int(re.findall('(\d+).*',string)[0])

	def extract_string(self, string):
		"""
		Removes some bad characters from the beautiful soup unicode and then 
		returns the string.

		:parameters:
			string (str)

		:returns: The same string with any '\xa0` characters removed.
		:rtype: str
		"""
		return str(re.sub('\xa0','',string))

	def make_NYC_precinct_database(self):
		"""
		This function scrapes the NYC Police website and gathers info on 
		the police precincts using `beautifulsoup <https://pypi.python.org/pypi/beautifulsoup4>`_
		and stores them in the SQLite database.
		"""
		names = []
		numbers = []
		address = []
		precincts = []
		
		# begin to scrape the website below
		url = "http://www.nyc.gov/html/nypd/html/home/precincts.shtml"
		soup = BeautifulSoup(urllib2.urlopen(url).read(),"lxml")


		# manhattan, bronx, brooklyn, queens, staten island
		precincts_in_table = [0,2,4,6,8]
		# get the manhattan precinct info
		tables = soup.find_all(class_='bodytext')

		# loop through the tables and extract the precinct info
		for prec in precincts_in_table:
			for row in tables[prec].find_all('tr')[0:]:
				col = row.find_all('td')
				name = self.extract_string(col[0].find('a').get_text())
				# deal with the special cases that dont use their number
				if name == 'Midtown So. Pct.':
					name = '14th Precinct'
				if name == 'Central Park Pct.':
					name = '22nd Precinct'
				if name == 'Midtown No. Pct.':
					name = '18th Precinct'
	
				names.append(name)
				precincts.append(self.extract_precinct(name))
				numbers.append(self.extract_string(col[1].get_text()))
				address.append(self.extract_string(col[2].get_text()))

		# now make pandas dataframe form the data
		NYC_Police_Precinct_Info = pd.DataFrame(
                            {'Precinct':precincts,
                             'Name':names,
                             'Address':address,
                             'Telephone':numbers
                            })

		# push it to the sqlite database
		conn = sqlite3.connect(self.database_name)
		NYC_Police_Precinct_Info.to_sql("NYC_Precint_Info", conn, 
						flavor='sqlite',index=False)
		conn.close()
		
if __name__ == "__main__":
	PreProcess = PreProcessor("./data/CrimeTime.db")
	PreProcess.make_NYC_Crime_database("NYC_Crime")
	PreProcess.make_NYC_precinct_database()
	
