import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

SQS = boto3.client("sqs")


def sendToSQS(event):
    data = event.get('data')
    try:
        logger.debug("Recording %s", data)
        u = "https://sqs.us-east-1.amazonaws.com/687819644709/DiningQueryQueue"
        logging.debug("Got queue URL %s", u)
        slots = event['currentIntent']['slots']
        body = {
            "cuisine": slots['Cuisine'],
            "date": slots['Date'],
            "time": slots['DiningTime'],
            "location": slots['Location'],
            "totalpeople": slots['PeopleNumber'],
            "phone": slots['Phone']
        }
        resp = SQS.send_message(
            QueueUrl=u, 
            MessageBody=json.dumps(body),
            MessageAttributes={}
        )
        logger.debug("Send result: %s", resp)
    except Exception as e:
        raise Exception("Could not record link! %s" % e)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_dining_suggestion(location, cuisine, time, date, numberOfPeople, phoneNumber):
    locations = ['new york','chicago','miami','austin','seattle']
    if location is not None and location.lower() not in locations:
        return build_validation_result(False,
                                       'Location',
                                       'Currently we only have suggestions for Austin, Chicago, Miami, New York and Seattle locations, no suggestions available for restraunts in {}. Apologies for the inconvinience, would you like suggestions for a differenet location?  '.format(location))
                                       
    cuisines = ['chinese', 'indian', 'italian', 'japanese', 'american']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'Cuisine',
                                       'Curently we only have suggestions for American, Chinese, Indian, Italian and Japanese cuisines, no suggestions available for restraunts with {} cuisine. Apologies for the inconvinience, would you like suggestions for a differenet cuisine?  '.format(cuisine))
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand that, please enter date again.')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date',  'Recomendations cannot be made for past dates, please enter a valid date.')
            
    
    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        d = datetime.datetime.now()
        
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        if hour < 10 or hour > 24:
            # Outside of business hours
            return build_validation_result(False, 'DiningTime', 'Usual business hours for most restaurants are from 10 AM. to 11 PM. Can you please specify a time during this range?')
        logger.debug("location 1 here")    
        if parse_int(d.hour) > hour and d.day == datetime.datetime.strptime(date, '%Y-%m-%d').date().day:
            logger.debug("location 2 here")
            return build_validation_result(False,'DiningTime','Recomendations cannot be made for past times, please enter a valid time.')

    
    if numberOfPeople is not None:
        if not numberOfPeople.isnumeric():
            return build_validation_result(False,
                                      'PeopleNumber',
                                      'Oops! That does not look like a valid number {}, '
                                      'Please enter a valid number.'.format(numberOfPeople))
        numberOfPeople = int(numberOfPeople)
        if numberOfPeople > 20 or numberOfPeople <= 0:
            return build_validation_result(False,
                                           'PeopleNumber',
                                           'Number of people can only be between 0 and 20.')
    
    logger.debug("checking phone number")
    if phoneNumber is not None and not phoneNumber.isnumeric():
        return build_validation_result(False,
                                       'Phone',
                                       'Oops! That does not look like a valid number {}, '
                                       'Please enter a valid phone number. '.format(phoneNumber))
    
    if phoneNumber is not None and len(phoneNumber) is not 10:
        return build_validation_result(False,
                                       'Phone',
                                       'Oops! That does not look like a valid number {}, '
                                       'Please enter a valid phone number. '.format(phoneNumber))
    
    
                                          
    return build_validation_result(True, None, None)



def diningSuggestions(intent_request,context):
    
    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    date = get_slots(intent_request)["Date"]
    time = get_slots(intent_request)["DiningTime"]
    numberOfPeople = get_slots(intent_request)["PeopleNumber"]
    phoneNumber = get_slots(intent_request)["Phone"]
    source = intent_request['invocationSource']
    
    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestion(location, cuisine, time, date, numberOfPeople, phoneNumber)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

    
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    sendToSQS(intent_request)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thank you for your patience, You are all set! We will be sending recommendations to your phone number shortly.'})


def thankYou(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Glad to help you, Have a great day ahead :)'})


def dispatch(intent_request,context):
    intent_name = intent_request['currentIntent']['name']

    if intent_name == 'DiningSuggestionsIntent':
        return diningSuggestions(intent_request,context)
    elif intent_name == 'ThankYouIntent':
        return thankYou(intent_request)
    
    raise Exception('Intent with name ' + intent_name + ' not supported')



def lambda_handler(event, context):
    logger.debug("inside LF1")
    logger.debug(event)
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    
    return dispatch(event,context)