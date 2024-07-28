import os
import sys
import json
import time
# from secretmanager import get_secret
import base64

import boto3
from botocore.exceptions import ClientError

# print(os.environ)

def handler(event, context):

    print(f'event: {event}')

    allowed_urls = os.environ['allowed_url']

    # Extract the origin from the request headers
    origin = event.get('headers', {}).get('origin', '')
    print(f'Origin:  {origin}')

     # Check if the origin is in the list of authorized domains
    if origin not in allowed_urls:
        # block access
        return {
            'isAuthorized': False,
            'context': {
                'origin': origin
            }
        }

    body = json.loads(event["body"])
    lead = body.get('lead',{})
    if len(lead)==0:
        name = body.get("name","")
        phone = body.get("phone","")
        email = body.get("email","")
        address = body.get("address","")
        subject = body.get("subject","")
        message = body.get("message","")
    else:
        name = lead.get("name","")
        phone = lead.get("phone","")
        email = lead.get("email","")
        address = lead.get("address","")
        subject = lead.get("subject","")
        message = lead.get("message","")

    if len(name)+len(phone)+len(email)+len(address)+len(subject)+len(message)==0:
        return_message = {
                "message":"No name+phone+email+address+subject+message in json is attached to the event",
                "statuscode":"400"
            }
        print(return_message)
        return return_message

    website_lead_topic = os.environ.get('website_lead_topic')

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
            Subject=subject,
            Message=text_body
        )

        message = {
            "message": f"Email sent! Message Response: {json.dumps(response)}",
        }
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(message)
        }
    except ClientError as e:
        return_message = {
                "message":f"SNS Email Error: {e}",
                "statuscode":"300"
            }
        print(return_message)
        return return_message
    


#######################################
