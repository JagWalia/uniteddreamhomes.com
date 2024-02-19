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

    body = json.loads(event["body"])
    lead = body["lead"]

    if "lead" not in body:
        return_message = {
                "message":"No lead json is attached to the event",
                "code":"400"
            }
        print(return_message)
        return return_message

    website_lead_topic = os.environ.get('website_lead_topic')

    
    name = lead.get("name")
    phone = lead.get("phone")
    email = lead.get("email")
    address = lead.get("address")
    subject = lead.get("subject")
    message = lead.get("message")


    # Use boto3 to publish a message to the SNS topic
    sns = boto3.client('sns')

    subject = "New Lead - United Dream Homes Website"
    html_body = f"""
    <html>
        <head></head>
        <body>
            <h2>New Lead Information:</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Address:</strong> {address}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Message:</strong> {message}</p>
        </body>
    </html>
    """
    text_body = f"""
                               New Lead Information: \n
            ---------------------------------------------------------\n
            Name:        {name}    \n
            Phone:       {phone}   \n
            Email:       {email}   \n
            Address:     {address} \n
            Subject:     {subject} \n
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
        return_message = {
                "message":f"Email sent! Message Response: {response}",
                "code":"200"
            }

        print(return_message)
        return return_message
    except ClientError as e:
        return_message = {
                "message":f"SNS Email Error: {e}",
                "code":"400"
            }
        print(return_message)
        return return_message


#######################################
