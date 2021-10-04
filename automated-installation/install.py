import boto3
import json
import sys
import time
from botocore.config import Config

def get_aws_region(client): 
    regions = client.describe_regions()
    selected = False
    while selected == False:
        i = 1
        for key in regions['Regions']:
            print(str(i) + ". "+ key['RegionName'])
            i = i + 1
        region_key = input("Enter corresponding number for desired region to place Lambda functions: ")

        if region_key.isnumeric():
            if int(region_key) < len(regions['Regions']) + 1 and int(region_key) > 0:
                break
            else:
                print ("You must enter a number between 1 and " + str(len(regions["Regions"])))
        else:
            print ("You must enter a number between 1 and " + str(len(regions["Regions"])))

    return regions["Regions"][int(region_key) -1]["RegionName"]

def get_aws_lambda_vpc(client):
    response = client.describe_vpcs()
    selected = False
    while selected == False:
        i = 1
        for vpc in response['Vpcs']:
            tags = vpc.get('Tags')
            if tags == None:
                name = '(No tag specifing name)'
            else:
                tag_dict = {tag['Key']: tag['Value'] for tag in tags}
                name = "(" + tag_dict['Name'] + ")"
            print(str(i) + ". "+ vpc['VpcId'] + " " + name)
            i = i + 1
        vpc_key = input("Enter corresponding number for desired VPC: ")

        if vpc_key.isnumeric():
            if int(vpc_key) < len(response['Vpcs']) + 1 and int(vpc_key) > 0:
                break
            else:
                print ("You must enter a number between 1 and " + str(len(response['Vpcs'])))
        else:
            print ("You must enter a number between 1 and " + str(len(response['Vpcs'])))

    vpc_id = response["Vpcs"][int(vpc_key) -1]["VpcId"]
    return vpc_id



def get_aws_lambda_subnets(client, aws_lambda_vpc_id):
    # remove following 2 lines in prod
    response = client.describe_subnets(
        Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [aws_lambda_vpc_id]
                }
            ]
    )
    available_subnet_ids = list()
    for subnet in response['Subnets']:       
        tags = subnet.get('Tags')
        if tags == None:
            name = 'No tag specifing name'
        else:
            tag_dict = {tag['Key']: tag['Value'] for tag in tags}
            name = tag_dict['Name'] 
        subnet = {
            'Id': subnet['SubnetId'],
            'Name': name
        }
        available_subnet_ids.append(subnet)
    
    selected_subnet_ids = list()
    done = False
    while done == False:    
        # check if all are added
        if len(available_subnet_ids) < 1:
            break
        i = 1
        
        print ("Enter 'D' when finished adding subnets")
        for subnet in available_subnet_ids:
            print(str(i)+". " + subnet["Id"] + " - " + subnet["Name"])
            i = i + 1
        
        print("")
        print("Currently selected subnets: ")
        print ('[%s]' % ', '.join(map(str, selected_subnet_ids)))
        sub_key= input("Enter the number of subnet to utilize: ")
        if sub_key == "D":
            break
        elif sub_key.isnumeric():
            if int(sub_key) < len(available_subnet_ids) + 1 and int(sub_key) > 0:
                selected_subnet_ids.append(available_subnet_ids[int(sub_key)-1]["Id"])
                available_subnet_ids.remove(available_subnet_ids[int(sub_key)-1])
            else:
                print ("You must enter a number between 1 and " + str(len(available_subnet_ids)))
        else:
            print ("You must enter a number between 1 and " + str(len(available_subnet_ids)))

    return selected_subnet_ids

def get_aws_security_groups(client, aws_lambda_vpc_id):
    # remove following 2 lines in prod
    response = client.describe_security_groups(
        Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [aws_lambda_vpc_id]
                }
            ]
    )
    available_security_group_ids = list()
    for securitygroup in response['SecurityGroups']:       
        tags = securitygroup.get('Tags')
        if tags == None:
            name = 'No tag specifing name'
        else:
            tag_dict = {tag['Key']: tag['Value'] for tag in tags}
            name = tag_dict['Name'] 
        securitygroup = {
            'Id': securitygroup['GroupId'],
            'Name': name
        }
        available_security_group_ids.append(securitygroup)
    
    selected_security_group_ids = list()
    done = False
    while done == False:    
        # check if all are added
        if len(available_security_group_ids) < 1:
            break
        i = 1
        
        print ("Enter 'D' when finished adding security groups")
        for securitygroup in available_security_group_ids:
            print(str(i)+". " + securitygroup["Id"] + " - " + securitygroup["Name"])
            i = i + 1
        
        print("")
        print("Currently selected security groups: ")
        print ('[%s]' % ', '.join(map(str, selected_security_group_ids)))
        sub_key= input("Enter the number of Security Group to utilize: ")
        if sub_key == "D":
            break
        elif sub_key.isnumeric():
            if int(sub_key) < len(available_security_group_ids) + 1 and int(sub_key) > 0:
                selected_security_group_ids.append(available_security_group_ids[int(sub_key)-1]["Id"])
                available_security_group_ids.remove(available_security_group_ids[int(sub_key)-1])
            else:
                print ("You must enter a number between 1 and " + str(len(available_security_group_ids)))
        else:
            print ("You must enter a number between 1 and " + str(len(available_security_group_ids)))

    return selected_security_group_ids

def get_aws_lambda_role():
    client = boto3.client('iam')
    response = client.list_roles()
    available_roles = list()
    for role in response['Roles']:       
        newrole = {
            'Arn': role['Arn'],
            'Name': role['RoleName']
        }
        available_roles.append(newrole)

    selected = False
    while selected == False:
        i = 1
        for role in available_roles:
            print(str(i) + ". "+ role['Name'])
            i = i + 1
        role_key = input("Enter corresponding number for desired role: ")

        if role_key.isnumeric():
            if int(role_key) < len(available_roles) + 1 and int(role_key) > 0:
                break
            else:
                print ("You must enter a number between 1 and " + str(len(available_roles)))
        else:
            print ("You must enter a number between 1 and " + str(len(available_roles)))

    role_arn = available_roles[int(role_key) -1]["Arn"]
    return role_arn



def create_config():
    global config

    client = boto3.client("ec2")
    aws_lambda_function_name = input("Enter a name for your lambda function: ")
    aws_region = get_aws_region(client)
    client = boto3.client("ec2", region_name=aws_region)
    aws_lambda_vpc_id = get_aws_lambda_vpc(client)
    aws_lambda_subnet_ids = ",".join(get_aws_lambda_subnets(client,aws_lambda_vpc_id))
    aws_lambda_security_group_ids = ",".join(get_aws_security_groups(client,aws_lambda_vpc_id))
    aws_lambda_role_arn = get_aws_lambda_role()
    aws_lex_bot_name = input("Enter a name for your AWS Lex bot: ")
    aws_lex_role_arn = input("Enter the ARN for the role to use with Lex: ")
    rbk_cluster_ip = input("Enter the IP address of the cluster to connect to: ")
    rbk_auth_token = input("Enter the API token of the Rubrik Cluster: ")
    config = {
        "aws_lambda_function_name": aws_lambda_function_name,
        "aws_region": aws_region,
        "aws_lambda_subnet_ids": aws_lambda_subnet_ids,
        "aws_lambda_security_group_ids": aws_lambda_security_group_ids,
        'rbk_cluster_ip': rbk_cluster_ip,
        'rbk_auth_token': rbk_auth_token,
        'aws_lambda_runtime': 'python3.7',
        'aws_lambda_role_arn': aws_lambda_role_arn,
        'aws_lex_bot_name': aws_lex_bot_name,
        'aws_lex_role_arn': aws_lex_role_arn
    }
    return config

def create_lambda_function(client,config):
    print ("Creating Lambda function ({0}) - This can take a few minutes, will process in background!".format(config['aws_lambda_function_name']))
    lambda_function = client.create_function(
        FunctionName=config['aws_lambda_function_name'],
        Runtime = config['aws_lambda_runtime'],
        Handler = 'lambda_function.lambda_handler',
        Role = config['aws_lambda_role_arn'],
        Code = {'ZipFile': open('./lambda_functions/roxie/roxie.zip','rb').read()},
        Timeout = 45,
        VpcConfig = {
            'SubnetIds': config['aws_lambda_subnet_ids'].split(","),
            'SecurityGroupIds': config['aws_lambda_security_group_ids'].split(",")
        },
        Environment = {
            'Variables': {
                'RBK_CLUSTER_IP': config['rbk_cluster_ip'],
                'RBK_AUTH_TOKEN': config['rbk_auth_token']
            }
        }
    )

    return lambda_function

def create_lex_bot_intents(aws_lex_bot_id):

    with open('intents.json') as f:
        data = json.load(f)
    
    for intent in data['Intents']:
        aws_lex_intent_utterances = intent['utterances']
        aws_lex_intent_name = intent['name']
        aws_lex_intent_description = intent['description']
        #MWP finish
        response = lex.create_intent(
            intentName=aws_lex_intent_name,
            description=aws_lex_intent_description,
            sampleUtterances=aws_lex_intent_utterances,
            fulfillmentCodeHook={
                'enabled': True
            },
            botId = aws_lex_bot_id,
            localeId="en_US",
            botVersion="DRAFT",
        )

def create_lex_bot(lex,config,lmda):
    print("Creating the Lex bot ({0})".format(config['aws_lex_bot_name']))
    response = lex.create_bot(
        botName=config['aws_lex_bot_name'],
        description="Roxie, Rubrik's intelligent personal assistant",
        dataPrivacy={
            'childDirected': False
        },
        idleSessionTTLInSeconds=300,
        roleArn = config['aws_lex_role_arn']
    )
    aws_lex_bot_id =  response["botId"]

    print("Waiting for bot to be created...")
    response = lex.describe_bot(
        botId=aws_lex_bot_id
    )
    bot_status = response['botStatus']
    while bot_status != "Available":
        print("Bot status is "+ bot_status)
        time.sleep(2)
        response = lex.describe_bot(
            botId=aws_lex_bot_id
        )
        bot_status = response['botStatus']
    response = lex.describe_bot(
        botId=aws_lex_bot_id
    )
    print ("Bot created...")
    print("Creating en_US Bot Locale")
    response = lex.create_bot_locale(
        botId=aws_lex_bot_id,
        botVersion = "DRAFT",
        localeId = "en_US",
        nluIntentConfidenceThreshold=0.40,
        voiceSettings={
            'voiceId': 'Ivy'
        }
    )

    response = lex.describe_bot_locale(
        botId = aws_lex_bot_id,
        botVersion = "DRAFT",
        localeId = "en_US"
    )
    locale_status = response['botLocaleStatus']
    while locale_status != 'NotBuilt':
        print ("Bot Locale Status is " + locale_status)
        time.sleep(2)
        response = lex.describe_bot_locale(
            botId = aws_lex_bot_id,
            botVersion = "DRAFT",
            localeId = "en_US"
        )
        locale_status = response['botLocaleStatus']
    print("Bot Locale en_US created!")
    print("Creating Intents...")
    create_lex_bot_intents(aws_lex_bot_id)
    print("Done adding intents!")
    print("Attaching Lex bot to Lambda function")
    response = lex.list_bot_aliases(
        botId = aws_lex_bot_id
    )
    aws_lex_bot_alias_id = response['botAliasSummaries'][0]['botAliasId']
    aws_lex_bot_alias_name = response['botAliasSummaries'][0]['botAliasName']
    # Get lambda Arn
    response = lmda.get_function(
        FunctionName=config['aws_lambda_function_name']
    )
    aws_lambda_function_arn = response['Configuration']['FunctionArn']
    # Update alias w/ Lambda
    response = lex.update_bot_alias(
        botAliasId = aws_lex_bot_alias_id,
        botAliasName = "TestBotAlias",
        botVersion = "DRAFT",
        botAliasLocaleSettings={
            "en_US": {
                "enabled": True,
                "codeHookSpecification": {
                    "lambdaCodeHook": {
                        "lambdaARN": aws_lambda_function_arn,
                        'codeHookInterfaceVersion': "1.0"
                    }
                }
            }
        },
        botId = aws_lex_bot_id
    )
    print("Done attaching Lex to Lambda")
    print("Adding permission for Lex to call Lambda function")
    aws_account_id = boto3.client('sts').get_caller_identity().get('Account')
    aws_lex_bot_arn = "arn:aws:lex:{0}:{1}:bot-alias/{2}/{3}".format(config['aws_region'], aws_account_id,aws_lex_bot_id,aws_lex_bot_alias_id)

    response = lmda.add_permission(
        FunctionName=config['aws_lambda_function_name'],
        StatementId="AllowLexBot-"+config['aws_lex_bot_name']+"-AccessToLambdaFunction-"+config['aws_lambda_function_name'],
        Action="lambda:InvokeFunction",
        Principal="lexv2.amazonaws.com",
        SourceArn=aws_lex_bot_arn
    )
    print("Done with permissions")
    print("Beginning initial build of bot")
    response = lex.build_bot_locale(
        botId=aws_lex_bot_id,
        botVersion="DRAFT",
        localeId="en_US"
    )
    print("Build has began on bot.")
    return aws_lex_bot_id


# Working Code!
if len(sys.argv) > 1:
    # config argument passed - let's read it
    print("Loading configuration from file (" + sys.argv[1] + ")")
    with open(sys.argv[1]) as file:
        config = json.load(file)
else:
    print ("No configuration file specified, creating temporary config now...")
    config = create_config()

boto_config = Config(
    region_name = config['aws_region']
)


lmda = boto3.client('lambda', config=boto_config)
lex = boto3.client('lexv2-models',config=boto_config)

aws_lambda_function = create_lambda_function(lmda,config)
aws_lex_bot = create_lex_bot(lex,config,lmda)

# Let's check on some background processes - first, the bot locale build
print("Waiting for bot locale to build")
response = lex.describe_bot_locale(
    botId = aws_lex_bot,
    botVersion = "DRAFT",
    localeId = "en_US"
)
bot_locale_status = response['botLocaleStatus']
while bot_locale_status != 'Built':
    print ("Bot Locale Status is " + bot_locale_status)
    time.sleep(2)
    response = lex.describe_bot_locale(
        botId = aws_lex_bot,
        botVersion = "DRAFT",
        localeId = "en_US"
    )
    bot_locale_status = response['botLocaleStatus']

print("Bot Locale Status has completed building")
print("Checking status of Lambda function creation background process...")    


response = lmda.get_function(
    FunctionName=config['aws_lambda_function_name']
)
lambda_function_status = response['Configuration']['State']
print("Lambda function state: {0}".format(lambda_function_status))
while lambda_function_status != "Active":
    print("Lambda function state: {0} - Waiting".format(lambda_function_status))
    response = lmda.get_function(
        FunctionName=config['aws_lambda_function_name']
    )
    lambda_function_status = response['Configuration']['State']
    time.sleep(4)
response = lmda.get_function(
    FunctionName=config['aws_lambda_function_name']
)
lambda_function_status = response['Configuration']['State']
print("Lambda function state: {0}".format(lambda_function_status))


print("All done - have fun chatting!")



