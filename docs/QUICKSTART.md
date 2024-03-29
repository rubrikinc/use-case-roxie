# Quick Start Guide: Roxie Bot


# Table of Contents

- [Quick Start Guide: Roxie Bot](#quick-start-guide-roxie-bot)
- [Table of Contents](#table-of-contents)
- [Introduction to the Roxie Bot](#introduction-to-the-roxie-bot)
- [Rubrik Cluster Configuration](#rubrik-cluster-configuration)
  - [Generate a Rubrik API Token](#generate-a-rubrik-api-token)
- [AWS Environment Configuration](#aws-environment-configuration)
  - [VPC Networking](#vpc-networking)
  - [IAM Roles](#iam-roles)
    - [Role for AWS Lambda](#role-for-aws-lambda)
    - [Role for AWS Lex](#role-for-aws-lex)
- [Roxie Installation & Configuration](#roxie-installation--configuration)
  - [Automated Installation](#automated-installation)
    - [Prerequisites](#prerequisites)
    - [Configuration](#configuration)
    - [Execution](#execution)
    - [Resources Created](#resources-created)
  - [Manual Installation](#manual-installation)
    - [AWS Lambda](#aws-lambda)
      - [Function Creation](#function-creation)
      - [Modifying the Lambda Role](#modifying-the-lambda-role)
      - [Function Configuration](#function-configuration)
        - [Function Code](#function-code)
        - [Environmental Variables](#environmental-variables)
        - [Network](#network)
      - [Function Testing](#function-testing)
      - [Troubleshooting](#troubleshooting)
        - [Network Troubleshooting](#network-troubleshooting)
        - [Authorization Troubleshooting](#authorization-troubleshooting)
    - [AWS Lex](#aws-lex)
      - [Bot Creation](#bot-creation)
      - [Intent Creation](#intent-creation)
        - [Sample Utterances](#sample-utterances)
        - [Code Hooks](#code-hooks)
      - [Bot Build](#bot-build)
      - [Bot Testing](#bot-testing)
- [Appendix A - Object Details](#appendix-a---object-details)


# Introduction to the Roxie Bot

Roxie may look a little complex, but the overall workflow is actually quite simple. You may want to [watch this getting started video](https://youtu.be/znjH9T3BveM) to better understand the high level components used in this project.

The end-to-end workflow is as follows:

1. A user asks a question using natural spoken or written word.
1. AWS Lex is listening for one or more "sample utterances" to determine your intent. In this case, the intent is to get the cluster status, and so the `cluster_status` intent would be chosen by Lex.
1. Lex then looks to see which AWS Lambda function to execute.
1. This function contains code used to query the Rubrik API and find an answer to our question.
1. The Rubrik API responds to the query and tells Lambda that everything is OK! The function code then formats the message into something a bit more human friendly.
1. The friendly message is handed back to Lex (and the Polly service) to share the good news - your cluster is doing awesome!

![Roxie Architecture](/docs/images/architecture.jpg)

---

# Rubrik Cluster Configuration

Rubrik's powerful API allows you to provide control and visibility to Roxie based on your specific needs and use cases. Access to the API is provided by an API Token. This method allows you to abstract away account information, such as the username and password, into a long, complex looking string called a token. Additionally, the token can be manually or automatically expired if any concerns arise or if the use case has a limited duration.

In order to generate an API Token, you must first decide what sort of user account Roxie will need for your environment. This will have a direct effect on the amount of control you wish to grant Roxie. Some considerations for your account choice include:



*   **End User (Recommended)** - An End User account will limit the scope of authority. This is handy for situations where you only want to provide visibility and reporting to your bot. Make sure the account has visibility to all of the SLA Domains, virtual machines, servers, applications, and cloud workloads that you wish to access via Roxie.
*   **Administrator** - An Administrator account will allow Roxie to receive more powerful commands, such as modifying or updating objects and configuration settings in your Rubrik cluster. While it is still possible to use Rubrik's Role Based Access Control (RBAC) to limit the scope of the Administrator account, it is good to be cautious when granting this level of authority to Roxie.


## Generate a Rubrik API Token

Once you have decided on a user account with the appropriate amount of permissions, log into the Rubrik UI using the account you wish Roxie to use and generate an API Token.



1.  Click on your user account name in the upper right corner of the UI and select **API Token Manager** from the menu.
1.  Click on the green, circular "plus sign" in the upper right of the UI to start the Generate API Token workflow.
    1.  Duration (Days): 30
    1.  Tag: `aws_lambda_functions`
1.  Click the **Generate** button.
1.  The Copy API Token window will appear with a token value displayed.
1.  Click on the **Copy** button to copy the token into your clipboard and close the window.
    1.  Make sure to save the token somewhere safe! For security purposes, Rubrik will never display the token value again.

```
Note: If you make a mistake with this process, just delete the newly generated token and start this workflow over again. A new token will be generated for you.
```

You should now see a new token ID appear in the API Token Manager list with the `aws_lambda_functions` tag associated. The ID value is just the object ID of your token; it is not the actual token used for authentication.

![API Token Manager](/docs/images/api-token-manager.jpg)

There is nothing more to configure in your Rubrik environment. Let's move on to the AWS components!

---

# AWS Environment Configuration

All of the logic and operations of Roxie are stored and live in AWS. While this may sound complex, the actual design is fairly simple. You're going to need to set up two services: AWS Lex for the Roxie bot itself, and AWS Lambda for all of the functions and logic to retrieve information from your Rubrik cluster. That's it!

With that said, there are a number of requirements you must meet in order to be successful with Roxie in AWS, such as making sure your VPC can talk back to your on-premises cluster and setting up IAM roles and policies. We'll go over these steps in greater detail in the next few sections.


## VPC Networking

It is recommended that you connect from AWS to your on-premises Rubrik instances by way of a VPN or dedicated tunnel. Be sure to add any necessary routing between the AWS region you choose and your target Rubrik cluster.


## IAM Roles

An IAM role is similar to a user, in that it is an AWS identity with permission policies that determine what the identity can and cannot do in AWS. However, instead of being uniquely associated with one person, a role is intended to be assumable by anyone who needs it. Also, a role does not have standard long-term credentials (password or access keys) associated with it. Instead, if a user assumes a role, temporary security credentials are created dynamically and provided to the user.

At a high level, there are two roles needed for Roxie to operate properly.

1.  A role for the AWS Lambda functions that are used to talk to the Rubrik API and Roxie bot.
1.  A role for the AWS Lex bot (Roxie) that is used to interact with the user.

These two roles have different purposes and need different permissions that will be described next.

### Role for AWS Lambda

While it is possible to manually generate a Lambda role, it's easiest to let AWS do it for you during the creation of your first Lambda function. This is because all of the permissions for generating CloudWatch Logs in your region. This allows your Lambda functions to write debug and console information to a log to assist with troubleshooting and auditing activities.

However, your future Lambda role will require permissions to use your VPC networking to tunnel back to your on-premises deployment of Rubrik. Let's go ahead and build the required VPC networking permissions into an IAM Policy that will be used later on this guide.

Navigate to IAM > Policies > and click the **Create Policy** button.

*   Service: EC2
*   Actions:
    *   List:
        *   DescribeNetworkInterfaces
    *   Write:
        *   CreateNetworkInterface
        *   DeleteNetworkInterface
*   Resources: *
*   Request conditions: None.

The resulting policy details should be similar to the image below:

![IAM Lambda VPC Policy](/docs/images/iam-lambda-vpc-policy.jpg)

Optionally, if you would rather use the JSON editor, fill in the code below:


```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeNetworkInterfaces"
            ],
            "Resource": "*"
        }
    ]
}
```

Click the **Review Policy** button to proceed.

*   Name: `lambda_vpc`
*   Description: Used to allow Lambda functions the ability to attach to VPC networks.

Click the **Create Policy** button to proceed.

There! You now have an IAM Policy that will be attached to the AWS Lambda role later on in this guide. If you want to take a look at your fancy new policy, it should appear similar to the image below:

![IAM Lambda VPC Policy Summary](/docs/images/iam-lambda-vpc-policy-summary.jpg)

We'll come back to the AWS Lambda role later. For now, you will not have a role generated until reaching the AWS Lambda section of this guide.

### Role for AWS Lex

We also advise letting AWS automatically generate your Lex role during the bot creation process. Amazon Lex will use the role to invoke Amazon Polly when synthesizing speech responses for your Roxie.

The name of the automatically generated role will be `AWSServiceRoleForLexBots` and will have the `AmazonLexBotPolicy` policy assigned. There is no other effort required beyond this initial creation.

We'll come back to the AWS Lex role. For now, you will not have a role generated until reaching the AWS Lex section of this guide.

---

# Roxie Installation & Configuration

Deploying an instance of Roxie into AWS involves the configuration of both AWS Lambda and AWS Lex. Depending on your preference, Roxie can be deployed either through an automated installation script developed with Python or through the series of steps outlined within manual configuration section.

## Automated Installation

The automated installation is by far the easiest way to get a functional Roxie instance configured within our AWS environment. At a high level, the automated installation script will perform the following:

* Creation and upload of Lambda function
* Attachement of Lambda function to specified VPC and specified IAM role
* Configuration of environment variables to support authentication to Rubrik Cluster
* Creation and configuration of Lex Bot (in English)
* Creation and configuration of included intents
* Configuration of fulfilment specification and permissions to run Lambda function
* Initial build of Roxie Lex bot with DRAFT version

Upon completion of the installation script, a fully functional Roxie instance will be available within the specified VPC.

The installation script can be broken down into three main categories: Prerequisites, Configuration, and Execution

### Prerequisites

To successfully execute the automated installation of Roxie the following prerequistes must be met on the clients system:

* [Python 3.x or higher](https://www.python.org/downloads/release/python-370/)
* AWS boto3 Python SDK (`pip install boto3`)
* A fully configured instance of the [AWS CLI](https://aws.amazon.com/cli/) (The script will pull the Access and Secret keys located within the `credentials` file)
* Clone this repo (https://github.com/rubrikinc/use-case-roxie/)
  
### Configuration

The automated installation requires a number of specified configurations in order to carry out the installation:

* **aws_lambda_function_name** - The desired name for the Lambda function created within AWS
* **aws_region** - The desired region to install the Lambda function and Lex bots
* **aws_lambda_subnet_ids** - A comma seperated list of the Subnet IDs of which the Lambda function will execute within
* **aws_lambda_security_group_ids** - A comma seperated list of the Security Group IDs to apply to the Lambda function
* **aws_lambda_runtime** - The version of Python of which to run the Lambda function. Currently Python 3.7 is supported (`python3.7`)
* **aws_lambda_role_arn** - The [ARN of the role](#role-for-aws-lambda) in which the Lambda function will execute.
* **aws_lex_bot_name** - The desired name of the Lex Bot that is created
* **aws_lex_role_arn** - The [ARN of the role](#role-for-aws-lex) utilized to execute the Lex Bot.
* **rbk_cluster_ip** - The IP of the Rubrik Cluster to connect to
* **rbk_auth_token** - The [token utlized](#rubrik-cluster-configuration) to provide authentication into the Rubrik Cluster.

The preferred method of providing the above configuration values to the installation script is by wrapping them up within a JSON file, and passing them to the installation script as an argument like below

```python
python3 install.py config.json
```

An example of a properly formed config.json file is shown below:

```json
{
    "aws_lambda_function_name": "roxie",
    "aws_region": "us-west-2",
    "aws_lambda_subnet_ids": "subnet-9fj8r9e0fjr8,subnet093jd839393kf",
    "aws_lambda_security_group_ids": "sg-0mdked838djkid",
    "aws_lambda_runtime": "python3.7",
    "aws_lambda_role_arn": "arn:aws:iam::1234567890:role/service-role/roxie_lambda",
    "aws_lex_bot_name": "roxie",
    "aws_lex_role_arn": "arn:aws:iam::1234567890:role/aws-service-role/lexv2.amazonaws.com/AWSServiceRoleForLexV2Bots_7Y934EBF929",
    "rbk_cluster_ip": "10.8.107.34",
    "rbk_auth_token": "BIG_LONG_TOKEN_STRING"
}
```

***NOTE: If you would like to have the script generate the `config.json` file for you, simply execute the script without providing the parameter (IE `python3 install.py`)***

### Execution

Once you have a configuration file, the script can be executed by simply running `install.py` and passing the `config.json` file as shown below

```python
python3 install.py config.json
```

Furthermore, the script can be utlized to create the config.json file for you by running it without the config arguments as shown below:

```python
python3 install.py
```

During this execution, the script will prompt you to select various resources within your AWS environment to generate a temporary config. Upon completion, the script will re-run with the newly temporary config.

### Resources Created

The Automated installation script will create the following:

First, a Lex Bot will be created. The Lex Bot is configured with the en_US locale. Lex Bots invoke the Lambda function through various intents (triggers). The intents created via the automated install script are located within the `intents.json` file. Below is a list of currently included intents:

* **get_cluster_status** - retrieves the connectivity status of the nodes within a Rubrik Cluster
* **get_archived_amount** - retrieves the amount of data written to archival locations
* **get_cluster_storage_details** - retrieves storage capacity statistics of the Rubrik Cluster
* **get_data_growth_rate** - retrieves the average daily growth rate
* **get_node_count** - retrieves the number of nodes within the Rubrik cluster
* **get_remaining_runway** - estimates the amount of time before cluster capacity will be exhausted
* **get_sla_compliance** - reports on various compliance statistics based around SLA Domains.
* **open_support_tunnel** - Opens a support tunnel an reports back on the configured port

***Note: We'd also sincerely love it if you would contribute any interesting functions you create back into the Roxie repository on GitHub. Share the love!***

The fulfillment of each intent happens via a single Lambda function. The Lambda function created contains the following python functions:

* **lambda_handler** - This is the entry point into the Lambda function. Each intent will first go through this function. lambda_handler will in turn pass the request to dispatch.
* **dispatch** - dispatch is used to determine which intent is invoking the function. In turn, dispatch calls individual functions depending on the invoking intent
* **individual intent functions** - These functions contain the code to connect the Rubrik API and retrieve the desired response. The responses are then formated into a proper format for Lex.

## Manual Installation

While the ideal option is to run the automated installation, Roxie can be configured manually if desired. The following outlines the process to create a Roxie instance manually.

### AWS Lambda

AWS Lambda is a compute service that lets you run code without provisioning or managing servers. AWS Lambda executes your code only when needed and scales automatically, from a few requests per day to thousands per second. You pay only for the compute time you consume - there is no charge when your code is not running. With AWS Lambda, you can run code for virtually any type of application or backend service - all with zero administration. All you need to do is supply your code in one of the languages that AWS Lambda supports (currently Node.js, Java, C#, Go and Python).

For this guide, we're going to give Roxie the power to get status on our Rubrik cluster that lives on-premises. This is driven by a lambda function written for the Python 3.7 runtime and is available in the Roxie repository on GitHub. Once you get comfortable with the process, feel free to add more functions to your bot to meet your unique use cases.

```
Note: We'd also sincerely love it if you would contribute any interesting functions you create back into the Roxie repository on GitHub. Share the love!
```

Let's start by building the function used to get cluster status.

#### Function Creation

Start by navigating to the AWS Lambda service and clicking the **Create Function** button and choosing the Author From Scratch option.

*   Name: `rubrik-roxie`
*   Runtime: Python 3.7
*   Role: Create a new role from one or more templates
*   Role Name: `roxie_lambda`
*   Policy Templates: Leave blank

Click on the **Create Function** button at the bottom right corner to proceed. The creation process may take a little while to complete.

Once finished, you will be taken to the `rubrik-roxie` function page. There's a lot of menu items on this page - don't be alarmed! We're going to come back to this page in a moment.

#### Modifying the Lambda Role

Remember the `lambda_vpc` IAM Policy that was generated earlier in this guide? It's time to use that policy to add more permissions to the brand new `roxie_lambda` role that you just created during the creation of your lambda function.

```
Note: Skipping this step will result in not being able to choose a VPC for your Lambda function's network. You will be limited to communicating with devices on the public Internet.
```

Navigate back to IAM > Roles and click on your `roxie_lambda` role to edit it. In the next screen, click on the large blue **Attach Policies** button.

![Roxie Lambda Role Summary](/docs/images/roxie-lambda-summary-1.jpg)

Next, select the `lambda_vpc` policy and click on the **Attach Policy** button in the bottom right corner. You should now have two policies attached to the `roxie_lambda` role:

*   `AWSLambdaBasicExecutionRole-{guid}`
*   `lambda_vpc`

![Roxie Lambda Role Summary](/docs/images/roxie-lambda-summary-2.jpg)

The role for your Lambda function is now able to use VPC networking, which results in being able to route back to your on-premises environment.

```
Note: If desired, this is also a good time to add a description to your role since it defaults to a blank value. A description is very helpful to you or your team! Find the Role Description field and click the Edit link next to it. For this example, we're going to use Role for Lambda functions used with Roxie.
```

You can now navigate back to the `rubrik-roxie` Lambda function to proceed with configuration. There is no more work required in IAM.

#### Function Configuration

There are only three sections to edit in the Lambda function page:

1.  [Function Code](#function-code): This is where the Python code for getting cluster status is loaded.
1.  [Environmental Variables](#environmental-variables): This is where the connection information for your Rubrik cluster is stored.
1.  [Network](#network): This is where the VPC network is selected.

##### Function Code

For this guide, we're going to use the contents of the `lambda_function.py` file found in the Roxie repository on GitHub. This file contains the code for responding to all of the built-in Roxie intents, however we will be only walking through the portion to retrieve the status of the cluster.

To upload the code, select **Upload from** dropdown to the top right of our code window, then select **.zip file**. From the presented dialog, select **Upload**

Locate and select the `roxie.zip` file located within the `automated-installation\lambda_functions\roxie\` directory included within this repository.

This will upload the function code, and replace any existing code within the `rubrik-roxie` function. Along with the code, the `requests` library files will also be uploded into the lambda function. The resulting output should look like the image below:

![Function Code for get_cluster_status](/docs/images/roxie-show-code.png)

You can now click the **Save** button in the upper right corner of the window to save your progress. It should change from orange to a greyed-out color upon success.

##### Environmental Variables

Next, the function needs to know how to connect to your cluster. We feel it's better to keep static information out of the function code. 

For this step, it's important to add two environment variables: `CLUSTER_IP` and `AUTH_TOKEN`. This can be done by scrolling down below the Function Code area and locating the Environmental Variables area.

1.  `RBK_CLUSTER_IP`: Enter the IP address of a node in your cluster. Make sure it is reachable from the VPC network that you plan to use for Roxie. This will be covered in the next section.
1.  `RBK_AUTH_TOKEN`: Enter the token created in the Generate a Rubrik API Token section.

![Environmental Variables for get_cluster_status](/docs/images/rbk-environment.png)

With those values updated, you can now click the **Save** button in the upper right corner of the window to save your progress. It should change from orange to a greyed-out color upon success.

##### Network

Now that the function code is loaded, it's time to choose a VPC for your Lambda function to use from a networking perspective. Scroll down to the Network section and load your specific VPC information.

As an example, the Rubrik Build lab uses a specific OR Demo VPC to communicate to the on-premises Rubrik cluster. The image below shows what a successful network configuration might look like for you:

![Network Settings for get_cluster_status](/docs/images/get-cluster-status-network.jpg)

Once finished, you can now click the **Save** button in the upper right corner of the window to save your progress. It should change from orange to a greyed-out color upon success.

```
Note: If the save button remains orange, it typically means that you have not properly added the EC2 permissions necessary for the Lambda role to attach to your VPC network.
```

#### Function Testing

Before proceeding further, it's a good idea to test your Lambda function to make sure that the code and networking configuration are functioning properly. To do this, use the built in Test functionality in the function.

Click the **Test** button in the top right corner. Next, make sure the **Create New Test Event** radio button is selected.

*   Event Template: Hello World
*   Event Name: `get_cluster_status`

Replace the JSON in the editor with the following:

```json
{
    "sessionState": {
        "intent": {
            "name": "get_cluster_status"
        }
    }
}
```

Click on the **Create** button in the bottom right corner to proceed. You should now have a new test named `get_cluster_status` next to the Test button. If so, click on the **Test** button to run the `get_cluster_status` test.

```
Note: This test event will only test the `get_cluster_status` intent. You can configure other events for other intents as you build them out.
```

The top area of the window will have a new area generated that contains the execution results of your test. If all goes well, this area will change to a light green color and state a result of succeeded. You can expand the details section to see the results in JSON format. In this example, had Roxie been asked to get cluster status by a user, she would have responded with "Your cluster is doing awesome."

![Test Content for get_cluster_status](/docs/images/get-cluster-test-result.png)

#### Troubleshooting

Most of the issues discovered with AWS Lambda fall into two categories: networking or authorization. Check out the checklists below to get around any known stumbling points or submit an Issue on the Roxie repository on GitHub for more prescriptive assistance.

##### Network Troubleshooting

Some items to investigate on the network:

*   Have you checked your security device logs to see if the function traffic is being received end-to-end?
*   Does your function have the correct network configuration values for the VPC, subnets, and security group?
*   Does your function correctly use the role that you attached the `lambda_vpc` policy against?
*   Have you checked to make sure that the VPC subnets can talk to your Rubrik cluster?
*   Are there any firewalls blocking the traffic?
*   Is your NAT Gateway configured properly?
*   Are you able to build an EC2 instance in the VPC network that your function is trying to use in order to validate that it can communicate with your Rubrik cluster?
*   Have you looked at the CloudWatch Logs and/or CloudTrail details to see where the function is failing?

##### Authorization Troubleshooting

Some items to investigate for authorization:

*   Have you checked the Rubrik cluster to see why the authorization request failed?
*   Have you perhaps limited the Roxie account to the point where it can't get cluster status?
*   Have you tried using an Administrative token to see if the issue is with the scope or permissiveness of your account?

### AWS Lex

Amazon Lex is an AWS service for building conversational interfaces into applications using voice and text. With Amazon Lex, the same deep learning engine that powers Amazon Alexa is now available to any developer, enabling you to build sophisticated, natural language chatbots into your new and existing applications. Amazon Lex provides the deep functionality and flexibility of natural language understanding (NLU) and automatic speech recognition (ASR) to enable you to build highly engaging user experiences with lifelike, conversational interactions and create new categories of products.

Roxie uses Amazon Lex to come alive and answer your questions. For every question you ask, she will attempt to look through all of the available decision points to see if there is a Lambda function that can be called to answer your question. Consider Lex to be Roxie's brain - she accepts verbal inputs, uses Lambda to find the answer, and then responds as an output.

![Roxie Architecture](/docs/images/architecture.jpg)

***NOTE: This guide has been updated to utilize the Lex v2 Bot APIs. If you are unable to utilize the v2 APIs and are restricted to the original Lex APIs please see the [older version of this guide here](QUICKSTART-V1.md)***

#### Bot Creation

Start by making a new custom bot for Roxie to use. If you are still utilizing the older v1 Console, switch to the new v2 console by selecting **Switch to the new Lex V2 console**. 

![Switch to V2 Console](/docs/images/switch-to-v2.png)

Once on the V2 console, select **Create bot**

*   AWS Lex > Bots > Create > Custom Bot
    *   Bot Name: Roxie
    *   IAM Permissions: Create a role with basic Amazon Lex permissions. 
    *   COPPA: No
    *   Idle Session Timeout: 1 minute
    *   Language: English (US)
    *   Voice Interaction: Ivy
    *   Intent classification confidence score threshold: 0.40

You now have a new bot to use for Roxie. That wasn't hard at all!

Before creating intents, we need to point the newly created Roxie bot to our Lambda function for intent fulfillment:

* AWS Lex > Bots > Roxie > Aliases > TestBotAlias > English (US)
    * Source: rubrik-roxie
    * Lambda function version or alias: $LATEST

![Assign Lambda Function](/docs/images/lambda-function-assign.png)

Now that our Lambda function and Lex bot have been linked we can begin creating intents.

#### Intent Creation

Upon bot creation, you will be taken to the intents configuration. An intent represents an action that the user wants to perform. Each intent should map to a command that you wish to see Roxie respond to.

If you are not on the intents page, browse to your bot -> Aliases -> TestBotAlias -> English (US) -> Intents

1.  Click on the **Add Intent** -> **Add empty intent** to start the workflow.
2.  Finally, give this intent a name. We're going to use the name `get_cluster_status`. ***NOTE: This much mach the intent names within the dispatch function of Lambda. You can find the desired intent names and sample utterances in the intents.json file located within this repo**

You now have your first intent. Let's dive deeper into the configuration areas of focus: sample utterances and fulfillment.

##### Sample Utterances

A sample utterance is the words or phrases that Roxie will listen for when determining what to do. Since this guide is all about getting cluster status, it would make sense to pick 3-5 of the most common ways that question can be asked and use them as sample utterances.

We'll pick several phrases from the `intents.json` example and enter them below:

1.  Status of my cluster
2.  Is the cluster doing okay
3.  How is my cluster doing
4.  What is the cluster status
5.  What is the status of the cluster

![Sample Utterances](/docs/images/sample-utterances.jpg)

If the spoken command matches one of the sample utterances, the intent will be chosen. Roxie will then look at the fulfillment to see what to do next.

##### Code Hooks

The business logic required to fulfill the user's intent is called a fulfillment. Essentially, if Roxie hears the phrase "What is the status of the cluster", she then needs to know how to respond. We're going to use the Lambda function created earlier to programmatically reach out to Rubrik cluster's API and retrieve information needed to respond.

Navigate to the Code hooks section of the intent, choose the **Use a Lambda function for fulfillment** checkbox.

![Fulfillment](/docs/images/fulfillment.png)

Configuration for this intent is now done. Make sure to scroll all the way to the bottom of the intent window and click **Save Intent**.

#### Bot Build

With the configuration out of the way, it's now time to build the bot with the new intent. From the intents section, located the **Build** button on the bottom right hand corner of the screen.

```
Note: You will most likely see a warning that says "You can continue editing your bot while the build is in progress. You can start testing your bot after the build completes." You can safely accept this warning by clicking the new Build button that is presented to you.
```

Once the build finishes, the message shown in the image below will most likely appear.

![Roxie Build Successful](/docs/images/roxie-build-successful.jpg)

#### Bot Testing

Let's test the bot and intent to see if it works properly. Click the **Test** button on the bottom right hand corner of the screen. This testing area allows you to either speak or type a sample utterance and see if the correct response is returned. This is the one time it's perfectly acceptable to talk to yourself out loud!

If you have a microphone handy, click on the small microphone button shown in the image below and speak an utterance. When done, click the small microphone button again to signal that you are done talking.

```
Note: If you don't have a microphone handy, you can type into the chat box instead.
```

![Test Bot Screen](/docs/images/test-bot-1.jpg)

Roxie will interpret the audio input and try to match it against an utterance contained in one or more intents. The response data contains a lot of great information to help understand what Lex is doing for Roxie. Click on the **Detail** radio button as shown in the image below to see more.

![Test Bot Screen](/docs/images/test-bot-2.jpg)

*   Intent-Name: This should match the intent based on the sample utterances provided int the intent. In this case, you should see the value of `get_cluster_status`.
*   Dialog-State: Fulfilled
*   Input-Transcript: The words you spoke into the microphone.
*   Message: The response from Roxie, as generated by the Lambda function `rubrik-roxie`.

Feel free to experiment with different inputs to tweak your sample utterances and add any that you think are missing.

# Appendix A - Object Details

All of the function, policy, role, bot, and other names used in this document.

<table>
  <tr>
   <td>Object
   </td>
   <td>Type
   </td>
   <td>Notes
   </td>
  </tr>
  <tr>
   <td><code>get_cluster_status</code>
   </td>
   <td>Lambda Function
   </td>
   <td>Based on <code>get_cluster_status.py</code>
   </td>
  </tr>
  <tr>
   <td><code>cluster_status</code>
   </td>
   <td>Lex Intent
   </td>
   <td>Gets cluster status by calling the <code>get_cluster_status</code> Lambda function
   </td>
  </tr>
  <tr>
   <td><code>aws_lambda_functions</code>
   </td>
   <td>RCDM Token
   </td>
   <td>Token used to authenticate the Lambda function calls
   </td>
  </tr>
  <tr>
   <td><code>lambda_vpc</code>
   </td>
   <td>IAM Policy
   </td>
   <td>Policy giving the Lambda functions (such as <code>get_cluster_status</code>) the ability to use a VPC network
   </td>
  </tr>
  <tr>
   <td><code>AWSServiceRoleForLexBots</code>
   </td>
   <td>IAM service-role 
   </td>
   <td>Used by the Lex bot
   </td>
  </tr>
  <tr>
   <td><code>AmazonLexBotPolicy</code>
   </td>
   <td>IAM Policy
   </td>
   <td>Used by the Lex bot to access the Polly service
   </td>
  </tr>
  <tr>
   <td><code>get_cluster_status.py</code>
   </td>
   <td>Python code
   </td>
   <td>Contains the code for the <code>get_cluster_status</code> function
   </td>
  </tr>
</table>
