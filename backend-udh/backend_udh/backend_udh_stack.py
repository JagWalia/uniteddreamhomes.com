
from constructs import Construct
from aws_cdk import App, Stack
import aws_cdk as core
from aws_cdk import (
                     aws_ecs as ecs,
                     aws_ecs_patterns as ecs_patterns, aws_applicationautoscaling as aws_app,
                     aws_events as events, 
                     aws_events_targets as targets, 
                     aws_lambda as aws_lambda,
                     aws_apigateway as aws_apigateway,
                     aws_logs as logs,
                     aws_s3 as s3,
                     aws_s3_notifications as s3_notify,
                     aws_sqs as sqs,
                     aws_lambda_event_sources as lambda_event_source,
                     aws_sns as sns, aws_sns_subscriptions as subscriptions,
                     )
import aws_cdk.aws_iam as iam
import os
import boto3
import json
from aws_cdk import aws_ec2 as ec2

class BackendUdhStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        config = kwargs.pop("config")
        super().__init__(scope, id, **kwargs)

        Account = config['stage-setting']['aws']['account']
        Region = config['stage-setting']['aws']['region']
        stack = config['stack']
        stage = config['stage']

        vpc_id = config['stage-setting']['aws']['vpc_id']
        allowed_ports = config['stage-setting']['aws']['allowed_ports']

        no_ingress_security_group = config['stage-setting']['aws']['no_ingress_security_group']
        private_subnets = config['stage-setting']['aws']['private_subnets']
        private_subnet = []
        for a in private_subnets:
            private_subnet.append(str(a))

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

        vpc_custom = ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)

        subnet1 = ec2.Subnet.from_subnet_id(
            self, f'subnet1-{stack}', private_subnet[0])
        subnet2 = ec2.Subnet.from_subnet_id(
            self, f'subnet2-{stack}', private_subnet[1])
        subnet3 = ec2.Subnet.from_subnet_id(
            self, f'subnet3-{stack}', private_subnet[2])

        no_ingress_security_group = ec2.SecurityGroup.from_security_group_id(self, f'sg-{stack}',
                                                                             security_group_id=no_ingress_security_group)
        # private_subnet_selection = vpc_custom.select_subnets(
        #     subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS) #PRIVATE_WITH_NAT)

        private_subnet_selection = ec2.SubnetSelection(subnets = [subnet1, subnet2, subnet3])

        # To add more then 1 SQL PORTS to work with INAP/DR
        for allowed_port in allowed_ports:
            no_ingress_security_group.add_ingress_rule(
                ec2.Peer.any_ipv4(), ec2.Port.tcp(allowed_port), f'Port {allowed_ports}')

        allowed_url = config['stage-setting']['aws']['allowed_url']
        website_bucket = config['stage-setting']['aws']['website_bucket']
        allowed_ip = "13.226.204.113"

        assume_role = iam.Role(self, f'{stack}-assume',
                               assumed_by=iam.CompositePrincipal(
                                     iam.ServicePrincipal(
                                         'lambda.amazonaws.com'),
                                     iam.ServicePrincipal(
                                         'apigateway.amazonaws.com'),
                                     iam.ServicePrincipal(
                                         'logs.amazonaws.com'),
                                     iam.ArnPrincipal("arn:aws:iam::" + str(Account) + ":root"),
                                     iam.WebIdentityPrincipal("cognito-identity.amazonaws.com")
                               ),
                                # Add necessary permissions for the role to access the API
                                managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess")],                                     
                               role_name=f'{stack}-assume',
                                # managed_policies=
                                #     iam.ManagedPolicy.from_aws_managed_policy_name('AWSLambdaBasicExecutionRole'),

                               inline_policies={'Policies': iam.PolicyDocument(
                                   statements=[
                                       iam.PolicyStatement(
                                           effect=iam.Effect.ALLOW,
                                           actions=[
                                                'execute-api:Invoke'],
                                           resources=[
                                               "arn:aws:execute-api:us-east-1:" +
                                               str(Account) +
                                               ":*",
                                               "arn:aws:s3:::www.uniteddreamhomes.com/*",
                                               "arn:aws:ssm:*:" +
                                               str(Account) +
                                               ":parameter/*"
                                           ]
                                       ),
                                       iam.PolicyStatement(
                                           effect=iam.Effect.ALLOW,
                                           actions=["ec2:CreateNetworkInterface",
                                                    "ec2:DescribeNetworkInterfaces",
                                                    "ec2:DeleteNetworkInterface",
                                                    "ec2:AssignPrivateIpAddresses",
                                                    "ec2:UnassignPrivateIpAddresses",
                                                    "lambda:InvokeFunction",
                                                    "lambda:FullAccess",
                                                    "secretsmanager:GetSecretValue",
                                                    "logs:*",
                                                    "ssm:GetParameter",
                                                    # "s3:*",
                                                    # "sqs:*",
                                                    "sns:*",
                                                    "cloudwatch:*"
                                                    ],
                                           resources=["*"]
                                       ),
                                       iam.PolicyStatement(
                                           effect=iam.Effect.ALLOW,
                                           actions=[
                                                    "s3:PutObject",
                                                    "s3:PutBucketAcl",
                                                    "s3:GetBucketAcl",
                                                    "s3:GetBucketAcl",
                                                    "s3:GetObject"
                                                    # "s3:*",
                                                    # "sqs:*",
                                                    # "sns:*"
                                                    ],
                                           resources=["arn:aws:s3:::www.uniteddreamhomes.com/*"]
                                       )
                                   ]
                               )
                               }
                               )

        api_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    principals=[iam.AnyPrincipal()],
                    actions=['execute-api:Invoke'],
                    resources=['execute-api:/*'],
                    effect= iam.Effect.DENY,
                    conditions= {
                      "NotIpAddress": {
                        "aws:SourceIp": allowedIPs_aws
                      }
                    }
                ),
                iam.PolicyStatement(
                    principals=[iam.AnyPrincipal()],
                    actions=['execute-api:Invoke'],
                    resources=['execute-api:/*'],
                    effect=iam.Effect.ALLOW
                )
            ]
        )

        assume_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"))

        # Attach policies to the IAM role
        assume_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[f"arn:aws:s3:::{website_bucket}/*"]
        ))
        # Create an SNS topic
        website_lead_topic = sns.Topic(self, f'{stack}-lead-topic', display_name=f'{stack}-lead-topic')

        # Add an email subscription to the SNS topic
        for website_email_contact in website_email_contacts:
            email_subscription = subscriptions.EmailSubscription(website_email_contact)
            website_lead_topic.add_subscription(email_subscription)

        env_variables['website_lead_topic'] = website_lead_topic.topic_arn


        # lambda to read secret manager
        lambda_get_secrets = aws_lambda.Function(
            self,
            f'{stack}-get-secrets',
            function_name=f"{stack}-get-secrets",
            role=assume_role,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset(
                path='lambda-functions/get-secrets'
            ),
            handler='start.handler',
            # layers = [lambdaLayer],
            timeout=core.Duration.seconds(30),
            allow_public_subnet=True,
            vpc=vpc_custom,
            # vpc_subnets=ec2.SubnetSelection(subnets=vpc_custom.select_subnets(
            #     subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT).subnets),
            vpc_subnets=private_subnet_selection,
            security_groups=[no_ingress_security_group],
            environment={
                **env_variables
            }
        )

        lambda_send_email_lead_udh = aws_lambda.Function(
            self,
            f"{stack}-send-email-lead-udh",
            function_name=f"{stack}-send-email-lead-udh",
            role=assume_role,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset(
                path='lambda-functions/send-email-lead-udh'
            ),
            handler='start.handler',
            timeout=core.Duration.seconds(30),
            allow_public_subnet=True,
            vpc=vpc_custom,
            vpc_subnets=private_subnet_selection,
            # vpc_subnets=ec2.SubnetSelection(subnets=vpc_custom.select_subnets(
            #     subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT).subnets),
            security_groups=[no_ingress_security_group],
            environment={
                **env_variables
            }
        )

        # lambda_send_email_lead_udh.add_permission("AllowS3BucketAccess",
        #     principal=iam.ServicePrincipal("s3.amazonaws.com"),
        #     source_arn="arn:aws:s3:::www.uniteddreamhomes.com/*"
        # )


        # api_policy = iam.PolicyDocument()

        # Create API Gateway



        api = aws_apigateway.LambdaRestApi(
            self,
            stack+'-api',
            description=f"API Gateway for {stack}",
            handler=lambda_send_email_lead_udh,
            rest_api_name=stack+"-api",
            # public with API Key
            endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
            proxy=False,
            policy=api_policy,
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=[allowed_url],
                allow_methods=["POST"],
                allow_headers=["*"]
            )
        )

        api_gen_lead_resource = api.root.add_resource("gen_lead")

        method_gen_lead = api_gen_lead_resource.add_method("POST",
                        integration=aws_apigateway.LambdaIntegration(
                            handler=lambda_send_email_lead_udh,
                            proxy=True,
                            credentials_role=assume_role,
                            request_templates={"application/json": '{ "statusCode": "200" }'}),
                        api_key_required=True,
                        method_responses=[{
                            # Successful
                            "statusCode": "200",
                            "responseParameters": {
                                "method.response.header.Content-Type": True,
                                "method.response.header.Access-Control-Allow-Headers": False,
                                "method.response.header.Access-Control-Allow-Methods": False,
                                "method.response.header.Access-Control-Allow-Origin": True,
                                "method.response.header.Access-Control-Allow-Credentials": False,
                            },
                        }, {
                            # error
                            "statusCode": "400",
                            "responseParameters": {
                                "method.response.header.Content-Type": True,
                                "method.response.header.Access-Control-Allow-Headers": False,
                                "method.response.header.Access-Control-Allow-Methods": False,
                                "method.response.header.Access-Control-Allow-Origin": True,
                                "method.response.header.Access-Control-Allow-Credentials": False,
                            },
                        }]
                    )

        # api = aws_apigateway.RestApi(
        #     self, f'{stack}-api',
        #     rest_api_name=f'{stack}-api',
        #     description=f"API Gateway for {stack}",
        #     default_cors_preflight_options=aws_apigateway.CorsOptions(
        #         allow_origins=[allowed_url],
        #         allow_methods=["POST"],
        #         allow_headers=["*"]
        #     )
        # )


        # Create Integration for the Lambda function
        # integration = aws_apigateway.LambdaIntegration(
        #     lambda_send_email_lead_udh,
        #     proxy=True
        # )

      
        # # Create API Gateway resource and method
        # api_resource = api.root.add_resource("genlead")

        # api_method = api_resource.add_method(
        #     "POST",
        #     integration,
        #     method_responses=[aws_apigateway.MethodResponse(
        #         status_code="200",
        #         response_models={"application/json": aws_apigateway.Model.EMPTY_MODEL}
        #     )]
        # )   
        
        # Create Deployment Stage
        deployment = aws_apigateway.Deployment(
            self,f'{stack}-api-deploy',
            api=api
        )

        stage_name = stage
        stage = aws_apigateway.Stage(
            self, f'{stack}-api-stage-{stage}',
            deployment=deployment,
            stage_name=stage_name
        )

#############
        # api_key = api.add_api_key(
        #     f'{stack}-api-key', api_key_name=f'{stack}-api-key')
        
        # usage_plan = api.add_usage_plan(
        #     f'{stack}-api-usage-plan', name=f'{stack}-api-usage-plan')

        # usage_plan_stage = usage_plan.add_api_stage(stage=stage)

        api.deployment_stage = stage

        # stage.add_api_key(api_key)

#############
        
       