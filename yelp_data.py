###############################################################################
#                                                                             #
#  Hyde Park Yelp-reviewed restaurants                                        #
#  Data collection                                                            #
#  Coded by Scarlett Swerdlow                                                 #
#  scarlett.swerdlow@gmail.com                                                #
#  March 28, 2015                                                             #
#                                                                             #
###############################################################################

import argparse
import bs4
import csv
import json
import oauth2
import pprint
import requests
import sys
import urllib
import urllib2

YELP_API_HOST = 'api.yelp.com' 
YELP_SEARCH_PATH = '/v2/search/'
YELP_BUSINESS_PATH = '/v2/business/'
GOOGLE_PATH = 'https://maps.googleapis.com/maps/api/geocode/xml?'
FCC_PATH = 'http://data.fcc.gov/api/block/find?'

YELP_CONSUMER_KEY = 	# To be filled in by user
YELP_CONSUMER_SECRET = 	# To be filled in by user
YELP_TOKEN = 			# To be filled in by user
YELP_TOKEN_SECRET = 	# To be filled in by user
GOOGLE_KEY = 			# To be filled in by user
WSAPI_KEY = 			# To be filled in by user

# Constants
OUTPUT_TRACT = 0
CENTROID_TRACT = 2
BUSINESS_LIST = 3
OUTPUT_BUSINESS = 0
BUS_ID = 0
BUS_NAME = 1
BUS_CNT = 2
BUS_RATE = 3
BUS_ADDRESS = 4
BUS_CITY = 5
BUS_STATE = 6
FIRST_SOUP_RESULT = 0
TRACT_FIPS_STRING = 5:11
TWO_MILES_IN_METERS = 3219


def request(host, path, url_params=None):
    """
    Citation: Copied from Yelp
    Prepares OAuth authentication and sends the request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        urllib2.HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = 'http://{0}{1}?'.format(host, urllib.quote(path.encode('utf8')))

    consumer = oauth2.Consumer(YELP_CONSUMER_KEY, YELP_CONSUMER_SECRET)
    oauth_request = oauth2.Request(method="GET", url=url, 
    							   parameters=url_params)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_YELP_TOKEN': YELP_TOKEN,
            'oauth_YELP_CONSUMER_KEY': YELP_CONSUMER_KEY
        }
    )
    YELP_TOKEN = oauth2.YELP_TOKEN(YELP_TOKEN, YELP_TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, 
    						   YELP_TOKEN)
    signed_url = oauth_request.to_url()
    
    print u'Querying {0} ...'.format(url)

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response


def search_by_latlng(category_filter, ll, radius_filter, offset):
    """
    Citation: Modified from Yelp
    Query the Search API by a search term and location.
    Args:
        category_filter (str): The category of returns passed to the API.
        ll (str): The search latitude and longitude passed to the API.
        radius_filter (int): The search radius around ll passed to the API.
        offset (int): Offset the list of returned business results by this.
    Returns:
        dict: The JSON response from the request.
    """
    
    url_params = {
        'category_filter': category_filter.replace(' ', '+'),
        'll': ll,
        'radius_filter': radius_filter,
        'offset': offset
    }
    return request(YELP_API_HOST, YELP_SEARCH_PATH, url_params=url_params)


def get_business(business_id):
    """
    Citation: Copied from Yelp
    Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    YELP_BUSINESS_PATH = YELP_BUSINESS_PATH + business_id

    return request(YELP_API_HOST, YELP_BUSINESS_PATH)


def lookup_restaurants_by_centroids(centroid_filename, radius_filter, 
									output_filename):
    """
    Citation: Original
    Queries the API for restaurants around a given point
    Args:
        centroid_filename (str): CSV with Census tract centroid lat and lng.
        radius_filter (int): The search radius around ll passed to the API.
        output_filename (str): CSV to save results to.
    """
    # Create list of already queried centroids
    # Will fail without exception on first lookup run
    try:
        with open(output_filename, 'rU') as f1:
            data = csv.reader(f1, delimiter=',')
            queried_list = [row[OUTPUT_TRACT] for row in data]
        f1.close()
    except:
        queried_list = []

    # Create dictionary of not already queried centroids
    centroid_dict = {}
    with open(centroid_filename, 'rU') as f2:
        data = csv.reader(f2, delimiter=',')
        next(data)
        for row in data:
            if str(row[CENTROID_TRACT]) in queried_list:
                continue
            centroid_dict[int(row[CENTROID_TRACT])] = {'pop': int(row[POP]),
            										   'lat': float(row[LAT]), 
            										   'lng': float(row[LNG])}
    f2.close()

    # Look up restaurants for not already queried centroids
    # Save results as you go
    with open(output_filename, 'a') as f3:
        output_filename = csv.writer(f3, delimiter=',')
        for key in centroid_dict:
            pop = centroid_dict[key]['pop']
            lat = centroid_dict[key]['lat']
            lng = centroid_dict[key]['lng']
            ll = str(lat) + ',' + str(lng)
            results = search_by_latlng('restaurants', ll, radius_filter, 0)
            count = results['total']

            # Look up Yelp restaurant ids. Yelp limits business results
            # to 20 per query and 1000 total per business. Use offset 
            # parameter (j) to collect up to 1000.
            rests = []
            j = 0
            while (j <= count) & (j < 1000):
                br = search_by_latlng('restaurants', ll, radius_filter, j)
                for i in range(0, len(br['businesses'])):
                    rests.append(br['businesses'][i]['id'].encode("UTF-8"))
                j += 20

            # Save results to output file
            output_filename.writerow([key, pop, count, rests])


def lookup_business_by_id(input_filename, output_filename):
    """
    Citation: Original
    Queries Yelp Business API to collect information on Chicago restaurants
    Args:
        input_filename (str): CSV with list of restaurants within 
            certain radius of Census tract centroid.
        output_filename (str): CSV to save results to.
    """

    # Create list of already queried tract centroids
    # Will fail without exception on first lookup run
    try:
        with open(output_filename, 'rU') as f1:
            data = csv.reader(f1, delimiter=',')
            queried_list = [row[OUTPUT_TRACT] for row in data]
        f1.close()
    except:
        queried_list = []

    # Create businesses dictionary that maps business ID to empty dictionary
    businesses = {}
    with open(input_filename, 'rU') as f2:
        data = csv.reader(f2, delimiter=',')
        for row in data:
        	# Extract each business ID from string in CSV
            tract_businesses = row[BUSINESS_LIST].split(', ')
            for business in tract_businesses:
                cleaned_business = clean_business_string(business)
                if cleaned_business in queried_list:
                    continue
                businesses[cleaned_business] = {}
    f2.close()

    # Look up business ID via Yelp Business API for not already queried
    # businesses. Save results as you go
    with open(output_filename, 'a') as f3:
        output_filename = csv.writer(f3, delimiter=',')
        for key in businesses:
            try:
                results = get_business(key)
                name = results['name'].encode("UTF-8")
                review_count = results['review_count']
                # API only gives avg rating or one ind rating
                average_rating = results['rating'] 
                address = results['location']['address'][0].encode("UTF-8")
                city = results['location']['city'].encode("UTF-8")
                state = results['location']['state_code'].encode("UTF-8")
                postal_code = results['location']['postal_code']
                # Save business information to CSV
                output_filename.writerow([key, name, review_count, 
                						  average_rating, address, 
                						  city, state, postal_code])
            except:
                # Yelp Business API fails for some business IDs
                continue


def lookup_business_tract(input_filename, output_filename):
    """
    Citation: Original
    Queries Google and FFC APIs to get Census tract information
    Args:
        input_filename (str): CSV of restaurant names, addresses, and Yelp info.
        output_filename (str): CSV to save results to.
    """

    # Create list of already looked up businesses
    # Will fail without exception on first lookup run
    try:
        with open(output_filename, 'rU') as f1:
            data = csv.reader(f1, delimiter=',')
            looked_up_list = [row[OUTPUT_BUSINESS] for row in data]
    except:
        looked_up_list = []

    # Create businesses dictionary that maps business ID to business name, 
    # review info, and address
    businesses = {}
    with open(input_filename, 'rU') as f2:
        data = csv.reader(f2, delimiter=',')
        for row in data:
            if row[BUS_ID] in looked_up_list:
                continue
            businesses[row[BUS_ID]] = {'name': row[BUS_NAME],
            						   'review_count': int(row[BUS_CNT]),
            						   'average_rating': float(row[BUS_RATE]),
            						   'address': row[BUS_ADDRESS],
            						   'city': row[BUS_CITY],
            						   'state': row[BUS_STATE]}
    f2.close()

    # Look up tracts for not already queried businesses
    # Save results as you go
    with open(output_filename, 'a') as f3:
        output_filename = csv.writer(f3, delimiter=',')
        for key in businesses:
        	# Skip if business is not in Chicago
            if businesses[key]['city'] != 'Chicago':
                continue
            name = businesses[key]['name']
            review_count = businesses[key]['review_count']
            average_rating = businesses[key]['average_rating']
            address = businesses[key]['address']
            city = businesses[key]['city']
            state = businesses[key]['state']
            lat, lng = lookup_ll(address, city, state)
            tract = lookup_tract(lat, lng)
            output_filename.writerow([key, name, review_count, average_rating, 
            						  address, city, state, lat, lng, tract])


######################
#                    #
#  HELPER FUNCTIONS  #
#                    #
######################

def clean_business_string(business):
    """
    Citation: Original
    Helper function that cleans business string of unwanted punctuation
    Args:
        business (str): Business ID string to be cleaned.
    Returns:
        cleaned business ID string
    """
    rv = business.replace("[", "")
    rv = rv.replace("]", "")
    rv = rv.replace("'", "")
    return rv


def make_soup(url):
    """
    Citation: Original.
    Helper function that makes soup of given url.
    Args:
        url (str): Url to be turned into soup.
    Returns:
        Soup.
    """
    html = requests.get(url)
    if html == None:
        return None
    else:
        text = html.text.encode('iso-8859-1')
        soup = bs4.BeautifulSoup(text)
    return soup


def lookup_ll(address, city, state):
	"""
	Citation: Original.
	Helper function that looks up lat and lng for given address.
	Args:
		address (str): Address to be passed to API.
		city (str): City to be passed to API.
		state (str): State to be passed to API.
	Returns:
		lat (float) and lng (float).
	"""
    complete_address = address + ',' + city + ',' + state
    d = {'address': complete_address, 'key': GOOGLE_KEY}
    url = GOOGLE_PATH + urllib.urlencode(d)
    soup = make_soup(url)
    if soup.find_all("status")[FIRST_SOUP_RESULT].text == "ZERO_RESULTS":
        return None
    lat = float(soup.find_all("lat")[FIRST_SOUP_RESULT].text.encode("UTF-8"))
    lng = float(soup.find_all("lng")[FIRST_SOUP_RESULT].text.encode("UTF-8"))
    return lat, lng


def lookup_tract(lat, lng):
	"""
	Citation: Original.
	Helper function that looks up tract for given lat and lng.
	Args:
		lat (float): Lat to be passed to API.
		lng (float): Lng to be passed to API.
	Returns:
		tract (int).
	"""
    d = {'format': 'xml', 'latitude': lat, 'longitude': lng, 
    	 'showall': 'false'}
    url = FCC_PATH + urllib.urlencode(d)
    soup = make_soup(url)
    block_fips = soup.find_all("block")[FIRST_SOUP_RESULT].attrs['fips']
    # Tract is 6-digit string in middle of block FIPS
    tract = int(str(block_fips[TRACT_FIPS_STRING]))
    return tract

#############
#           #
#  EXECUTE  #
#           #
#############

def go():

	# Look up restaurants within 2 miles of each Census tract centroid
	lookup_restaurants_by_centroids('centroids.csv', TWO_MILES_IN_METERS, 
									'centroids_output2mile.csv')

	# Look up Yelp info for all restaurants within 2 miles of all Census tracts
	lookup_business_by_id('centroids_output2mile.csv', 
						  'ChicagoRestaurants.csv')

	# Look up tract info for all restaurants within 2 miles of all Census tracts
	lookup_business_tract('ChicagoRestaurants.csv', 
						  'ChicagoRestaurantsDetailed.csv')

