import aws_cdk as core
import aws_cdk.assertions as assertions

from appsec_workshop.appsec_workshop_stack import AppsecWorkshopStack

# example tests. To run these tests, uncomment this file along with the example
# resource in appsec_workshop/appsec_workshop_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AppsecWorkshopStack(app, "appsec-workshop")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
