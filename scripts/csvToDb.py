import boto3
from boto3.dynamodb.conditions import Key,Attr

import datetime
import csv
from decimal import Decimal

with open('Restaurants.csv', newline='') as f:
    reader = csv.reader(f)
    restaurants = list(reader)

restaurants = restaurants[1:]
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurant-table')

for restaurant in restaurants:
    tableEntry = {
        'Timestamp': str(datetime.datetime.now()),
        'BID': restaurant[0],
        'Name': restaurant[1],
        'Address': restaurant[2],
        'Location': restaurant[3],
        'TotalReviews': int(restaurant[4]),
        'Rating': Decimal(restaurant[5]),
        'Zip_Code': restaurant[6],
        'Cuisine': restaurant[7]
    }
    print(tableEntry['Name'])
    response = table.put_item(Item=tableEntry)
    print(" Entry Inserted\n")

print("Data inserted to DynamoDB table yelp-restaurants")

# response = table.scan(FilterExpression=Attr('BID').eq('_2yFuoC12M9cfFxTbqCEzQ'))
# print(response['Items'])