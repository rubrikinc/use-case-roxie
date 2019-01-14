"""Return node count."""
import json
import ssl
import urllib2
import os

CLUSTER_IP = os.environ['cluster_ip']
AUTH_TOKEN = os.environ['auth_token']

''' Sample Utterances
What is the node count
How many nodes are in the cluster
What is the number of nodes in the cluster
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


def lambda_handler(event, context):
    del event
    del context

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    req = urllib2.Request(
        'https://%s/api/internal/cluster/me/node' % CLUSTER_IP, None)
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)

    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))
    print('REST API call response: %s' % resp)
    """ Sample response:
    {u'data':
        [{u'status': u'OK', u'ipAddress': u'172.31.33.0',
          u'id': u'VRECBDF3AF04B',
          u'supportTunnel': {u'isTunnelEnabled': True, u'enabledTime':
                             u'2019-01-09T08:39:42.000Z',
                             u'lastActivityTime': u'2019-01-09T21:14:06.000Z',
                             u'port': 13600,
                             u'inactivityTimeoutInSeconds': 345600},
          u'brikId': u'RUBRIK'}
        ],
        u'total': 1,
        u'hasMore': False
    }
    """

    node_count = len(resp['data'])
    if node_count == 1:
        output = 'Cluster has 1 node'
    else:
        output = 'Cluster has %s nodes' % node_count

    LEX_RESULT['dialogAction']['message']['content'] = output
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
