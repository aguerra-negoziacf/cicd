import boto3
import os
import json

taskDefinitionName = os.getenv('TASK_DEFINITION_NAME')#, 'prod-websocket-td')
clusterName        = os.getenv('CLUSTER_NAME')#, 'ngz-prod-apps')
serviceName        = os.getenv('SERVICE_NAME')#, 'prod-websocket-svc')
newEcrImage        = os.getenv('NEW_ECR_IMAGE')#, '794130475503.dkr.ecr.us-east-1.amazonaws.com/websocket:latest')
delay              = os.getenv('DELAY', 30)
maxAttempts        = os.getenv('MAX_ATTEMPTS', 30)
roleArn            = os.getenv('ROLE_ARN')#, 'arn:aws:iam::200023452677:role/terraform-import-ecs-runner')
sessionName        = os.getenv('SESSION_NAME', 'ecsDeploy')
envNvars           = os.getenv('ENV_VARS')
region             = os.getenv('AWS_REGION', 'us-east-1')


def updateTaskDefinition(client, taskDefinitionName, newEcrImage,
                         clusterName, serviceName):
    taskDefResponse    = client.describe_task_definition(
        taskDefinition = taskDefinitionName
    )
    for container in taskDefResponse['taskDefinition']['containerDefinitions']:
        container['image'] = newEcrImage
        if envNvars is not None:
            data = json.loads(envNvars)
            for environment in data:
                container[environment] = data['environment']
    taskDefRegisterResponse = client.register_task_definition(
        family               = taskDefinitionName,
        containerDefinitions = taskDefResponse['taskDefinition']
                                              ['containerDefinitions'],
        taskRoleArn          = taskDefResponse['taskDefinition']['taskRoleArn'] if "taskDefinition" in taskDefResponse and "taskRoleArn" in taskDefResponse['taskDefinition'] else ''
    )
    revision = (taskDefRegisterResponse['taskDefinition']['revision'])
    client.update_service(
        cluster        = clusterName,
        service        = serviceName,
        taskDefinition = taskDefinitionName + ':' + str(revision)
    )


def waitForServiceUpdate(client, clusterName, serviceName):
    waiter = client.get_waiter('services_stable')
    waiter.wait(
        cluster      = clusterName,
        services     = [serviceName],
        WaiterConfig = {
            'Delay'      : delay,
            'MaxAttempts': maxAttempts
        }
    )


def assumeRole(roleArn, sessionName):
    client = boto3.client('sts', region_name=region)
    response = client.assume_role(RoleArn=roleArn, RoleSessionName=sessionName)
    session = boto3.Session(
        aws_access_key_id     = response['Credentials']['AccessKeyId'],
        aws_secret_access_key = response['Credentials']['SecretAccessKey'],
        aws_session_token     = response['Credentials']['SessionToken'])
    client = session.client('ecs', region_name=region)
    return client


def main():
    client = assumeRole(roleArn, serviceName)
    updateTaskDefinition(client, taskDefinitionName, newEcrImage,
                         clusterName, serviceName)
    waitForServiceUpdate(client, clusterName, serviceName)


if __name__ == "__main__":
    main()
