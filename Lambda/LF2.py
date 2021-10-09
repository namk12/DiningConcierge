import boto3
import json
import requests
import logging
import random
from requests_aws4auth import AWS4Auth
from boto3.dynamodb.conditions import Key,Attr

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def getSQSMessage():
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/687819644709/DiningQueryQueue'

    # Send message to SQS queue
    sqsResponse = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )
    logger.debug('Message received')
    logger.debug('Number of messages received: {num}'.format(num=len(sqsResponse.get('Messages', []))))

    for message in sqsResponse.get("Messages", []):
        message_body = message["Body"]
        receipt_handle = message['ReceiptHandle']
        logger.debug("Message body: {message_body}")
        logger.debug("Receipt Handle: {receipt_handle}")
        sqs.delete_message(QueueUrl=queue_url,ReceiptHandle=receipt_handle)

    logger.debug("SQS messages processed")

    return message_body


def lambda_handler(event, context):
    # TODO implement

    message = getSQSMessage()
    logger.debug('SQS message received = {}'.format(message))
    messageJSON = json.loads(message)

    #Fetch Data from message
    cuisine = messageJSON['cuisine']
    date = messageJSON['date']
    time = messageJSON['time']
    location = messageJSON['location']
    totalpeople = messageJSON['totalpeople']
    phone = messageJSON['phone']
    phone = "+1"+phone

    ##Fetch ID for specific cuisines from ES##
    es_query = "https://search-restaurantsdomain-kiwcrdoojpsgfjf7enn46jrd3e.us-east-1.es.amazonaws.com/restaurantindex/_search"
    body ={
        "query": {
            "bool": {
                "must": [
                    { "match": { "address": location }}
                ],
                "filter": [
                    { "term":  { "cuisine": cuisine }}

                ]
            }
        }
    }
    x = json.dumps(body)

    esResponse = requests.post(es_query,auth=('namk12','NamKap@14310'),data=x,headers={'Content-Type':'application/json'})

    data = json.loads(esResponse.content.decode('utf-8'))
    print("printing data here")
    print(data)

    totalResponses = data["hits"]["total"]["value"]
    print(totalResponses)

    try:
        esData = data["hits"]["hits"]
    except KeyError:
        logger.debug("Error extracting hits from ES response")

    ids = []
    for data in esData:
        ids.append(data["_source"]["id"])

    message_body = 'Hello! Here are my suggestions for {cuisine} restaurants for {totalpeople} people, for {date} at {time}.\n'.format(
        cuisine=cuisine,
        totalpeople=totalpeople,
        date=date,
        time=time
    )

    ##Fetch Location and Name from DynamoDB ##
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurant-table')

    for i in range(min(5,len(ids))):
        dbQueryResponse = table.scan(FilterExpression=Attr('BID').eq(ids[i]))
        #dbQueryResponse = json.loads(dbQueryResponse)
        res = dbQueryResponse['Items'][0]
        temp = "{i}. {Name} at {Address} \n".format(
            i=i+1,
            Name=res['Name'],
            Address=res['Address']
        )
        message_body = message_body + temp

    logger.debug('message body to be sent = {message_body}'.format(message_body=message_body))

    sns = boto3.client('sns', region_name= 'us-east-1')
    response = sns.publish(
        PhoneNumber=phone,
        Message= message_body ,
        MessageStructure='string'
    )

    logger.debug(response)

    return {
        'statusCode': 200,
        'body': json.dumps("LF2 running succesfully")
    }