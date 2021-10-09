from opensearchpy import OpenSearch, RequestsHttpConnection
import csv
import boto3
import requests
import logging
from requests_aws4auth import AWS4Auth
import json

host = 'search-restaurantsdomain-kiwcrdoojpsgfjf7enn46jrd3e.us-east-1.es.amazonaws.com'  # For example, my-test-domain.us-east-1.es.amazonaws.com
region = 'us-east-1'  # e.g. us-west-1

service = 'es'

search = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=('namk12','NamKap@14310'),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

with open('Restaurants.csv', newline='') as f:
    reader = csv.reader(f)
    restaurants = list(reader)

restaurants = restaurants[1:]

for restaurant in restaurants:
    index_data = {
        'id': restaurant[0],
        'address': restaurant[2],
        'cuisine': restaurant[7]
    }
    print(index_data)
    search.index(index="restaurantindex", doc_type="RestaurantIndex", id=restaurant[0], body=index_data, refresh=True)


print("and we are done")