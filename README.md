**CRIMETIME**

*Web application for visualizing and predict crime rates in New York City.*

*To see the web application in action visit: www.crimetime.online.*

The code was written in <a href="https://www.python.org/"> Python</a> 
using <a href="http://flask.pocoo.org/"> Flask</a>. 
and was deployed to <a href="https://aws.amazon.com/"> Amazon web services.</a>

The crime data was provided by <a href="https://nycopendata.socrata.com/"> NYC Open Data</a>. The info for police precincts was obtained through scraping the NYPD's 
<a href="http://www.nyc.gov/html/nypd/html/home/precincts.shtml"> website.</a> All data was cleaned and stored in a <a href="https://sqlite.org/">SQLite</a> database.

Forecasted crime rates were predicted using a seasonal ARIMA model through the python
library <a href="http://statsmodels.sourceforge.net/"> Statsmodels</a>.

**Dependenices**

1.) Python 2

2.) SQLite

3.) StatsModels (0.8.0rc1)

3.) Pandas (0.19.1)

4.) GeoPandas (0.2.1)

5.) Geopy (1.11.0)

6.) Shapely (1.5.17)

8.) Flask (0.11.1)

9.) Basemap (1.0.7)

10.) Matplotlib (1.5.3)

12.) Numpy (1.11.2)

13.) Beautifulsoup4 (4.5.3)

14.) Doxygen (only to build documentation)


**Installation**

Download the "NYPD_7_Major_Felony_Incident_Map.csv" from the NYC Open Data website, 
place it in the /data/ directory. Then in the CrimeTime directory run 

*python ./backend/PreProcessor.py*

to build the database.

**Usage**

Run the command in the CrimeTime directory:

*python run.py*

then you should see something like:

*Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)*

Go to the address, "http://0.0.0.0:5000/" in your webbrowser.

**Documentation**

To build the documentation, run the following command in the CrimeTime directory:

*doxygen doc/Doxfile*

a directory called html will be created open the file "index.html" in the html directory.




