import json
import boto3
import os
import logging
import datetime


import secrets

def make_token():
    """
    Creates a cryptographically-secure, URL-safe string
    """
    return secrets.token_urlsafe(16)


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    # TODO implement

    logger.debug('user chat event recieved = {event}'.format(event=event))

    client = boto3.client('lexv2-runtime')
    token = '45S45'
    lexResponse = client.recognize_text(
        botId='QZRYDTU9XP',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId=token,
        text = event['messages'][0]['unstructured']['text']
    )

    logger.debug("Lex response is generated")
    logger.debug('Lex response = {resp}'.format(resp=str(lexResponse)))

    txt = lexResponse['messages'][0]['content']

    val = {
        "messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": "test_session",
                    "text": txt,
                    "timestamp": str(datetime.datetime.now())
                }
            }
        ]
    }

    return val