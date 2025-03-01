"""An AWS Python Pulumi program"""

import os
import glob
import iam
import pulumi
import pulumi_aws as aws
from pulumi import Config

region = aws.config.region
config = pulumi.Config()
custom_stage_name = "example"

##################
## Lambda Function
##################

# Create a Lambda function, using code from the `./app` folder.

# pulumi up -c APP_VERSION=latest
app_version = config.require("APP_VERSION")


if app_version == "latest":
    # find the latest file named `package-*.zip` in the `app/build/packages` folder, using file timestamp
    list_of_files = glob.glob("../app/build/packages/package-*.zip")
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Using latest app version: {latest_file}")
    code = pulumi.FileArchive(latest_file)
else:
    print(f"Using app version: {app_version}")
    code = pulumi.FileArchive(f"../app/build/packages/package-{app_version}.zip")


lambda_func = aws.lambda_.Function(
    "mylambda",
    role=iam.lambda_role.arn,
    runtime="python3.13",
    handler="gen_ai_on_aws.main.handler",
    code=pulumi.FileArchive("../app/build/packages/package-e75ea75_SNAPSHOT.zip"),
)


####################################################################
##
## API Gateway REST API (API Gateway V1 / original)
##    /{proxy+} - passes all requests through to the lambda function
##
####################################################################


# Create a single Swagger spec route handler for a Lambda function.
def swagger_route_handler(arn):
    return {
        "x-amazon-apigateway-any-method": {
            "x-amazon-apigateway-integration": {
                "uri": pulumi.Output.format(
                    "arn:aws:apigateway:{0}:lambda:path/2015-03-31/functions/{1}/invocations",
                    region,
                    arn,
                ),
                "passthroughBehavior": "when_no_match",
                "httpMethod": "POST",
                "type": "aws_proxy",
            },
        },
    }


# Create the API Gateway Rest API, using a swagger spec.
rest_api = aws.apigateway.RestApi(
    "api",
    body=pulumi.Output.json_dumps(
        {
            "swagger": "2.0",
            "info": {"title": "api", "version": "1.0"},
            "paths": {
                "/{proxy+}": swagger_route_handler(lambda_func.arn),
            },
        }
    ),
)

# Create a deployment of the Rest API.
deployment = aws.apigateway.Deployment(
    "api-deployment",
    rest_api=rest_api.id,
)

# Create a stage, which is an addressable instance of the Rest API. Set it to point at the latest deployment.
stage = aws.apigateway.Stage(
    "api-stage",
    rest_api=rest_api.id,
    deployment=deployment.id,
    stage_name=custom_stage_name,
)

# Give permissions from API Gateway to invoke the Lambda
rest_invoke_permission = aws.lambda_.Permission(
    "api-rest-lambda-permission",
    action="lambda:invokeFunction",
    function=lambda_func.name,
    principal="apigateway.amazonaws.com",
    source_arn=deployment.execution_arn.apply(lambda arn: arn + "*/*"),
)

#########################################################################
# Create an HTTP API and attach the lambda function to it
##    /{proxy+} - passes all requests through to the lambda function
##
#########################################################################

http_endpoint = aws.apigatewayv2.Api("http-api-pulumi-example", protocol_type="HTTP")

http_lambda_backend = aws.apigatewayv2.Integration(
    "example",
    api_id=http_endpoint.id,
    integration_type="AWS_PROXY",
    connection_type="INTERNET",
    description="Lambda example",
    integration_method="POST",
    integration_uri=lambda_func.arn,
    passthrough_behavior="WHEN_NO_MATCH",
)

url = http_lambda_backend.integration_uri

http_route = aws.apigatewayv2.Route(
    "example-route",
    api_id=http_endpoint.id,
    route_key="ANY /{proxy+}",
    target=http_lambda_backend.id.apply(lambda targetUrl: "integrations/" + targetUrl),
)

http_stage = aws.apigatewayv2.Stage(
    "example-stage",
    api_id=http_endpoint.id,
    route_settings=[
        {
            "route_key": http_route.route_key,
            "throttling_burst_limit": 1,
            "throttling_rate_limit": 0.5,
        }
    ],
    auto_deploy=True,
)

# Give permissions from API Gateway to invoke the Lambda
http_invoke_permission = aws.lambda_.Permission(
    "api-http-lambda-permission",
    action="lambda:invokeFunction",
    function=lambda_func.name,
    principal="apigateway.amazonaws.com",
    source_arn=http_endpoint.execution_arn.apply(lambda arn: arn + "*/*"),
)

# Export the https endpoint of the running Rest API
pulumi.export(
    "apigateway-rest-endpoint",
    deployment.invoke_url.apply(lambda url: url + custom_stage_name + "/{proxy+}"),
)
# See "Outputs" for (Inputs and Outputs)[https://www.pulumi.com/docs/intro/concepts/inputs-outputs/] the usage of the pulumi.Output.all function to do string concatenation
pulumi.export(
    "apigatewayv2-http-endpoint",
    pulumi.Output.all(http_endpoint.api_endpoint, http_stage.name).apply(
        lambda values: values[0] + "/" + values[1] + "/"
    ),
)
