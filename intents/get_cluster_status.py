"""Return cluster status."""
import json
import os
import ssl
import urllib2

CLUSTER_IP = os.environ['CLUSTER_IP']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

''' Sample Utterances
Is cluster doing okay
What is the status of the cluster
Status of my cluster
How is my cluster doing
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

ENDPOINT_CLUSTER_STATUS = 'https://{0}/api/internal/cluster/me/node'


def lambda_handler(event, context):
    del event
    del context

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    req = urllib2.Request(ENDPOINT_CLUSTER_STATUS.format(CLUSTER_IP), None)
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
    ok_nodes_count = 0
    for node in resp['data']:
        if node['status'] == 'OK':
            ok_nodes_count += 1

    node_count = len(resp['data'])
    if ok_nodes_count == node_count:  # All nodes are doing fantastic
        output = 'Your cluster is doing awesome'
    else:
        output = (
            'I am sorry, not all nodes in the cluster are ok.'
            ' %s out of %s nodes are in trouble.' %
            ((node_count - ok_nodes_count), node_count)
        )

    LEX_RESULT['dialogAction']['message']['content'] = output
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
