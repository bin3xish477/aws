import json

def lambda_handler(event, context):
    effect = None

    if event['Authorization'] == 'secureAuthToken':
        effect = 'Allow'
    else:
        effect = 'Deny'
        
    policy_doc = {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": [
                        "arn:aws:execute-api:us-east-1:{accountId}:{apiId}/*/GET/{resource}"
                    ]
                }
            ]
        }
    }
    return policy_doc
