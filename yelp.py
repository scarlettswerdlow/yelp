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

# Yelp credentials
YELP_API_HOST = 'api.yelp.com'
YELP_SEARCH_PATH = '/v2/search/'
YELP_BUSINESS_PATH = '/v2/business/'
YELP_CONSUMER_KEY = 'XvXnElUpR3YxGrrr3rl5Rg'
YELP_CONSUMER_SECRET = 'L9xJolklshy4y7w1NHlfSFTDPS0'
YELP_TOKEN = 'yh1JFbM7J3kzfUdRMdfq28HsbceLxCvq'
YELP_TOKEN_SECRET = 'g6GArPxWfAEzKTbOMyUhxyKqUZc'

# Google credentials
GOOGLE_PATH = 'https://maps.googleapis.com/maps/api/geocode/xml?'
GOOGLE_KEY = 'AIzaSyCJROPaxoCXvvMlvVP7PQ3Y3MdGk3NAhfM'
WSAPI_KEY = '97629a630dfa8afa6586d70999603c0a'

# FCC credentials
FCC_PATH = 'http://data.fcc.gov/api/block/find?'

NAME = 0
TRACT = 2
POP = 3
LAT = 4
LNG = 5


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
    oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_YELP_TOKEN': YELP_TOKEN,
            'oauth_YELP_CONSUMER_KEY': YELP_CONSUMER_KEY
        }
    )
    YELP_TOKEN = oauth2.YELP_TOKEN(YELP_TOKEN, YELP_TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, YELP_TOKEN)
    signed_url = oauth_request.to_url()
    
    print u'Querying {0} ...'.format(url)

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response


def search_by_location(category_filter, location, offset):
    """
    Citation: Modified from Yelp
    Query the Search API by a search term and location.
    Args:
        category_filter (str): The category of returns passed to the API.
        location (str): The location passed to the API.
        offset (int): Offset the list of returned business results by this amount.
    Returns:
        dict: The JSON response from the request.
    """
    
    url_params = {
        'category_filter': category_filter.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'offset': offset
    }
    return request(YELP_API_HOST, YELP_SEARCH_PATH, url_params=url_params)


def search_by_latlng(category_filter, ll, radius_filter, offset):
    """
    Citation: Modified from Yelp
    Query the Search API by a search term and location.
    Args:
        category_filter (str): The category of returns passed to the API.
        ll (str): The search latitude and longitude passed to the API.
        radius_filter (int): The search radius around ll passed to the API.
        offset (int): Offset the list of returned business results by this amount.
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


def make_location_dict(location):
    """
    Citation: original
    Queries the API for up to 1000 restaurants in a given location
    Returns:
        Dictionary that maps Yelp business ID to business name, rating, and number of reviews
    """
    rv = {}
    j = 0
    results = search_by_location('restaurants', location, j)
    print str(results['total']) + ' restaurants in ' + location
    while (j <= results['total']) & (j < 1000):
        results = search_by_location('restaurants', location, j)
        for i in range(0, len(results['businesses'])):
            rv[results['businesses'][i]['id']] = {'name': results['businesses'][i]['name'],
                                                  'rating': results['businesses'][i]['rating'],
                                                  'review_count': results['businesses'][i]['review_count']}
        j += 20
    return rv


def count_restaurants_by_neighborhood(neighborhood_filename, output_filename):
    """
    Citation: original
    Queries the API for the number of restaurants in Yelp-defined Chicago neighborhods.
    Args:
        neighborhood_filename (str): CSV with names of Yelo-defined Chicago neighborhoods.
        output_filename (str): CSV to save results to.
    """
    with open(neighborhood_filename, 'rU') as f:
        data = csv.reader(f, delimiter = ',')
        neighborhood_list = [rows[NAME].strip() for rows in data]

    rv = {}
    for neighborhood in neighborhood_list:
        location = neighborhood + ', Chicago, IL'
        results = search_by_location('restaurants', location, 0)
        count = results['total']
        print str(count) + ' restaurants in ' + neighborhood
        rv[neighborhood] = {'restaurant_count': count}

    with open(filename, 'wb') as f:
        filename = csv.writer(f, delimiter = ',')
        filename.writerows([[key, rv[key]['restaurant_count']] for key in rv])


def lookup_restaurants_by_centroids(centroid_filename, radius_filter, output_filename):
    """
    Citation: original
    Queries the API for restaurants around a given point
    Args:
        centroid_filename (str): CSV with Census tract centroid latitude and longitude.
        radius_filter (int): The search radius around ll passed to the API.
        output_filename (str): CSV to save results to.
    """
    # Create list of already queried tract centroids
    try:
        with open(output_filename, 'rU') as f1:
            data = csv.reader(f1, delimiter=',')
            queried_list = [row[0] for row in data]
        f1.close()
    except:
        queried_list = []

    # Create dictionary of not already queried centroids
    centroid_dict = {}
    with open(centroid_filename, 'rU') as f2:
        data = csv.reader(f2, delimiter=',')
        next(data)
        for row in data:
            if str(row[TRACT]) in queried_list:
                continue
            centroid_dict[int(row[TRACT])] = {'pop': int(row[POP]), 
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

            # Look up Yelp restaurant ids
            restaurants = []
            j = 0
            while (j <= count) & (j < 1000):
                business_results = search_by_latlng('restaurants', ll, radius_filter, j)
                # API limits business results to 20 per query
                for i in range(0, len(business_results['businesses'])):
                    restaurants.append(business_results['businesses'][i]['id'].encode("UTF-8"))
                j += 20

            # Save results to output file
            output_filename.writerow([key, pop, count, restaurants])


def clean_business_string(business):
    """
    Citation: original
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


def lookup_business_by_id(input_filename, output_filename):
    """
    Citation: original
    Queries Yelp Business API to collect information on Chicago restaurants
    Args:
        input_filename (str): CSV with list of restaurants within 
            certain radius of Census tract centroid.
        output_filename (str): CSV to save results to.
    """

    # Create list of already queried tract centroids
    try:
        with open(output_filename, 'rU') as f1:
            data = csv.reader(f1, delimiter=',')
            queried_list = [row[0] for row in data]
        f1.close()
    except:
        queried_list = []

    # Create businesses dictionary that maps business ID to empty dictionary
    businesses = {}
    with open(input_filename, 'rU') as f2:
        data = csv.reader(f2, delimiter=',')
        for row in data:
            tract_businesses = row[3].split(', ')
            for business in tract_businesses:
                cleaned_business = clean_business_string(business)
                if cleaned_business in queried_list:
                    continue
                businesses[cleaned_business] = {}
    f2.close()

    with open(output_filename, 'a') as f3:
        output_filename = csv.writer(f3, delimiter=',')
        for key in businesses:
            # Look up business ID via Yelp Business API
            try:
                results = get_business(key)
                name = results['name'].encode("UTF-8")
                review_count = results['review_count']
                average_rating = results['rating'] # API only gives avg rating or one ind rating
                address = results['location']['address'][0].encode("UTF-8")
                city = results['location']['city'].encode("UTF-8")
                state = results['location']['state_code'].encode("UTF-8")
                postal_code = results['location']['postal_code']
                # Save business information to CSV
                output_filename.writerow([key, name, review_count, average_rating, address, city, state, postal_code])
            except:
                # Yelp Business API fails for some business IDs
                continue


def make_soup(url):
    """
    Citation: original
    Helper function that makes soup of given url.
    Args:
        Url to be turned into soup.
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
    complete_address = address + ',' + city + ',' + state
    d = {'address': complete_address, 'key': GOOGLE_KEY}
    url = GOOGLE_PATH + urllib.urlencode(d)
    soup = make_soup(url)
    if soup.find_all("status")[0].text == "ZERO_RESULTS":
        return None
    lat = float(soup.find_all("lat")[0].text.encode("UTF-8"))
    lng = float(soup.find_all("lng")[0].text.encode("UTF-8"))
    return lat, lng


def lookup_tract(lat, lng):
    d = {'format': 'xml', 'latitude': lat, 'longitude': lng, 'showall': 'false'}
    url = FCC_PATH + urllib.urlencode(d)
    soup = make_soup(url)
    block_fips = soup.find_all("block")[0].attrs['fips']
    tract = int(str(block_fips[5:11]))
    return tract


def lookup_business_tract(input_filename, output_filename):

    # Create list of already looked up businesses
    try:
        with open(output_filename, 'rU') as f1:
            data = csv.reader(f1, delimiter=',')
            looked_up_list = [row[0] for row in data]
        print 'Created looked up business list'
    except:
        looked_up_list = []
        print 'No already looked up business list'

    # Create businesses dictionary that maps business ID to business name, review info, and address
    businesses = {}
    with open(input_filename, 'rU') as f2:
        data = csv.reader(f2, delimiter=',')
        for row in data:
            if row[0] in looked_up_list:
                continue
            businesses[row[0]] = {'name': row[1],
                                  'review_count': int(row[2]),
                                  'average_rating': float(row[3]),
                                  'address': row[4],
                                  'city': row[5],
                                  'state': row[6]}
    f2.close()

    with open(output_filename, 'a') as f3:
        output_filename = csv.writer(f3, delimiter=',')
        for key in businesses:
            print 'Looking up business ' + key
            # Look up business via Yelp Business API
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
            output_filename.writerow([key, name, review_count, average_rating, address, city, state, lat, lng, tract])
            print 'Saved information to csv'


lookup_business_tract('ChicagoRestaurants.csv', 'ChicagoRestaurantsDetailed.csv')

#print lookup_tract(41.799251, -87.583647)

#print lookup_ll('5307 S Hyde Park Blvd', 'Chicago', 'IL')

#lookup_business_by_id('centroids_output2mile.csv', 'ChicagoRestaurants.csv')
#lookup_restaurants_by_centroids('centroids.csv', 3219, 'output_detailed3.csv')

#chi_neighborhoods = create_list('ChicagoYelpNeighborhoods.csv')
#neighborhood_dict = lookup_businesses(chi_neighborhoods, 'Chicago, IL', 'ChicagoReviewedBusinessesByNeighborhood.csv')

#hyde_park_dict = make_comm_dict('Hyde Park, Chicago, IL')
#write_dict('HydeParkRestaurants.csv', hyde_park_dict)
#albany_park_dict = make_comm_dict('Albany Park, Chicago, IL')
#write_dict('AlbanyParkRestaurants.csv', albany_park_dict)

