#!/usr/bin/env python

"""
Return GeoJSON centroids for each postcode in Luxembourg

- Downloads the latest geojson from UDATA_ADDRESSES
- Average the position of all postcodes
- Spit out geojson

Run like :

python3 postcode-centroid.py > centroids.geojson

A sample centroids.geojson.xz (from 2016-07-11) is included.

There are 63 postcodes in Luxembourg that contain only one
address. Some of these are for residential addresses. You
might want to consider merging these points with the nearest
neighbour if you need to anonymise the output data of
your project.
"""

import requests
import geojson
from collections import defaultdict

# The API endpoint that contains the link to the most recent version of the
# addresses in all available formats (geojson, but also shp).
UDATA_ADDRESSES = 'https://data.public.lu/api/1/datasets/adresses-georeferencees-bd-adresses/'

# Eugh, magic numbers.
# This is just the uuid for the addresses in geojson format.
UDATA_ADDRESSES_ID = '7b58cf20-cbb0-4970-83f7-53a277f691b8'

# Initialise
postcodes = defaultdict(list)
postcodes_centroids = []

# Udata has no permalink. Parse the API to get the latest geojson.
udata_json = requests.get(UDATA_ADDRESSES).json()

# Find the resource with that ID in the udata json
# i.e. our addresses
for resource in udata_json['resources']:
    if resource['id'] == UDATA_ADDRESSES_ID:
        ADDRESSES_GEOJSON = resource['url']
        break
else:
    # Oops, the for loop didn't find anything!
    raise IOError("Could not find resource id {} in {}".format(
        UDATA_ADDRESSES_ID, UDATA_ADDRESSES
    ))

# Downloading the addresses might take ~15 seconds.
# In the meanwile, shake your wrists and correct your posture.
addresses = requests.get(ADDRESSES_GEOJSON).json()

# For all addresses, append coordinates to the list of coordinates
# of this postcode.
for address in addresses['features']:
    code_postal = address['properties']['code_postal']
    coordinates = address['geometry']['coordinates'][0]
    postcodes[code_postal].append(coordinates)

# For all postcodes, calculate the centroid

for postcode, points in postcodes.items():
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    try:
        count = len(points)
        # round to 6 decimals
        centroid = (
            round(sum(x) / count, 6),
            round(sum(y) / count, 6)
            )
    except ZeroDivisionError:
        pass
        # print("No address for postcode {}".format(postcode))

    postcodes_centroids.append(
        geojson.Feature(
            geometry=geojson.Point(centroid),
            properties={"postcode": postcode, "count": count}
        )
    )

# Dump the json features as a FeatureCollection
print(geojson.dumps(geojson.FeatureCollection(postcodes_centroids)))
