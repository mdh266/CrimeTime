import json
import pymongo

def precinct_info(feature: dict) -> dict:
    precinct = {}
    # set the _id to the  precinct so we keep it unique
    precinct['_id']        = int(feature['properties']['precinct'])
    precinct['precinct']   = int(feature['properties']['precinct'])
    precinct['shape_area'] = float(feature['properties']['shape_area'])
    precinct['shape_leng'] = float(feature['properties']['shape_leng'])
    precinct['geometry']   = {}
    precinct['geometry']['coordinates']   = feature['geometry']['coordinates']
    precinct['geometry']['type']          = "MultiPolygon"
    
    return precinct


def main(path):
	"""
	"""

	# load the data
	with open("{}/NYC_Police_Precincts.geojson".format(path)) as f:
	    data = json.load(f)

	# connect to the mongo
	conn = pymongo.MongoClient('mongodb://localhost:27017')

	# connect to the twitter database
	db = conn.db_crimetime

	# create collection
	precinct_shapes = db.precinct_shapes

	# create the precinct info dictionaries
	precints = [precinct_info(feature) for feature in data['features']]

	# load them into the Mongo collection
	precinct_shapes.insert_many(precints)

if __name__ == "__main__":
	main("data")