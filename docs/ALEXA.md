# Creating a Roxie Alexa Skill

# Table of Contents

# Introduction to the Roxie Alexa Skill

Since Amazon's Alexa utlizes Lex in order to determine and power intents for its' skills, porting Roxie to an Alexa Skill is a fairly simple process.  This guide will walk through the steps which need to be performed in order to export/import the Lex intents, create the wrapper Lambda function, and publish the Alexa skill to a subset of beta users. Requirements and configuration may change if wishing to publically publish a skill within the Alexa Skills directory or the Alexa for Business directory.

Even though Alexa is powered by Lex, there are a number of different requirements and limitations which must be met and overcome before the skill will work. For example, while Lex allows us to configure an endpoint (Lambda function) per intent, Alexa only supports one endpoint overall. For this reason we need to build a wrapper Lambda function which will in turn call the individual Roxie Lambda functions.  

The end to end workflow is as follows:

1. A users asks a question to Roxie via the Alexa skill keyword.
1. Alexa Skills Kit (ASK) translates the utterances or spoken words to a given intent.
1. The intent is sent to the wrapper Lambda function (ASK endpoint) for processing.
1. The wrapper Lambda function processes the intent name, calling the associated individual Lambda function to fulfil the intent.
1. The individual function contains code used to query the Rubrik API and find an answer to our question.
1. The Rubrik API responds to the query and responds to the individual Lambda function. The function code then formats the message into something a bit more human friendly.
1. The friendly message is handed back to the wrapper Lambda function, where it is then further modified into a format which the Alexa Skill can read and sent to the Alexa Skill.
1. The Alexa Skill then presents the response to the user via spoken word.

# Prerequisites

The following are the prerequisites required in order to create and test the Roxie Alexa Skill

* Installation and configuration of a function Roxie Chatbot
* Access to the Alexa Developer Portal
* An Amazon Echo, Echo Dot, or Alexa supported device registered to an Amazon account

# Configuration

## Create an Alexa Skill

1. Log into the Alexa Developer Portal and click `Create Skill` to create a new skill. Give the skill your desired name, selecting `Custom` as a model, and `Provision your own` for backend hosting.
1. From the template selection screen, select `Start from scratch`
1. From the left hand navigation within the build section, select `Invocation`.
1. Here we need to define an invocation name for our skill. This will be the command passed to Alexa to invoke our skill. This example uses ``Rubrik Roxy``. *Note - Roxy must be spelt with a 'y' here in order for Alexa to understand the pronounciation of our invocation.*
1. From the left hand navigational menu, select `JSON editor`.
1. Drag and drop [this file](https://dothis) containing the Roxie intents into the JSON editor and click `Save Model`
***NOTE*** The names of the intents must be an exact match with the names of the individual Lambda functions setup within your Roxie bot. The wrapper function created later will execute these individual functions based on the intent name.  Ensure that the intent names match.

With our intents and invocation configured, we can now begin to create the wrapper lambda function.  

## Create a wrapper Lambda Function

## Associate wrapper Lambda function ARN with Alexa Skill

## Modify IAM service role used by Roxie

## Publish the Alexa skill and associate beta user(s)