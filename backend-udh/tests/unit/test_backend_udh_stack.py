import aws_cdk as core
import aws_cdk.assertions as assertions

from backend_udh.backend_udh_stack import BackendUdhStack

# example tests. To run these tests, uncomment this file along with the example
# resource in backend_udh/backend_udh_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BackendUdhStack(app, "backend-udh")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
