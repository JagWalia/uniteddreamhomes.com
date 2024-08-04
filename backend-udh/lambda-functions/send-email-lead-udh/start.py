import os
import sys
import json
import time
# from secretmanager import get_secret
import base64
import datetime

import boto3
from botocore.exceptions import ClientError

# print(os.environ)

def handler(event, context):

    print(f'event: {event}')

    allowed_urls = os.environ['allowed_url']

    print(f'Allowed URLs: {allowed_urls}')

    # Extract the origin from the request headers
    origin = event.get('headers', {}).get('origin', '')
    print(f"Origin:  '{origin}', length: {len(origin)}")

    # Check if the origin is in the list of authorized domains
    if (origin not in allowed_urls) or (len(origin)==0):
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({'message': 'Forbidden: Access denied.'})
        }


    body = json.loads(event["body"])
    lead = body.get('lead',{})
    if not lead:
        lead = body

    name = lead.get("name","")
    phone = lead.get("phone","")
    email = lead.get("email","")
    address = lead.get("address","")
    subject = lead.get("subject","")
    message = lead.get("message","")

    if len(name)+len(phone)+len(email)+len(address)+len(subject)+len(message)==0:
        message = "No name+phone+email+address+subject+message in json is attached to the event",

        return_message = {
                "statuscode":"400",
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({"message": f"No valid data in request. {message}"})
            }
        print(return_message)
        return return_message
    
    website_lead_topic = os.environ.get('website_lead_topic')

    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject_with_datetime = f"New Lead - {subject} - {current_datetime}"

    # Use boto3 to publish a message to the SNS topic
    sns = boto3.client('sns')

    # subject = "New Lead - United Dream Homes Website"
    html_body = f"""
    <html>
        <head></head>
        <body>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Address:</strong> {address}</p>
            <p><strong>Message:</strong> {message}</p>
        </body>
    </html>
    """
    text_body = f"""
            Subject:     {subject} \n
            ---------------------------------------------------------\n
            Name:        {name}    \n
            Phone:       {phone}   \n
            Email:       {email}   \n
            Address:     {address} \n
            Message:     {message} \n
    """


    # Send the email
    try:
    # Publish the message to SNS topic
        response=sns.publish(
            TopicArn=website_lead_topic,
            Subject=subject_with_datetime,
            Message=text_body
        )

        message =  f"Email sent successfully - {current_datetime}"

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                "Content-Type": "application/json"
        },
            'body': json.dumps({"message": message})
        }
    except ClientError as e:
        message =f"SNS Email Error: {e}"
        return_message = {
                "statuscode":"300",
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                    "Content-Type": "application/json"
                },
                'body': json.dumps({'message': F'Error : {message}'})
            }
        print(return_message)
        return return_message
    


#######################################
