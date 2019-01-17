"""Open support tunnel on one of the nodes.  This takes about 5-10 seconds.

Note: Lambda function have default timeout of 3 seconds. Please make sure
to set the timeout to 30 seconds. This option is available in 'Basic settings'
section in AWS Lambda editor web page.
"""
import json
import math
import os
import ssl
import urllib2
import urllib

CLUSTER_IP = os.environ['CLUSTER_IP']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

''' Sample Utterances
Open support tunnel
Create support tunnel
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

ENDPOINT_NODE = 'https://{0}/api/internal/node'
ENDPOINT_TUNNEL = 'https://{0}/api/internal/node/{1}/support_tunnel'


def lambda_handler(event, context):
    del event
    del context

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Get node ID of one of the nodes in the cluster
    req = urllib2.Request(ENDPOINT_NODE.format(CLUSTER_IP), None)
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))
    print('REST API call response: %s' % resp)
    """ Sample response:
    {u'lastUpdateTime': u'2019-01-16T00:09:57.371Z',
     u'name': u'PhysicalCloudStorage', u'value': u'3482213220',
     u'frequencyInMin': 30}
    """
    first_node_id = resp['data'][0]['id']
    output = ''
    if resp['data'][0]['supportTunnel']['isTunnelEnabled']:
        # Tunnel is already open. Get tunnel port.
        output = 'Support tunnel is already open.'
        tunnel_port = resp['data'][0]['supportTunnel']['port']
        output += ' Tunnel port is %s' % tunnel_port
    else:
        # Open tunnel
        values = {'isTunnelEnabled': True, 'inactivityTimeoutInSeconds': 0}
        data = json.dumps(values).encode('utf8')
        print data
        req = urllib2.Request(
            ENDPOINT_TUNNEL.format(CLUSTER_IP, first_node_id), data)
        req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
        req.get_method = lambda: 'PATCH'
        handler = urllib2.HTTPSHandler(context=ssl_context)
        opener = urllib2.build_opener(handler)
        resp = json.load(opener.open(req))
        print('REST API call response: %s' % resp)
        """ Sample response:
        {u'isTunnelEnabled': True, u'enabledTime': u'2019-01-16T05:59:50.000Z',
         u'lastActivityTime': u'2019-01-15T05:43:16.000Z',
         u'port': 13600, u'inactivityTimeoutInSeconds': 0}
        """
        tunnel_port = resp['port']
        output = 'Support tunnel has been opened at %s' % tunnel_port

    LEX_RESULT['dialogAction']['message']['content'] = output
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
