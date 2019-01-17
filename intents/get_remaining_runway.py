"""Return storage runway remaining."""
import json
import os
import ssl
import urllib2

CLUSTER_IP = os.environ['CLUSTER_IP']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

''' Sample Utterances
How much runway is left
How much runway do I have left
What is the remaining runway on my cluster
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

ENDPOINT_RUNWAY = 'https://{0}/api/internal/stats/runway_remaining'


def human_readable_days(days):
    years = int(days / 365)
    months = int((days % 365) / 30)
    days = days - ((years * 365) + (months * 30))
    output = ''
    if years:
        if years == 1:
            output = '%s year' % years
        else:
            output = '%s years' % years
    if months:
        if output:
            output += ' and '
        output += '%s months' % months
    if days:
        if output:
            output += ' and '
        output += '%s days' % days
    return output


def lambda_handler(event, context):
    del event
    del context

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    req = urllib2.Request(ENDPOINT_RUNWAY.format(CLUSTER_IP), None)
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))
    print('REST API call response: %s' % resp)
    """ Sample response:
    {u'days': 1314}
    """
    output = (
        'Your cluster has storage runway of %s.'
        ' Consider increasing cluster size or reducing local retention period'
        ' to increase the runway left.' %
        human_readable_days(resp['days'])
    )

    LEX_RESULT['dialogAction']['message']['content'] = output
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
