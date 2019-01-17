"""Return SLA compliance summary."""
import json
import math
import os
import ssl
import urllib2

CLUSTER_IP = os.environ['CLUSTER_IP']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

''' Sample Utterances
How are my SLAs doing
Are my SLAs in compliance
Read out SLA compliance summary
Get me SLA compliance summary
Give me SLA compliance summary
How many SLAs are in compliance
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

ENDPOINT_SLA_COMP_SUMMARY = (
    'https://{0}/api/internal/report?report_template=SlaComplianceSummary'
)
ENDPOINT_SLA_COMP_CHART = 'https://{0}/api/internal/report/{1}/chart'


def lambda_handler(event, context):
    del event
    del context

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Get CustomReport ID
    req = urllib2.Request(ENDPOINT_SLA_COMP_SUMMARY.format(CLUSTER_IP), None)
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)
    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))
    print('REST API call response: %s' % resp)
    """ Sample response:
    {u'data': [{u'updatedTime': u'2019-01-15T20:54:15+0000',
      [{u'updatedTime': u'2019-01-15T20:54:15+0000',
        u'name': u'SLA Compliance Summary',
        u'reportTemplate': u'SlaComplianceSummary',
        u'id': u'CustomReport:::31fd5038-5ed1-464e-9907-7d597b10a958',
        u'reportType': u'Canned',
        u'updateStatus': u'Ready'}],
      u'total': 1,
      u'hasMore': False
    }
    """
    # Extract report ID
    report_id = resp['data'][0]['id']

    # Get details of the report using ID from above
    req = urllib2.Request(
        ENDPOINT_SLA_COMP_CHART.format(CLUSTER_IP, report_id), None
    )
    req.add_header('Authorization', 'Bearer %s' % AUTH_TOKEN)

    handler = urllib2.HTTPSHandler(context=ssl_context)
    opener = urllib2.build_opener(handler)
    resp = json.load(opener.open(req))
    print('REST API call response: %s' % resp)
    """ Sample response:
    [{u'reportTemplate': u'SlaComplianceSummary', u'name': u'SLA Compliance',
      u'attribute': u'ComplianceStatus',
      u'dataColumns': [
        {u'dataPoints': [{ u'value': 4.0, u'measure': u'ObjectCount'}],
         u'label': u'InCompliance'},
        {u'dataPoints': [{u'value': 0.0, u'measure': u'ObjectCount'}],
         u'label': u'NonCompliance'}
      ],
      u'measure': u'ObjectCount', u'chartType': u'Donut', u'id': u'chart0'
     },

     {u'reportTemplate': u'SlaComplianceSummary',
      u'name': u'SLA Compliance by SLA Domain', u'attribute': u'SlaDomain',
      u'dataColumns': [
        {u'dataPoints': [
           {u'value': 2.0, u'measure': u'InComplianceCount'},
           {u'value': 0.0, u'measure': u'NonComplianceCount'}],
         u'label': u'OneHourSLA'},
        {u'dataPoints': [
           {u'value': 2.0, u'measure': u'InComplianceCount'},
           {u'value': 0.0, u'measure': u'NonComplianceCount'}],
         u'label': u'Gold'}
      ],
      u'measure': u'StackedComplianceCountByStatus',
      u'chartType': u'StackedVerticalBar',
      u'id': u'chart1'
     }
    ]
    """
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

    LEX_RESULT['dialogAction']['message']['content'] = output
    print('Response to Lex: %s' % LEX_RESULT)
    return LEX_RESULT

if __name__ == '__main__':
    lambda_handler(None, None)
