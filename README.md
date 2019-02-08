# CrimeTime
---------------------

## Introduction 
---------------------

This web application was part of a 3 week project at <a href="http://insightdatascience.com/">Insight Data Science</a>.  I originally started this project because I was interested in developing a data driven approach to reducing crime in the NYC area.  Working on this project I quickly noticed that different neighborhoods are affected by different types of crime and these crimes peak at different times of the year (you can see this <a href="http://michael-harmon.com/blog/crimetime.html">blog post</a> to read more).  I thought if I could make a web application that forecasts monthly crime rates on a local level it might help police redistribute their resources more effectively and thus reduce the crime in NYC.  The applicaiton could also be of interest to individuals or business who are concerned about crime rates in their neighborhood.  

The application prompts to enter an address from the input page seen below:
	

![Input Page](./doc/input.png)


And they get back a report on the historical trends of crimes in their neighborhood:

	
![All Crime Info](./doc/Historical.png)

Users can select specific crimes in their neighborhood and get the historical trend, seasonality, as well as which days and times most of these crimes happen.  The results for assault are shown below:

	
![Specific Crime Info](./doc/Dashboard.png)

Users can also choose to forecast specific crime rates into the future.


## How It works
---------------------

**The source code can be found <a href="https://github.com/mdh266/CrimeTime">here</a>.**


This code was written using <a href="https://www.python.org/"> Python</a> and <a href="http://flask.pocoo.org/"> Flask</a>
and deployed to <a href="https://aws.amazon.com/"> Amazon web services.</a> Users are prompted to enter an address and then I use the <a href="https://pypi.python.org/pypi/geopy">geopy</a> library to get
the latitude and longitude of the address.  Once that latitude and longitude are known I 
use the <a href="https://pypi.python.org/pypi/Shapely">shapely</a> library to find out which police 
precinct the address is in and obtain the data on that police precinct.

The info for police precincts was obtained by scraping the NYPD's 
<a href="http://www.nyc.gov/html/nypd/html/home/precincts.shtml"> website </a> using the
<a href="https://pypi.python.org/pypi/beautifulsoup4"> beautifulsoup</a> library and 
also this specific
 <a href="https://nycopendata.socrata.com/Public-Safety/Police-Precincts/78dh-3ptz/data">database</a>. The historical crime data was obtained from the <a href="https://nycopendata.socrata.com/">NYC Open Data Website</a> 
and cleaning was completed using <a href="http://pandas.pydata.org/">Pandas</a> and
<a href="http://geopandas.org/">GeoPandas</a>. The data was then stored in a 
<a href="https://sqlite.org/">SQLite</a> database. Forecasted crime rates were predicted using a 
<a href="http://www.statsmodels.org/dev/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html">seasonal ARIMA</a>
model through the Python library <a href="http://statsmodels.sourceforge.net/"> StatsModels</a>. 
I used a grid search to obtain the appropriate model paramaters with the selection criteria that the choice of parameters must minimize the validation error.


## Running it on your own computer
---------------------

To run this web application on your computer, please email me to obtain the SQLite
database and install all the necessary dependencies on you computer.  You can install all the depencies using <a href="https://www.docker.com/">Docker</a> by running the following commands from the <code>CrimeTime/</code> directory:

	docker build -t crimetime . 

You can then run the application with the command,

	docker run -id p 5000:5000 crimetime

Then enter the address http://0.0.0.0:5000/ into your web browser to use the web application.

Alternatively you can use the  <a href="https://www.continuum.io/anaconda-overview">Anaconda</a> distribution and create an virtual environment using the <code>environment.yml</code> file as described <a href="https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file">here</a>.  And then run the following command from the <code>CrimeTime/</code> directory:

	python tornadoapp.py

and go to the address http://0.0.0.0:5000/ in your web browser.



## Building the database
---------------------

To build the database on your local machine first download the file "NYPD_7_Major_Felony_Incident_Map.csv" from the NYC Open Data website and
place it in the <code>CrimeTime/data/</code> directory. Then making sure you have all the necessary dependencies installed on your computer (see above) and type the folowing command into your terminal from the <code>CrimeTime/</code> directory,

	python ./backend/PreProcessor.py	


**NOTE: If NYC Open Data no longer has the file on their website, please email me and I will provide you with the database.**


## Testing
---------------------

To test the code to make sure it works run the following command in your terminal shell from the <code>/CrimeTime/</code>directory:

	py.test tests	

You will then see a report on the testing results.

## Documentation
---------------------

To build the documentation for this code type the following command in terminal from <code>/CrimeTime/</code> directory:

	sphinx-apidoc -F -o doc/ backend/
Then cd into the <code>doc/</code> directory and type,

	make html

The html documentation will be in the directory <code>_build/html/</code>.  Open the file <code>index.html</code> in that directory.


