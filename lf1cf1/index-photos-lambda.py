import json
import urllib.parse
import boto3
import datetime
import requests
import logging


print('Loading function')

s3 = boto3.client("s3", "us-east-1")
open_search_url = "https://search-photos-b4z3pxsk23qaueyus6uwmqbhmq.us-east-1.es.amazonaws.com/photos/_doc"
rekognition = boto3.client("rekognition", "us-east-1")

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    # key = event['Records'][0]['s3']['object']['key']

    # # Replace '+' with spaces and then decode URL-encoded characters
    # key = key.replace('+', ' ').encode('utf-8').decode('urldecode')
    
    labels = []
    
    custom_labels = ""
    try:
        log=s3.head_object(Bucket=bucket, Key=key)["ResponseMetadata"]
        print(log)
        
        custom_labels_json = s3.head_object(Bucket=bucket, Key=key)["ResponseMetadata"]["HTTPHeaders"]
        print(custom_labels_json)
        if "x-amz-meta-customlabels" in custom_labels_json:
            custom_labels = custom_labels_json["x-amz-meta-customlabels"]
            if custom_labels.strip() != "":
                for elm in custom_labels.split(","):
                    labels.append(elm.strip())
    except Exception as e:
        print("ERRoR:", e)
        raise e
    
    print("Custom Labels: ", custom_labels)
    print("Labels:", labels)
    try:
        response = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=10,
            MinConfidence=90,
        )
        
        
        if response["Labels"]:
            for label in response["Labels"]:
                name = label["Name"]
                labels.append(name)
        print(f"labels are {labels}")
        to_post = {
            "objectKey": key,
            "bucket": bucket,
            "createdTimeStamp": str(datetime.datetime.now()),
            "labels": labels,
        }
        print("to_post:  ",to_post)
        r = requests.post(
            url=open_search_url,
            auth=("admin","photosAdmin@12"),
            json=to_post,
        )
        print(r.text)
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
