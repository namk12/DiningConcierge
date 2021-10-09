import boto3
import json
import requests
from requests_aws4auth import AWS4Auth

def getSQSMessage():
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/687819644709/DiningQueryQueue'

    # Send message to SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    print(f"Number of messages received: {len(response.get('Messages', []))}")

    for message in response.get("Messages", []):
        message_body = message["Body"]
        receipt_handle = message['ReceiptHandle']
        # print(f"Message body: {message_body}")
        # print(f"Receipt Handle: {receipt_handle}")
        #sqs.delete_message(QueueUrl=queue_url,ReceiptHandle=receipt_handle)

    print("SQS messages processed")

    return message_body


def lambda_handler(event, context):
    # TODO implement

    message = getSQSMessage()
    print("message = "+message)
    messageJSON = json.loads(message)

    #Fetch Data from message
    cuisine = messageJSON["cuisine"]
    date = messageJSON['date']
    time = messageJSON['time']
    location = messageJSON['location']
    totalpeople = messageJSON['totalpeople']
    phone = messageJSON['phone']

    ##Fetch ID for specific cuisines from ES##
    es_query = "https://search-restaurantsdomain-kiwcrdoojpsgfjf7enn46jrd3e.us-east-1.es.amazonaws.com/_search?q={cuisine}".format(
        cuisine=cuisine)
    esResponse = requests.get(es_query)
    data = json.loads(esResponse.content.decode('utf-8'))
    try:
        esData = data["hits"]["hits"]
    except KeyError:
        logger.debug("Error extracting hits from ES response")

    ids = []
    for data in esData:
        ids.append(data["_source"]["id"])

    print("naman === "+len(ids))

    ##Fetch Location and Name from DynamoDB ##

    return {}