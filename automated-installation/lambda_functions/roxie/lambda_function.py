import requests
import json
import os
import ssl
import math
from urllib3.exceptions import InsecureRequestWarning

CLUSTER_IP = os.environ['RBK_CLUSTER_IP']
AUTH_TOKEN = os.environ['RBK_AUTH_TOKEN']


''' Sample Utterances
Is cluster doing okay
What is the status of the cluster
Status of my cluster
How is my cluster doing
'''

LEX_RESULT = {
    "sessionState": {
        "dialogAction": {
            "type": "Close"
        },
        "intent": {
            "state": "Fulfilled",
            # "name": "intent_name" <---- filled inside functions
        }
    },
    "messages": [
        {
            "contentType": "PlainText",
            # "content": "content" <---- filled inside functions
        }
    ]
}
"""
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
"""


ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
headers = {'Authorization': 'Bearer ' + AUTH_TOKEN}




def get_cluster_status(intent_request):
    ENDPOINT_CLUSTER_STATUS = 'https://{0}/api/internal/cluster/me/node'
    resp = requests.get(ENDPOINT_CLUSTER_STATUS.format(CLUSTER_IP),headers=headers,verify=False)
    
    ok_nodes_count = 0
 
    for node in resp.json()['data']:
        if node['status'] == 'OK':
            ok_nodes_count += 1

    node_count = len(resp.json()['data'])
    if ok_nodes_count == node_count:  # All nodes are doing fantastic
        output = 'Your cluster is doing awesome'
    else:
       output = (
            'I am sorry, not all nodes in the cluster are ok.'
            ' %s out of %s nodes are in trouble.' %
            ((node_count - ok_nodes_count), node_count)
        )

    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

def human_readable_size(bytes):
    tb = None
    gb = None
    mb = None
    TB = math.pow(10,12)
    GB = math.pow(10,9)
    MB = math.pow(10,6)
    PRECISION=1
    
    bytes = int(bytes)
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

def get_archived_amount(intent_request):


    ENDPOINT_ARCHIVAL_STORAGE = 'https://{0}/api/internal/stats/cloud_storage/physical'

    resp = requests.get(ENDPOINT_ARCHIVAL_STORAGE.format(CLUSTER_IP),headers=headers,verify=False)  
    resp = resp.json()
    
    if 'value' not in resp:
        output = 'I am sorry, amount of data archived is not available'
    else:
        output = 'Archived amount is %s' % human_readable_size(resp['value'])
    
    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

def get_cluster_storage_details(intent_request):
    ENDPOINT_SYSTEM_STORAGE = 'https://{0}/api/internal/stats/system_storage'
    resp = requests.get(ENDPOINT_SYSTEM_STORAGE.format(CLUSTER_IP),headers=headers,verify=False)  
    resp = resp.json()

    total = human_readable_size(resp['total'])
    used = human_readable_size(resp['used'])
    available = human_readable_size(resp['available'])
    output = (
        'Your cluster has total storage space of %s.'
        ' %s is used and %s is available.' %
        (total, used, available)
    )
    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

def get_data_growth_rate(intent_request):
    ENDPOINT_STORAGE_GROWTH = 'https://{0}/api/internal/stats/average_storage_growth_per_day'
    resp = requests.get(ENDPOINT_STORAGE_GROWTH.format(CLUSTER_IP),headers=headers,verify=False)  
    resp = resp.json()

    if 'bytes' not in resp:
        output = (
            'I am sorry, rate of data growth is not available at this point')
    else:
        bytes = resp['bytes']
        output = 'Your rate of data growth is %s' % human_readable_size(bytes)    
    
    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

def get_node_count(intent_request):
    ENDPOINT_CLUSTER_STATUS = 'https://{0}/api/internal/cluster/me/node'
    resp = requests.get(ENDPOINT_CLUSTER_STATUS.format(CLUSTER_IP),headers=headers,verify=False)  
    resp = resp.json()

    node_count = len(resp['data'])
    if node_count == 1:
        output = 'Cluster has 1 node'
    else:
        output = 'Cluster has %s nodes' % node_count 

    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT   

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

def get_remaining_runway(intent_request):
    ENDPOINT_RUNWAY = 'https://{0}/api/internal/stats/runway_remaining'

    resp = requests.get(ENDPOINT_RUNWAY.format(CLUSTER_IP),headers=headers,verify=False)  
    resp = resp.json()

    output = (
        'Your cluster has storage runway of %s.'
        ' Consider increasing cluster size or reducing local retention period'
        ' to increase the runway left.' %
        human_readable_days(resp['days'])
    )   
    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT   

def get_sla_compliance(intent_request):
    ENDPOINT_SLA_COMP_SUMMARY = 'https://{0}/api/internal/report?report_template=SlaComplianceSummary'
    ENDPOINT_SLA_COMP_CHART = 'https://{0}/api/internal/report/{1}/chart'

    resp = requests.get(ENDPOINT_SLA_COMP_SUMMARY.format(CLUSTER_IP),headers=headers,verify=False)  
    resp = resp.json()

    # Extract report ID
    report_id = resp['data'][0]['id']
    
    resp = requests.get(ENDPOINT_SLA_COMP_CHART.format(CLUSTER_IP,report_id),headers=headers,verify=False)  
    resp = resp.json()

    # Pick the compliance summary from 'measure' type 'ObjectCount' (See
    # sample response above).
    def get_sla_counts(resp):
        num_slas = 0
        in_compliance_count = 0
        non_compliance_count = 0
        for report in resp:
            if report['measure'] == 'ObjectCount':
                for data_column in report['dataColumns']:
                    data_point = data_column['dataPoints'][0]
                    num_slas += data_point['value']
                    if data_column['label'] == 'InCompliance':
                        in_compliance_count += data_point['value']
                    else:
                        non_compliance_count += data_point['value']
        return (
            int(num_slas), int(in_compliance_count), int(non_compliance_count))

    def get_non_compliance_slas(resp):
        """Return noncompliance SLAs along with the number of objects that
           are out of compliance.
        """
        non_compliance_slas = {}
        for report in resp:
            if report['measure'] != 'StackedComplianceCountByStatus':
                continue
            for data_column in report['dataColumns']:
                for data_point in data_column['dataPoints']:
                    if data_point['measure'] != 'NonComplianceCount':
                        continue
                    non_compliance_count = data_point['value']
                    if non_compliance_count:
                        sla_name = data_column['label']
                        non_compliance_slas[sla_name] = (
                            int(non_compliance_count)
                        )
        return non_compliance_slas

    num_slas, in_compliance_count, non_compliance_count = get_sla_counts(resp)
    if non_compliance_count == 0:
        output = 'Great news! All your %s SLAs are in compliance!' % num_slas
    else:
        # Find SLAs that are not in compliance
        non_compliance_slas = get_non_compliance_slas(resp)
        details_list = []
        for key in non_compliance_slas.keys():
            if non_compliance_slas[key] == 1:
                details_list.append(
                    '%s object in SLA %s' % (non_compliance_slas[key], key)
                )
            else:
                details_list.append(
                    '%s objects in SLA %s' % (non_compliance_slas[key], key)
                )
        details = ', '.join(details_list)

        output = (
            '%s out of %s SLAs are in compliance, remaining %s SLAs are not.'
            ' %s are not in compliance.' %
            (in_compliance_count, num_slas, non_compliance_count, details)
        )
    
    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT   

def open_support_tunnel(intent_request):
    ENDPOINT_NODE = 'https://{0}/api/internal/node'
    ENDPOINT_TUNNEL = 'https://{0}/api/internal/node/{1}/support_tunnel'

    resp = requests.get(ENDPOINT_NODE.format(CLUSTER_IP),headers=headers,verify=False)  
    resp = resp.json()

    first_node_id = resp['data'][0]['id']
    output = ''
    if resp['data'][0]['supportTunnel']['isTunnelEnabled']:
        # Tunnel is already open. Get tunnel port.
        output = 'Support tunnel is already open.'
        tunnel_port = resp['data'][0]['supportTunnel']['port']
        output += ' Tunnel port is %s' % tunnel_port
    else:
        values = {'isTunnelEnabled': True, 'inactivityTimeoutInSeconds': 0}
        data = json.dumps(values).encode('utf8')
        print (data)
        resp = requests.patch(ENDPOINT_TUNNEL.format(CLUSTER_IP, first_node_id),headers=headers,verify=False,data=data)
        resp = resp.json()
        tunnel_port = resp['port']
        output = 'Support tunnel has been opened at %s' % tunnel_port
    
    LEX_RESULT['messages'][0]['content'] = output
    LEX_RESULT['sessionState']['intent']['name'] = intent_request['sessionState']['intent']['name'] 
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT           

def dispatch(intent_request):
    intent_name = intent_request['sessionState']['intent']['name']
    response = None
    if intent_name == 'get_cluster_status':
        return get_cluster_status(intent_request)
    elif intent_name == 'get_archived_amount':
        return get_archived_amount(intent_request)
    elif intent_name == 'get_cluster_storage_details':
        return get_cluster_storage_details(intent_request)
    elif intent_name == 'get_data_growth_rate':
        return get_data_growth_rate(intent_request)
    elif intent_name == 'get_node_count':
        return get_node_count(intent_request)
    elif intent_name == 'get_remaining_runway':
        return get_remaining_runway(intent_request)
    elif intent_name == 'get_sla_compliance':
        return get_sla_compliance(intent_request)
    elif intent_name == 'open_support_tunnel':
        return open_support_tunnel(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    response = dispatch(event)
    return response