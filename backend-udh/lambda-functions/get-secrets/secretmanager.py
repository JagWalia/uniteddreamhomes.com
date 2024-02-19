import logging
from base64 import b64decode, b64encode
import json
import boto3



def get_secret(secret_name: str) -> dict:
    """Retrieves Secret from AWS Secret Manager"""

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    print(f'getting secret values for {secret_name}')
    response = client.get_secret_value(
        SecretId=secret_name
    )

    print(f'secret response: {response}')
    if 'SecretString' in response:
        secret = response['SecretString']
    else:
        secret = b64decode(response['SecretBinary'])

    return json.loads(secret)



