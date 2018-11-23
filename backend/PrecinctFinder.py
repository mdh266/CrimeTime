from geopy.geocoders import Nominatim

import geopandas as gpd 

from shapely.geometry import Point, MultiPolygon
from descartes import PolygonPatch

# import pymongo

class PrecinctFinder (object):
	""""
	This is class builds an object which uses `geopy <https://pypi.python.org/pypi/geopy/1.11.0>`_
	of the address, lattitude and longitude.  It then uses <a href="https://pypi.org/project/Shapely/>
	Shapely</a> to figure out what polic precinct the latitute and longitude belong to.

	:attributes:
	------------

		**geo_df** (`GeoPandas DataFrame <http://geopandas.org/data_structures.html#geodataframe>`_):
			The GeoPandas DataFrame of the geojson file, to plot the NYPD Precincts.

		**prec_found** (boolean):
			Boolean to record if the police precinct of the user entered address has been found.
		
		**location** (dict):
			Dictionary returned by `geopy <https://pypi.python.org/pypi/geopy/1.11.0>`_
			of the address, lattitude and longitude.

		**address** (str): 
			Address returned by `geopy <https://pypi.python.org/pypi/geopy/1.11.0>`_ .

		**prec** (int):
			Police precinct of the address.
	"""

	def __init__(self, production_mode : bool):
		
		## Geolocator object
		self._geolocator = Nominatim(user_agent="myapp")

		# Boolean to know to run in production mode, changes location of database
		self.production_mode = production_mode
	
		## boolean as to whether the precinct was found in the find_precinct call
		self.prec_found    = None

		## The location dictionary returned by geopy
		self.location      = None

		## Address of the location from geopy
		self.address       = None 

		## Precinct of the address
		self.prec		   = None

		## Police precinct geopandas dataframe
		self.geo_df       = None

		if self.production_mode == True:
			self.geo_df = gpd.read_file("./data/NYC_Police_Precincts.geojson")
		else:
			self.geo_df = gpd.read_file("../data/NYC_Police_Precincts.geojson")

		self.geo_df['precinct'] = self.geo_df['precinct'].astype(int)

	def find_precinct(self, address : str) -> bool:
		""" 
		Takes in address and finds the police precint the address belongs to.

		:Parameters: address (str): 
			The address contianing number, street and borough.

		:returns: 
			Boolean of whether the police precinct of address is found.

		:rtype: 
			Boolean.
		"""

		## Boolean of whether the precinct of address is found	
		self.prec_found = False
		## location of the address
		try:
			self.location = self._geolocator.geocode(address)
		except:
			pass
		
		if(self.location == None):
			return self.prec_found
		else:
			self.address = self.location.address
	
			# Get the longitude and latitude of the address
			point =  Point(self.location.longitude, self.location.latitude)

 			# Loop through all the NYC precincts geometries and
			# find which precinct the address is in.
			N = self.geo_df.shape[0]
			for i in range(0,N):
				if(point.within(self.geo_df.loc[i,'geometry'])):
					self.prec = int(self.geo_df.loc[i,'precinct'])
					self.prec_found = True

			if self.production_mode:
				return self.prec_found

	def get_precinct(self) -> int:
		"""
		Returns the precinct of the address that was searched for.
		
		:returns: prec
		:rtype: int
		"""
		return self.prec

	def get_address(self) -> str:
		"""
		Returns the address that was searched for.
		
		:returns: address
		:rtype: str
		"""
		return str(self.address)

	def get_precinct_shape(self) -> MultiPolygon:
		"""
		Returns the MuliPolygon for the precinct that was found.
		"""
		prec = None
		if self.prec_found:
			precinct              = self.get_precinct()
			prec_index            = self.geo_df[self.geo_df.precinct==precinct].index
			prec                  = self.geo_df['geometry'][prec_index[0]]

		return prec


	def find_precinct_w_mongo(self, address : str) -> bool:
		""" 
		Takes in address and finds the police precint the address belongs to using MongoDB

		:Parameters: address (str): 
			The address contianing number, street and borough.

		:returns: 
			Boolean of whether the police precinct of address is found.

		:rtype: 
			Boolean.
		"""

		## Boolean of whether the precinct of address is found	
		self.prec_found = False
		## location of the address
		try:
			self.location = self._geolocator.geocode(address)
		except:
			pass
		
		if(self.location == None):
			return self.prec_found
			
		else:
			self.address = self.location.address
	
			query = {"geometry": { 
				  "$geoIntersects": { 
				       "$geometry": { 
				        "type": "Point", 
				        "coordinates": [ self.location.longitude,
				        				 self.location.latitude]
				        			} 
				 				    } 
							} 
					} 

			projection = {"_id":0, "precinct":1}

			conn            = pymongo.MongoClient('mongodb://localhost:27017')
			db              = conn.db_crimetime
			precinct_shapes = db.precinct_shapes
			results         = precinct_shapes.find(query, projection)

			if results.count() > 0:

				self.prec_found = True
				precint_info    = results.next()
				self.prec       = precint_info['precinct']

		return self.prec_found


if __name__ == "__main__":
	loc_info = PrecinctFinder(False)
	loc_info.find_precinct("29 E. 109th St. Manhattan, NY")

	print(loc_info.get_address())
	print(loc_info.get_precinct())
