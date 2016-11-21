#!/usr/bin/env/python

import numpy as np
import re
import pandas as pd
import sqlite3

import sys
import os.path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

class PreProcessor(object):
		"""
		Creates a SQLite database for crimes in New York City.  It will
		read in the data from the CSV file, clean it and store it to disk.
		"""
    
    def __init__(self):
			"""
			Constructor will just create address and column names.
			"""

			## The csv file of crime data downloaded from NYC Open Data
    	self.address = "./data/NYPD_7_Major_Felony_Incident_Map.csv"
    
			## Column names for the database
    	self.headers = ['DATE','WEEKDAY','MONTH', 'DAY', 'YEAR','HOUR',
                    'OFFENSE', 'CLASSIFICATION', 'PRECINCT', 
                     'BOROUGH', 'LATITUDE', 'LONGITUDE', 'EXTRA']

			
    def make_database(self, database_name):
				"""
				This function is does all the work.
				"""
        crime_df = pd.read_csv(self.address,index_col=None)
        #crime_new_df = pd.DataFrame.copy(crime_df)

        crime_df.drop('OBJECTID',1, inplace=True)
        crime_df.drop('Identifier',1, inplace=True)
        crime_df.drop('CompStat Month',1, inplace=True)
        crime_df.drop('CompStat Day',1, inplace=True)
        crime_df.drop('CompStat Year',1, inplace=True)
        crime_df.drop('Jurisdiction',1, inplace=True)
        crime_df.drop('Sector',1, inplace=True)
        
        # rename the columns
        crime_df.columns = self.headers

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
        
        conn = sqlite3.connect(database_name)
        crime_df.to_sql('Crime_Data', conn,flavor='sqlite',index=False)
        conn.close()
        
        self.data_base_name = database_name
        self.table_name = 'Crime_Data'



if __name__ == "__main__":
	PreProcess = PreProcessor()
	PreProcess.make_database("./data/CrimeTime.db")
