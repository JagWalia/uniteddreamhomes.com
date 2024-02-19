import os
import sys
import json
import time
from secretmanager import get_secret
import base64

"""
Sample pahyload:
{
    "secret_name":"sql-server-beta"
}
"""

def handler(event: dict, context: dict):
  if 'event' in event:
      if event.get('event') == 'warmup':
          print("Lambda is warm.")
          resp = {"statusCode": 200, "body": event}
          return resp

  try:
    print(f'Event:{event}')
    secret_config = {}
    # if "secret_name" not in event['body']:
    #     secret_config = {"statusCode": 400, "body": "{secret_name} not provided"}
    #     print(secret_config)
    #     return secret_config

    # body = json.loads(event['body'])
    if event['isBase64Encoded']==True:
        base64_string=event['body']
        
        base64_bytes = base64_string.encode("ascii")
        body_string_bytes = base64.b64decode(base64_bytes)
        
        body_string = body_string_bytes.decode("ascii")    
        
        print(f'body string: {body_string}')
    
        if "secret_name" not in body_string:
            secret_config = {"statusCode": 400, "body": "{secret_name} not provided"}
            print(secret_config)
            return secret_config
    
        body = json.loads(body_string)
    else:
        body = json.loads(event['body'])

    secret_name = body['secret_name']
    print(f"Reading Secret Manager for {secret_name}")
    secret = get_secret(secret_name)

    #returning the response only
    show_secret(secret)
    secret_config = {"statusCode": 200, "body": json.dumps(secret)}
    print(f'returning: {secret_config}')

    return secret_config
  except Exception as ex:
      print(ex)
      raise (ex)

def show_secret(secret: dict):

    for key in secret:
        print(f'{key}: {secret[key]}')
