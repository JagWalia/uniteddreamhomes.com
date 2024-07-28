from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_iam as iam,
    CfnOutput,
    CfnResource,
    aws_apigateway as apigateway,
)

from constructs import Construct

class BackendUdhStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        config = kwargs.pop("config")
        super().__init__(scope, id, **kwargs)

        Account = config['stage-setting']['aws']['account']
        Region = config['stage-setting']['aws']['region']
        stack = config['stack']
        stage = config['stage']

        # vpc_id = config['stage-setting']['aws']['vpc_id']
        # allowed_ports = config['stage-setting']['aws']['allowed_ports']

        # no_ingress_security_group = config['stage-setting']['aws']['no_ingress_security_group']
        # private_subnets = config['stage-setting']['aws']['private_subnets']
        # private_subnet = []
        # for a in private_subnets:
        #     private_subnet.append(str(a))

        website_email_contact =  config['stage-setting']['aws']['website_email_contact']
        website_email_contacts = []
        for a in website_email_contact:
            website_email_contacts.append(str(a))

        
        # storing environment variable
        env_variables={}
        for item in config['stage-setting']:
            for v in config['stage-setting'][item]:
                env_variables[v] = str(config['stage-setting'][item][v])

        # env_variables = {
        #     "account": Account,
        #     "region": Region

        # }

        allowedAccounts = config['stage-setting']['aws']['allowedAccounts']
        allowedAccountsArn_aws = []
        for a in allowedAccounts:
            allowedAccountsArn_aws.append("arn:aws:iam::" + str(a) + ":root")
        # print("AllowedAccounts_aws:" + str(allowedAccountsArn_aws))

        allowedIPs = config['stage-setting']['aws']['allowedIPs']
        allowedIPs_aws = []
        if allowedIPs:
            for a in allowedIPs:
                allowedIPs_aws.append(str(a))

        allowed_urls = config['stage-setting']['aws']['allowed_url']
        allowed_urls_aws = []
        if allowed_urls:
            for a in allowed_urls:
                allowed_urls_aws.append(str(a))

        # vpc_custom = ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)

        # subnet1 = ec2.Subnet.from_subnet_id(
        #     self, f'subnet1-{stack}', private_subnet[0])
        # subnet2 = ec2.Subnet.from_subnet_id(
        #     self, f'subnet2-{stack}', private_subnet[1])
        # subnet3 = ec2.Subnet.from_subnet_id(
        #     self, f'subnet3-{stack}', private_subnet[2])

        # no_ingress_security_group = ec2.SecurityGroup.from_security_group_id(self, f'sg-{stack}',
        #                                                                      security_group_id=no_ingress_security_group)
        # private_subnet_selection = ec2.SubnetSelection(subnets = [subnet1, subnet2, subnet3])

        # # To add more then 1 SQL PORTS to work with INAP/DR
        # for allowed_port in allowed_ports:
        #     no_ingress_security_group.add_ingress_rule(
        #         ec2.Peer.any_ipv4(), ec2.Port.tcp(allowed_port), f'Port {allowed_ports}')

        website_bucket = config['stage-setting']['aws']['website_bucket']

        # Create an SNS topic
        website_lead_topic = sns.Topic(self, f'{stack}-lead-topic', display_name=f'{stack}-lead-topic')

        # Add an email subscription to the SNS topic
        for website_email_contact in website_email_contacts:
            email_subscription = subscriptions.EmailSubscription(website_email_contact)
            website_lead_topic.add_subscription(email_subscription)

        env_variables['website_lead_topic'] = website_lead_topic.topic_arn

        # # lambda to read secret manager
        # lambda_get_secrets = _lambda.Function(
        #     self,
        #     f'{stack}-get-secrets',
        #     function_name=f"{stack}-get-secrets",
        #     role=assume_role,
        #     runtime=aws_lambda.Runtime.PYTHON_3_8,
        #     code=aws_lambda.Code.from_asset(
        #         path='lambda-functions/get-secrets'
        #     ),
        #     handler='start.handler',
        #     # layers = [lambdaLayer],
        #     timeout=core.Duration.seconds(30),
        #     allow_public_subnet=True,
        #     vpc=vpc_custom,
        #     # vpc_subnets=ec2.SubnetSelection(subnets=vpc_custom.select_subnets(
        #     #     subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT).subnets),
        #     vpc_subnets=private_subnet_selection,
        #     security_groups=[no_ingress_security_group],
        #     environment={
        #         **env_variables
        #     }
        # )

        email_lambda  = _lambda.Function(
            self,
            f"{stack}-send-email-lead",
            function_name=f"{stack}-send-email-lead",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset(
                path='lambda-functions/send-email-lead-udh'
            ),
            handler='start.handler',
            timeout=Duration.seconds(30),
            environment={
                **env_variables
            }
        )

        # Grant Lambda permission to publish to the SNS topic
        website_lead_topic.grant_publish(email_lambda)

        api_resource_policy = iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        principals=[iam.AnyPrincipal()],
                        actions=['execute-api:Invoke'],
                        resources=["*"],
                        effect= iam.Effect.ALLOW,
                        conditions= {
                            "StringLike": {
                                "aws:Referer": allowed_urls_aws
                            }
                        }
                    )
                ]
            )

        # Create an API Gateway
        api = apigateway.RestApi(self, f"{stack}-api",
            rest_api_name=f"{stack}-api",
            description=f"{stack}-api",
            policy=api_resource_policy
        )

         # Add CORS options to the resource
        def add_cors_options(api_resource):
            api_resource.add_method(
                'OPTIONS',
                apigateway.MockIntegration(
                    integration_responses=[{
                        'statusCode': '200',
                        'responseParameters': {
                            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization'",
                            'method.response.header.Access-Control-Allow-Origin': "'*'",
                            'method.response.header.Access-Control-Allow-Methods': "'OPTIONS,POST,GET'"
                        }
                    }],
                    passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
                    request_templates={"application/json": "{\"statusCode\": 200}"}
                ),
                method_responses=[{
                    'statusCode': '200',
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Headers': True,
                        'method.response.header.Access-Control-Allow-Origin': True,
                        'method.response.header.Access-Control-Allow-Methods': True
                    }
                }]
            )

        # Create a resource and method
        resource = api.root.add_resource("sendLeadMessage")

        # Add CORS to the resource if it does not exist
        try:
            add_cors_options(resource)
        except Exception as e:
            print(f"CORS options already exist: {e}")

        resource.add_method("POST", apigateway.LambdaIntegration(email_lambda))



        # Grant API Gateway access to the Lambda function
        email_lambda.add_permission(f"{stack}-ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=api.arn_for_execute_api()
        )

        api_deployment = apigateway.CfnDeployment(self, f'{stack}-deployment',
            rest_api_id=api.rest_api_id,
            stage_name=stage
        )


        # api_resource_policy = iam.PolicyDocument(
        #         statements=[
        #             iam.PolicyStatement(
        #                 principals=[iam.AnyPrincipal()],
        #                 actions=['execute-api:Invoke'],
        #                 resources=[api.arn_for_execute_api()],
        #                 effect= iam.Effect.ALLOW,
        #                 conditions= {
        #                     "StringLike": {
        #                         "aws:Referer": allowed_urls_aws
        #                     }
        #                 }
        #             )
        #         ]
        #     )


