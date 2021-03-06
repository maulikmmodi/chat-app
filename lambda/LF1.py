import json
import os
import math
import dateutil.parser
import datetime
import time
import logging
import boto3
from botocore.vendored import requests


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Helper Functions:

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

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
    
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
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


""" --- Functions that control the bot's behavior --- """

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

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# Action Functions

def greeting_intent(intent_request):
    
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText', 
                'content': 'Hi there, how can I help?'}
        }
    }

def thank_you_intent(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText', 
                'content': 'Glad I can help!!'}
        }
    }

def validate_dining_suggestion(location, cuisine, num_people, date, given_time, emailId):
    
    locations = ['brooklyn', 'new york', 'manhattan']
    if location is not None and location.lower() not in locations:
        return build_validation_result(False,
                                       'Location',
                                       'Please enter correct location')
                                       
    cuisines = ['indian', 'mexican', 'japanese','chinese', 'american']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'Cuisine',
                                       'Please enter correct Cuisine')
                                       
    if num_people is not None:
        num_people = int(num_people)
        if num_people > 50 or num_people < 0:
            return build_validation_result(False,
                                      'People',
                                      'Please add people betweek 0 to 50')
    
    
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand that, what date would you like to add?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date', 'You can search restaurant from today onwards. What day would you like to search?')

    if given_time is not None:
        if len(given_time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', None)

        hour, minute = given_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', 'Not a valid time')

        if hour < 10 or hour > 16:
            # Outside of business hours
            return build_validation_result(False, 'Time', 'Our business hours are from ten a m. to five p m. Can you specify a time during this range?')

    emailList = ['mm9817@nyu', 'maulik.modi@nyu.edu']
    if emailId is not None and emailId.lower() not in emailList:
        
        return build_validation_result(False,
                                      'Email',
                                      'Please add valid email for recommendation')
    
    return build_validation_result(True, None, None)

def dining_suggestion_intent(intent_request):
    
    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    num_people = get_slots(intent_request)["People"]
    date = get_slots(intent_request)["Date"]
    given_time = get_slots(intent_request)["Time"]
    emailId = get_slots(intent_request)["Email"]
    source = intent_request['invocationSource']
    
    
    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)
        
        validation_result = validate_dining_suggestion(location, cuisine, num_people, date, given_time, emailId)
        print (validation_result)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
                               
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        
        print ('here')
        print ('uncomment below to get the ')
        return delegate(output_session_attributes, get_slots(intent_request))
      
    # time to Unix time conversion for the yelp API  
    # req_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    # req_hour, req_minute = given_time.split(':')
    # req_hour = parse_int(req_hour)
    # req_minute = parse_int(req_minute)
    
    # dt = datetime.datetime(req_date.year, req_date.month, req_date.day, req_hour, req_minute)
    # dt_unix = time.mktime(dt.timetuple())
    # dt_unix = parse_int(dt_unix)
    
        
    # Add Yelp API endpoint to get the data
    requestData = {
                    "term":cuisine+", restaurants",
                    "location":location,
                    "categories":cuisine,
                    # "open_at": dt_unix,
                    "limit":"3",
                    "peoplenum": num_people,
                    "Date": date,
                    "Time": given_time,
                    "EmailId": emailId
                }
                
    print (requestData)
    
    # This is for the yelp API
    # resultData = restaurantApiCall(requestData)
    
    messageId = restaurantSQSRequest(requestData)
    print (messageId)

    return close(intent_request['sessionAttributes'],
             'Fulfilled',
             {'contentType': 'PlainText',
              'content': 'Got all the data, You will receive recommendation soon.'})


def restaurantSQSRequest(requestData):
    
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-west-2.amazonaws.com/844243140541/food-bot-queue'
    delaySeconds = 5
    messageAttributes = {
        'Term': {
            'DataType': 'String',
            'StringValue': requestData['term']
        },
        'Location': {
            'DataType': 'String',
            'StringValue': requestData['location']
        },
        'Categories': {
            'DataType': 'String',
            'StringValue': requestData['categories']
        },
        "DiningTime": {
            'DataType': "String",
            'StringValue': requestData['Time']
        },
        "DiningDate": {
            'DataType': "String",
            'StringValue': requestData['Date']
        },
        'PeopleNum': {
            'DataType': 'Number',
            'StringValue': requestData['peoplenum']
        },
        'EmailId': {
            'DataType': 'String',
            'StringValue': requestData['EmailId']
        }
    }
    messageBody=('Recommendation for the food')
    
    response = sqs.send_message(
        QueueUrl = queue_url,
        DelaySeconds = delaySeconds,
        MessageAttributes = messageAttributes,
        MessageBody = messageBody
        )
    
    print ('send data to queue')
    print(response['MessageId'])
    
    return response['MessageId']
    
    

def restaurantApiCall(requestData):
    
    url = "https://api.yelp.com/v3/businesses/search"
    
    querystring = requestData
    
    payload = ""
    headers = {
        'Authorization': "Bearer 7NjA90modOdaeEn6bLkfmOoy3YIibnWpCUki41GqXzW5z0nlxHPwRpjXeAJ1ycwHd0qeiipWT-9vtxH-WcSdM5zj9TcHhJrEzW6n_4tuQCS5YHUOnmvg_Ax4KYmKXHYx",
        'cache-control': "no-cache",
        'Postman-Token': "d1b24c2d-4f0d-4a67-b5fa-48f40f6fa447"
        }
    
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    message = json.loads(response.text)
    
    print(message['businesses'])
    
    if len(message['businesses']) <= 0:
        return 'We can not find any restaurant under this description, please try again.'
    
    textString = "Hello! Here are my " + requestData['categories'] + " restaurant suggestions for " + requestData['peoplenum'] +" people, for " + requestData['Date'] + " at " + requestData['Time'] + ". "
    count = 1
    for business in message['businesses']:
        textString = textString + " " + str(count) + "." + business['name'] + ", located at " + business['location']['address1'] + " "
        count += 1
    
    textString = textString + " Enjoy your meal!"
    return textString


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return greeting_intent(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return dining_suggestion_intent(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')
    

""" --- Main handler --- """

def lambda_handler(event, context):
    # TODO implement
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Hello from Lambda!')
    # }
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
