import httplib
import urllib
import json
import os
import distutils.util
import boto3
import csv
from datetime import datetime

# https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/alexa-skills-kit-interface-reference#outputspeech-object
# https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/speech-synthesis-markup-language-ssml-reference#say-as
# https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/understanding-the-structure-of-the-built-in-intent-library
# https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/ask-bp-sample-utterances
# https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model-handler-types.html

# https://realtime.livetv.net/Home/GetExtFlightInfo?TailNumber=N179JB&_=1498994944563
# {"ATN":"N179JB","ALT":"25030.875","SPD":"390","TRA":"UP","TER":"UP","FID":"N179JB_20170702010042","FNR":"JBU515","SDT":"","SAT":"","GID":"2","PVN":"","SPV":""}

raw_alexa_return = """
        {
          "version": "1.0",
          "response": {
            "outputSpeech": {
              "type": "PlainText",
              "text": "",
              "ssml": ""
            },
            "card": {
              "content": "",
              "title": "LiveConnect",
              "type": "Simple"
            },
            "reprompt": {
              "outputSpeech": {
                "type": "PlainText",
                "text": ""
              }
            },
            "shouldEndSession": true
          },
          "sessionAttributes": {}
        }

"""

def lambda_main(raw_event, context):
    """
        {
          "session": {
            "sessionId": "SessionId.6ab325dd-xxxx-xxxx-aee5-456cd330932a",
            "application": {
              "applicationId": "amzn1.echo-sdk-ams.app.bd304b90-xxxx-xxxx-86ae-1e4fd4772bab"
            },
            "attributes": {},
            "user": {
              "userId": "amzn1.ask.account.XXXXXX"
            },
            "new": true
          },
          "request": {
            "type": "IntentRequest",
            "requestId": "EdwRequestId.b851ed18-2ca8-xxxx-xxxx-cca3f2b521e4",
            "timestamp": "2016-07-05T15:27:34Z",
            "intent": {
              "name": "FlytNetSummary",
              "slots": {
                "Station": {
                  "name": "Station",
                  "value": "Balboa Park"
                }
              }
            },
            "locale": "en-US"
          },
          "version": "1.0"
        }

        inflight cloud

        Return Value
        ------------
        {
          "version": "1.0",
          "response": {
            "outputSpeech": {
              "type": "PlainText",
              "text": "Train departures from Balboa Park are as follows: Towards Daly 
        City on platform 1. In 3 minutes: 9 car train. In 9 minutes: 9 car train. In 
        11 minutes: 10 car train. Towards Dublin/Pleasanton on platform 2. In 13 
        minutes: 9 car train..."
            },
            "card": {
              "content": "Train departures from Balboa Park are as follows: Towards 
        Daly City on platform 1. In 3 minutes: 9 car train. In 9 minutes: 9 car train. 
        In 11 minutes: 10 car train. Towards Dublin/Pleasanton on platform 2. In 13 
        minutes: 9 car train...",
              "title": "BART Departures from Balboa Park",
              "type": "Simple"
            },
            "reprompt": {
              "outputSpeech": {
                "type": "PlainText",
                "text": ""
              }
            },
            "shouldEndSession": false
          },
          "sessionAttributes": {}
        }

    """
    print "lambda_main: Start"
    print raw_event

    #event = json.loads(raw_event)
    event = raw_event
    verbose = distutils.util.strtobool(get_envvar('AFAS_verbose', 'False'))
    useSsml = distutils.util.strtobool(get_envvar('AFAS_useSsml', 'False'))
    tmpfolder = get_envvar('AFAS_tmpfolder',  "/tmp/")
    reqtype = get_request_type(event)
    intent = get_intent(event)

    
    print 'Verbose: ' + str(verbose)
    print 'useSsml: ' + str(useSsml)
    print 'tmpfolder: ' + str(tmpfolder)
    print 'Request Type: ' + str(reqtype)
    print 'Intent: ' + str(intent)

    if reqtype == "LaunchRequest":
        response = json.loads(raw_alexa_return)
        response['response']['outputSpeech']['text'] = "Please ask about an airport. You can say 'what airport is KBOS'"
    elif (intent == None or intent not in  ["ResolveAirportCode"]):
        response = json.loads(raw_alexa_return)
        response['response']['outputSpeech']['text'] = "Unknown intent."
    else:
        
        load_airports(tmpfolder, verbose)

        if intent == "ResolveAirportCode":
            response = IntentResolveAirportCode(event, useSsml, verbose)

    if verbose:
        print response
    
    return response


def IntentResolveAirportCode(event, useSsml, verbose):
    """
        Handles the ResolveAirportCode intent.
    """
    
    # Basic Message
    rawText = "{0} is {1}, located in {2}, {3}."
    ssmlText = "<speak> <say-as interpret-as='characters'><prosody rate='x-slow'>{0}</prosody></say-as> is {1}, located in {2}, {3}.</speak>"
    if useSsml:
        msgFmt = ssmlText
    else:
        msgFmt = rawText

    slotA = get_slot_alphanum(event, "A")
    slotB = get_slot_alphanum(event, "B")
    slotC = get_slot_alphanum(event, "C")
    slotD = get_slot_alphanum(event, "D")

    slot = build_from_slots([slotA, slotB, slotC, slotD])
    print "Slots: " + slot
    slotAirport = None
    if slot in _airportDict:
        slotAirport = _airportDict[slot]

    if slotAirport is None:
        # Not found
        useSsml = True
        msg = "<speak>I am not familiar with the airport <say-as interpret-as='characters'><prosody rate='x-slow'>{0}</prosody></say-as></speak>".format(slot)
        cardText = "I am not familiar with the airport {0}.".format(slot)
        pass
    else:
        msg = msgFmt.format(slot, slotAirport[0], slotAirport[1], slotAirport[2])
        cardText = rawText.format(slot, slotAirport[0], slotAirport[1], slotAirport[2])

    response = json.loads(raw_alexa_return)
    response['response']['card']['content'] = cardText
    if useSsml:
        response['response']['outputSpeech']['type'] = "SSML"
        response['response']['outputSpeech']['ssml'] = msg
    else:
        response['response']['outputSpeech']['text'] = msg

    return response

def get_slot_alphanum(event, slotid):
    slotVal = None
    if slotid in event["request"]["intent"]["slots"]:
        if "value" in event["request"]["intent"]["slots"][slotid]:
            slotVal = event["request"]["intent"]["slots"][slotid]["value"]

    if slotVal != None:
        if slotVal.lower() == "dash":
            slotVal  = "-"
        else:    
            slotVal  = slotVal[0].upper()
    
    return slotVal

def build_from_slots(slots):

    name = ""
    for s in slots:
        if(s is not None):
            name += s

    return name

def get_intent(event):
    intent = None
    if "request" in event:
        if "intent" in event['request']:
            if "name" in event['request']['intent']:
                intent = event['request']['intent']['name']
    return intent

def get_request_type(event):
    reqtype = None
    if "request" in event:
        if "type" in event['request']:
          reqtype = event['request']['type']
    return reqtype

def get_envvar(name, default):
    val = os.environ.get(name)
    if(val is None):
        val = default

    return val


def HttpsGet(server, path, headers, verbose = True):
    # Request login path
    c = httplib.HTTPSConnection(server)
    c.request("GET", path, None, headers)
    response = c.getresponse()
    data = response.read()

    if verbose:
        print_response(response, data)

    result = dict()
    result["headers"] = response.getheaders()
    result["body"] = data
    result["Cookie"] = response.getheader("Set-Cookie")
    c.close()
    return result

def HttpPost(server, path, payload, headers, verbose = True):
       
    c = httplib.HTTPSConnection(server)
    c.request("POST", path, payload, headers)
    response = c.getresponse()
    data = response.read()

    if verbose:
        print_response(response, data)

    result = dict()
    result["headers"] = response.getheaders()
    result["body"] = data
    result["Cookie"] = response.getheader("Set-Cookie")
    c.close()
    return result

def print_response(response, data):
    print response.status, response.reason

    hdrs = response.getheaders()
    for h in hdrs:
        print h[0] + ": " + h[1]
    print ""
    
    print data

raw_json_event_rac = """{
          "session": {
            "sessionId": "SessionId.6ab325dd-xxxx-xxxx-aee5-456cd330932a",
            "application": {
              "applicationId": "amzn1.echo-sdk-ams.app.bd304b90-xxxx-xxxx-86ae-1e4fd4772bab"
            },
            "attributes": {},
            "user": {
              "userId": "amzn1.ask.account.XXXXXX"
            },
            "new": true
          },
          "request": {
            "type": "IntentRequest",
            "requestId": "EdwRequestId.b851ed18-2ca8-xxxx-xxxx-cca3f2b521e4",
            "timestamp": "2016-07-05T15:27:34Z",
            "intent": {
              "name": "ResolveAirportCode",
              "slots": {
                "A": {
                  "name": "A",
                  "value": "K"
                },
                "B": {
                  "name": "B",
                  "value": "B"
                },
                "C": {
                  "name": "C",
                  "value": "O"
                },
                "D": {
                  "name": "D",
                  "value": "S"
                }
              }
            },
            "locale": "en-US"
          },
          "version": "1.0"
        }"""        


def load_airports(tmpfolder, verbose = False):

    global _airportDict
    tmpfile =   tmpfolder + 'airports.csv'

    if(not os.path.isfile(tmpfile)):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket('lambda-alexaliveconnectskillpy')

        if verbose:
            for o in bucket.objects.all():
                print o

        # fetch from S3
        bucket.download_file('airports/airports.csv', tmpfile)

    # Load the airports
    with open(tmpfile, mode='r') as infile:
        reader = csv.reader(infile)
        _airportDict = dict((rows[5],(rows[1], rows[2], rows[3])) for rows in reader)

    if verbose:
        print _airportDict['KMLB']

# for testing purpose args defaulted to current folder & file. 
# returns True if file found
def file_exists(FOLDER_PATH='../', FILE_NAME=__file__):
    return os.path.isdir(FOLDER_PATH) \
        and os.path.isfile(os.path.join(FOLDER_PATH, FILE_NAME))    

def main():
    evt = json.loads(raw_json_event_rac)
    #evt = json.loads(raw_json_event)
    ctx = None

    #evt['request'] = dict()
    #evt['request']['intent'] = dict()
    #evt['request']['intent']['name'] = "FlytNetSummary"

    resp = lambda_main(evt, ctx)
    print resp
    

# This is the main of the program.
if __name__ == "__main__":
    main()
