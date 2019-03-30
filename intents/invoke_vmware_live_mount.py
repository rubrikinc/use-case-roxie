"""Invoke VMware Live Mount"""
import json
import os
import ssl
import urllib2
import urllib

CLUSTER_IP = os.environ['CLUSTER_IP']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

''' Sample Utterances
Live mount a VMware VM
Invoke a VMware VM Live Mount
Invoke a VMware Virtual Machine Live Mount
Live mount a VMware Virtual Machine
Live Mount a VM
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

ENDPOINT_VM_ID = 'https://{0}/api/v1/vmware/vm?is_relic=false&primary_cluster_id=local&name={1}'
ENDPOINT_VM_SNAPSHOT = 'https://{0}/api/v1/vmware/vm/{1}/snapshot'
ENDPOINT_LIVE_MOUNT = 'https://{0}/api/v1/vmware/vm/snapshot/{1}/mount'

def lambda_handler(event, context):
    #del event
    #del context

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    vm_name = event['currentIntent'] ['slots'] ['slotOne']

    #Get VM ID
    req = urllib2.Request(ENDPOINT_VM_ID.format(CLUSTER_IP,vm_name), None)
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))    
    print(resp["total"])
    if resp["total"] == 1:
        #Get latest snapshot from VM
        vm_id = resp["data"][0]["id"]
        req = urllib2.Request(ENDPOINT_VM_SNAPSHOT.format(CLUSTER_IP,vm_id), None)
        req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
        handler = urllib2.HTTPSHandler(context=ssl_context)
        opener = urllib2.build_opener(handler)
        resp = json.load(opener.open(req))
        if resp["total"] == 0:
            output = "No snapshots exist for vm matching " + vm_name + ". Aborting"
        else:
            #Lets keep going
            snapshot_id = resp["data"][0]["id"]
            print(ENDPOINT_LIVE_MOUNT.format(CLUSTER_IP,snapshot_id))
            values = { }
            data = urllib.urlencode(values)
            req = urllib2.Request(ENDPOINT_LIVE_MOUNT.format(CLUSTER_IP,snapshot_id), data)
            req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
            handler = urllib2.HTTPSHandler(context=ssl_context)
            opener = urllib2.build_opener(handler)
            resp = json.load(opener.open(req))
            output='Latest snapshot for ' + vm_name + ' has been mounted.'
    else:
        output = "No VMs found matching " + vm_name
    
    LEX_RESULT['dialogAction']['message']['content'] = output
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
