import boto3
import os
import shutil
from zipfile import ZipFile

lambdaName               = os.getenv('LAMBDA_NAME', 'qa-failed-pagares-worker')
roleArn                 = os.getenv('ROLE_ARN', 'arn:aws:iam::787437540378:role/QANegoziaAdmin')
pathBuild               = os.getenv('PATH_BUILD', './dist')
sessionName             = os.getenv('SESSION_NAME', 'lambdaDeploy')

def make_zip_file_bytes(path):
    zip_file = os.path.abspath(path)
    print("generating zip file with dir...", zip_file)
    shutil.make_archive(zip_file, 'zip', zip_file)
    if not os.path.isfile(zip_file + '.zip'):
        raise ValueError('Lambda file zip does not exist: {0}'.format(pathBuild))

    print("file zip to upload...", zip_file + '.zip')
    with open(zip_file + '.zip', 'rb') as f:
        file_content = f.read() # Read whole file in the file_content string
    return file_content

def updateContentLambda(client, lambdaName, pathBuild):
    if not os.path.isdir(pathBuild):
        raise ValueError('Lambda directory does not exist: {0}'.format(pathBuild))

    response = client.update_function_code(
        FunctionName = lambdaName,
        ZipFile = make_zip_file_bytes(path=pathBuild),
    )

    print("Lambda updated...", response['FunctionName']) if response['FunctionName'] == lambdaName else exit(1)

def assumeRole(roleArn, sessionName):
    client = boto3.client('sts')
    response = client.assume_role(RoleArn=roleArn, RoleSessionName=sessionName)
    session = boto3.Session(
        aws_access_key_id     = response['Credentials']['AccessKeyId'],
        aws_secret_access_key = response['Credentials']['SecretAccessKey'],
        aws_session_token     = response['Credentials']['SessionToken']
    )
    return session


def main():
    session = assumeRole(roleArn, sessionName)
    lambdaClient = session.client('lambda')

    updateContentLambda(lambdaClient, lambdaName, pathBuild)

if __name__ == "__main__":
    main()
