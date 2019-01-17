"""Return cluster storage details."""
import json
import math
import os
import ssl
import urllib2

CLUSTER_IP = os.environ['CLUSTER_IP']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

''' Sample Utterances
What is the capacity of the cluster
How much space is available on the cluster
How much space is used on the cluster
Give me cluster storage details
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

ENDPOINT_SYSTEM_STORAGE = 'https://{0}/api/internal/stats/system_storage'

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

    req = urllib2.Request(ENDPOINT_SYSTEM_STORAGE.format(CLUSTER_IP), None)
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))
    print('REST API call response: %s' % resp)
    """ Sample response:
    {u'available': 1343263428608, u'used': 5166104576,
    u'lastUpdateTime': u'2019-01-12T16:14:43.514Z',
    u'miscellaneous': 1850674970, u'snapshot': 3315429606,
    u'liveMount': 0, u'total': 1348429533184}
    """
    total = human_readable_size(resp['total'])
    used = human_readable_size(resp['used'])
    available = human_readable_size(resp['available'])
    output = (
        'Your cluster has total storage space of %s.'
        ' %s is used and %s is available.' %
        (total, used, available)
    )

    LEX_RESULT['dialogAction']['message']['content'] = output
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
