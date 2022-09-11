import json

def lambda_handler(event, context):
    effect = None
    headers = event['headers']
    
    # this is where you would validate the auth token, for example,
    # from a DynamoDB table
    if headers['Authorization'] == 'secureAuthToken':
        effect = 'Allow'
    else:
        effect = 'Deny'
        
    policy_doc = {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statements": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    # don't forget to substitute the insert the accountId, apiId, and resource
                    "Resource": "arn:aws:execute-api:us-east-1:{accountId}:{apiId}/*/GET/{resource}"
                }
            ]
        }
    }
    return policy_doc
