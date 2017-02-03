# CrimeTime: Predicting crime rates in NYC


*To see the web application in action visit:* <a href="http://crimetime.online"> www.crimetime.online</a>

## Introduction 

This web application was part of a 3 week project at <a href="http://insightdatascience.com/">Insight Data Science</a>.
Users are prompted to enter an address from the input page seen below.
	

![Input Page](./Documentation/input.png)

And they get back a report on the historical trends of crimes in their neighborhood

	
![All Crime Info](./Documentation/Historical.png)

Users can look at the historical data of specific crimes in their neighborhood and get 
more specific on trends, seasonality, as well as which days and time most crimes happen like the results below:

	
![Specific Crime Info](./Documentation/Dashboard.png)

Users can also choose to forecast specific crime rates in their neighborhood into the future.


## How It works

This code was written in <a href="https://www.python.org/"> Python</a> and <a href="http://flask.pocoo.org/"> Flask</a>
and was deployed to <a href="https://aws.amazon.com/"> Amazon web services.</a> Users are prompted to enter an address and then I use the <a href="https://pypi.python.org/pypi/geopy">geopy</a> library to get
the latitude and longitude of the address.  Once that latitude and longitude are known I 
use the <a href="https://pypi.python.org/pypi/Shapely">shapely</a> library to find out which police 
precinct the address is in and obtain the data on that police precinct.

The info for police precincts was obtained by scraping the NYPD's 
<a href="http://www.nyc.gov/html/nypd/html/home/precincts.shtml"> website </a> using 
<a href="https://pypi.python.org/pypi/beautifulsoup4"> beautifulsoup</a> library and 
also this specific
 <a href="https://nycopendata.socrata.com/Public-Safety/Police-Precincts/78dh-3ptz/data">database</a> 
on the NYC Open Data Website. The historical crime data was obtained from the <a href="https://nycopendata.socrata.com/">NYC Open Data Website</a> 
and cleaning was completed using <a href="http://pandas.pydata.org/">Pandas</a> and
<a href="http://geopandas.org/">GeoPandas</a>. The data was then stored in a 
<a href="https://sqlite.org/">SQLite</a> database. Forecasted crime rates were predicted using a 
<a href="http://www.statsmodels.org/dev/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html">seasonal ARIMA</a>
model through the python library <a href="http://statsmodels.sourceforge.net/"> StatsModels</a>. 
I used a grid search to obtain the appropriate model paramaters that minimize the validation error.


## Dependencies

1. Python 2.7
2. SQLite
3. StatsModels (0.8.0rc1)
4. Pandas (0.19.1)
5. GeoPandas (0.2.1)
6. Geopy (1.11.0)
7. Shapely (1.5.17)
8. Flask (0.11.1)
9. Basemap (1.0.7)
10. Matplotlib (1.5.3)
11. Numpy (1.11.2)
12. Beautifulsoup4 (4.5.3)
13. Sphinx (only to build documentation)
14. pytest (only for testing)

## Running it on your own computer

To run this web application on your computer make sure you have obtained or built the SQLite
database and have all the dependencies installed on you computer.  Then run the 
command in the /CrimeTime/ directory:

	python run.py	

You should see something like:

	Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)	

Enter the address http://0.0.0.0:5000/ into your web browser to use the web application.


## Building the database

Download the file "NYPD_7_Major_Felony_Incident_Map.csv" from the NYC Open Data website, 
place it in the /CrimeTime/data/ directory. Then to build the database type
the command in the /CrimeTime/ directory,

	python ./backend/PreProcessor.py	


**NOTE: If NYC Open Data no longer has the file on their website, please email me and I will provide you with the database.**


## Testing

To test the code to make sure it works run the following command from the /CrimeTime /directory:

	py.test tests	


## Documentation





