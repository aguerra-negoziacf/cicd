import boto3
import os
import json

taskDefinitionName = os.getenv('TASK_DEFINITION_NAME')
clusterName        = os.getenv('CLUSTER_NAME')
serviceName        = os.getenv('SERVICE_NAME')
newEcrImage        = os.getenv('NEW_ECR_IMAGE')
delay              = os.getenv('DELAY', 30)
maxAttempts        = os.getenv('MAX_ATTEMPTS', 30)
roleArn            = os.getenv('ROLE_ARN')
sessionName        = os.getenv('SESSION_NAME', 'ecsDeploy')
envNvars           = os.getenv('ENV_VARS')


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
        taskRoleArn          = taskDefResponse['taskDefinition']['taskRoleArn'] or ''
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
    client = boto3.client('sts')
    response = client.assume_role(RoleArn=roleArn, RoleSessionName=sessionName)
    session = boto3.Session(
        aws_access_key_id     = response['Credentials']['AccessKeyId'],
        aws_secret_access_key = response['Credentials']['SecretAccessKey'],
        aws_session_token     = response['Credentials']['SessionToken'])
    client = session.client('ecs')
    return client


def main():
    client = assumeRole(roleArn, serviceName)
    updateTaskDefinition(client, taskDefinitionName, newEcrImage,
                         clusterName, serviceName)
    waitForServiceUpdate(client, clusterName, serviceName)


if __name__ == "__main__":
    main()
