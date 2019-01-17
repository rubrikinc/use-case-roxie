"""Return rate of data growth."""
import json
import math
import os
import ssl
import urllib2

CLUSTER_IP = os.environ['CLUSTER_IP']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

''' Sample Utterances
How is my data growing
How fast is my data growing
What is the amount of data growth
Rate of data growth
What is the rate of my data growth
'''

LEX_RESULT = {
    'dialogAction': {
        'type': 'Close',
        'fulfillmentState': 'Fulfilled',
        'message': {
            'contentType': 'PlainText',
            # 'content': '%s' <--- This is filled in the end
        }
    }
}

TB = math.pow(10, 12)
GB = math.pow(10, 9)
MB = math.pow(10, 6)
PRECISION = 1

ENDPOINT_STORAGE_GROWTH = (
    'https://{0}/api/internal/stats/average_storage_growth_per_day'
)


def human_readable_size(bytes):
    tb = None
    gb = None
    mb = None
    tb = round(bytes / TB, PRECISION)
    if not tb:
        gb = round(bytes / GB, PRECISION)
    if not tb and not gb:
        mb = round(bytes / MB, PRECISION)

    output = None
    if tb:
        output = '%s Terabytes' % tb
    if gb:
        output = '%s Gigabytes' % gb
    if mb:
        output = '%s Megabytes' % mb
    if not output:
        output = '%s Bytes' % bytes

    return output


def lambda_handler(event, context):
    del event
    del context

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    req = urllib2.Request(ENDPOINT_STORAGE_GROWTH.format(CLUSTER_IP), None)
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))
    print('REST API call response: %s' % resp)
    """ Sample response:
    {u'bytes': 984544048}
    """
    if 'bytes' not in resp:
        output = (
            'I am sorry, rate of data growth is not available at this point')
    else:
        bytes = resp['bytes']
        output = 'Your rate of data growth is %s' % human_readable_size(bytes)

    LEX_RESULT['dialogAction']['message']['content'] = output
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
