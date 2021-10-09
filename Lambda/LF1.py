"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
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


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


# def get_slots(intent_request):
#     return intent_request['currentIntent']['slots']


# def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
#     return {
#         'sessionAttributes': session_attributes,
#         'dialogAction': {
#             'type': 'ElicitSlot',
#             'intentName': intent_name,
#             'slots': slots,
#             'slotToElicit': slot_to_elicit,
#             'message': message
#         }
#     }


def close(session_attributes, message):
    response = {
        'sessionState': session_attributes,
        'messages':[
            {
                'contentType': 'PlainText',
                'content': message
            }
        ]
    }

    return response

# def close(session_attributes, fulfillment_state, message):
#     response = {
#         'sessionState': session_attributes,
#         'messages': [{
#             'contentType':'PlainText',
#             'content': message
#         }]
#     }

#     response

# def delegate(session_attributes, slots):
#     return {
#         'sessionAttributes': session_attributes,
#         'dialogAction': {
#             'type': 'Delegate',
#             'slots': slots
#         }
#     }


# """ --- Helper Functions --- """


# def parse_int(n):
#     try:
#         return int(n)
#     except ValueError:
#         return float('nan')


# def build_validation_result(is_valid, violated_slot, message_content):
#     if message_content is None:
#         return {
#             "isValid": is_valid,
#             "violatedSlot": violated_slot,
#         }

#     return {
#         'isValid': is_valid,
#         'violatedSlot': violated_slot,
#         'message': {'contentType': 'PlainText', 'content': message_content}
#     }


# def isvalid_date(date):
#     try:
#         dateutil.parser.parse(date)
#         return True
#     except ValueError:
#         return False


# def validate_order_flowers(flower_type, date, pickup_time):
#     flower_types = ['lilies', 'roses', 'tulips']
#     if flower_type is not None and flower_type.lower() not in flower_types:
#         return build_validation_result(False,
#                                       'FlowerType',
#                                       'We do not have {}, would you like a different type of flower?  '
#                                       'Our most popular flowers are roses'.format(flower_type))

#     if date is not None:
#         if not isvalid_date(date):
#             return build_validation_result(False, 'PickupDate', 'I did not understand that, what date would you like to pick the flowers up?')
#         elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
#             return build_validation_result(False, 'PickupDate', 'You can pick up the flowers from tomorrow onwards.  What day would you like to pick them up?')

#     if pickup_time is not None:
#         if len(pickup_time) != 5:
#             # Not a valid time; use a prompt defined on the build-time model.
#             return build_validation_result(False, 'PickupTime', None)

#         hour, minute = pickup_time.split(':')
#         hour = parse_int(hour)
#         minute = parse_int(minute)
#         if math.isnan(hour) or math.isnan(minute):
#             # Not a valid time; use a prompt defined on the build-time model.
#             return build_validation_result(False, 'PickupTime', None)

#         if hour < 10 or hour > 16:
#             # Outside of business hours
#             return build_validation_result(False, 'PickupTime', 'Our business hours are from ten a m. to five p m. Can you specify a time during this range?')

#     return build_validation_result(True, None, None)


# """ --- Functions that control the bot's behavior --- """


def dining_suggestions(intent_request):
    """
    Performs dialog management and fulfillment for dining suggestions.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    flower_type = get_slots(intent_request)["FlowerType"]
    date = get_slots(intent_request)["PickupDate"]
    pickup_time = get_slots(intent_request)["PickupTime"]
    source = intent_request['invocationSource']

    if source == 'DiningSuggestionsIntent':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_order_flowers(flower_type, date, pickup_time)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        if flower_type is not None:
            output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model

        return delegate(output_session_attributes, get_slots(intent_request))

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thanks, your order for {} has been placed and will be ready for pickup by {} on {}'.format(flower_type, pickup_time, date)})


# """ --- Intents --- """


# def dispatch(intent_request):
#     """
#     Called when the user specifies an intent for this bot.
#     """

#     logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

#     intent_name = intent_request['currentIntent']['name']

#     # Dispatch to your bot's intent handlers
#     if intent_name == 'DiningSuggestionsIntent':
#         return dining_suggestions(intent_request)

#     raise Exception('Intent with name ' + intent_name + ' not supported')


# """ --- Main handler --- """


# def lambda_handler(event, context):
#     """
#     Route the incoming request based on intent.
#     The JSON body of the request is provided in the event slot.
#     """
#     # By default, treat the user request as coming from the America/New_York time zone.
#     os.environ['TZ'] = 'America/New_York'
#     time.tzset()
#     logger.debug('event.bot.name={}'.format(event['bot']['name']))

#     return dispatch(event)


def lambda_handler(event, context):
    # TODO implement
    logger.debug("inside dining suggestions code hook")
    logger.debug(event)
    sqs = boto3.client('sqs')

    queue_url = 'https://sqs.us-east-1.amazonaws.com/687819644709/DiningQueryQueue'

    # Send message to SQS queue
    slots = event['sessionState']['intent']['slots']
    body = {
        "cuisine": slots['Cuisine']['value']['interpretedValue'],
        "date": slots['Date']['value']['interpretedValue'],
        "time": slots['DiningTime']['value']['interpretedValue'],
        "location": slots['Location']['value']['interpretedValue'],
        "totalpeople": slots['PeopleNumber']['value']['interpretedValue'],
        "phone": slots['Phone']['value']['interpretedValue']
    }

    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={},
        MessageBody=json.dumps(body)
    )


    print(response)
    logger.debug('SQS sending success')

    # tmpstr = "Thanks, your suggestions for {} restaurants near {} has been sent to {}.".format(slots['Cuisine'], slots['Location'],slots['Phone'])


    sessionState = {
        "sessionAttributes":{

        },
        "dialogAction":{
            "type":"Close"
        },
        "intent":{
            "confirmationState": "None",
            "name": "DiningSuggestionsIntent",
            "state": "Fulfilled"
        },
        "state":"Fulfilled"
    }

    return close(sessionState,
                 'Thanks, your suggestions for {} restaurants near {} has been sent to {}.'.format(body['cuisine'], body['location'],body['phone']))


    # return close(event['sessionAttributes'],
    #              'Fulfilled',
    #              {'contentType': 'PlainText',
    #               'content': 'Thank you for the information, we are generating our recommendations, we will send the recommendations to your phone when they are generated'})
   