import boto3
import os
import time
import mimetypes

s3BucketUri             = os.getenv('S3_BUCKET_URI')
cloudFrontClusterId     = os.getenv('CLOUD_FRONT_CLUSTER_ID')
roleArn                 = os.getenv('ROLE_ARN')
pathBuild               = os.getenv('PATH_BUILD', './dist')
sessionName             = os.getenv('SESSION_NAME', 's3Deploy')


def createInvalidation(client, cloudFrontClusterId):
    res = client.create_invalidation(
        DistributionId=cloudFrontClusterId,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': [
                    '/*'
                ]
            },
            'CallerReference': str(time.time()).replace(".", "")
        }
    )
    print("Invalidation created successfully with Id: " + res['Invalidation']['Id'])

def updateContentBucket(client, s3BucketUri, pathToCopy):
    for root, dirs, files in os.walk(pathToCopy):
        for file in files:
            local_path = os.path.join(root, file)
            s3_path = os.path.relpath(local_path, pathToCopy)
            mimetype, _ = mimetypes.guess_type(local_path)
            print("Uploading...", s3_path)
            client.upload_file(local_path, s3BucketUri, s3_path, ExtraArgs={"ContentType": mimetype, "ACL": 'public-read'})

    list_objects = client.list_objects_v2(Bucket=s3BucketUri)
    print("Uploaded files...", list_objects['KeyCount'])

def deleteContentBucket(client, s3BucketUri):
    list_objects = client.list_objects_v2(Bucket=s3BucketUri)
    
    if (list_objects['KeyCount'] == 0): return
    objects_to_delete = []
    for object in list_objects['Contents']:
        objects_to_delete.append({"Key": object['Key']})
   
    print("Deleting", len(objects_to_delete), "files...")
    client.delete_objects(
        Bucket=s3BucketUri,
        Delete={
            'Objects': objects_to_delete
        }
    )
    print("Files successfully deleted...")


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
    s3Client = session.client('s3')
    cfClient = session.client('cloudfront')

    deleteContentBucket(s3Client, s3BucketUri)
    updateContentBucket(s3Client, s3BucketUri, pathBuild)
    createInvalidation(cfClient, cloudFrontClusterId)


if __name__ == "__main__":
    main()
