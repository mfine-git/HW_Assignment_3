from __future__ import print_function
import boto3
import botocore
import json
import os
import sys
import logging
import uuid
from PIL import Image
import PIL.Image
import pymysql
import base64
from botocore.exceptions import ClientError

s3_client = boto3.client('s3', 'us-east-1', config=botocore.config.Config(s3={'addressing_style':'path'}))
img_formats = ["jpg", "jpeg", "png"]
secret_name = "RDSsecret"
reduction_factor = 3 # define how image size wiil be reducted


def resize_image(image_path, resized_path, reduction_factor):
    # converting uploaded image to thumbnail
    with Image.open(image_path) as image:
        image.thumbnail(tuple(x / reduction_factor for x in image.size))
        image.save(resized_path)


def get_secret(secret_name):
    # pull secret from Secret Manager
    region_name = "us-east-1"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret_object = get_secret_value_response['SecretString']
        else:
            secret_object = base64.b64decode(get_secret_value_response['SecretBinary'])
    return json.loads(secret_object)


def rds_update(secret_object, par1, par2, par3, par4, par5):
    # Update RDS "File_Upload_Catalog" table
    rds_host  = secret_object['host']
    name = secret_object['username']
    password = secret_object['password']
    db_name = secret_object['dbname']
    try:
        conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    except pymysql.MySQLError as e:
        print("ERROR: Unexpected error: Could not connect to MySQL instance.")
        print(e)
        sys.exit()    
    item_count = 0
    print("Connecting to MySQL instance.")
    with conn.cursor() as cur:
        print("Creating table.")
        cur.execute("create table if not exists File_Upload_Catalog ( ID  int NOT NULL AUTO_INCREMENT, File_upload_date varchar(255) NOT NULL, File_upload_time varchar(255) NOT NULL, File_name varchar(255) NOT NULL, Original_file_size varchar(255) NOT NULL, Thumbnail_size varchar(255) NOT NULL, PRIMARY KEY (ID))")
        print("Inserting data.")
        sql_insert_query = """ insert into File_Upload_Catalog (File_upload_date, File_upload_time, File_name, Original_file_size, Thumbnail_size) values (%s,%s,%s,%s,%s)""" 
        tuple_pars = (par1, par2, par3, par4, par5)
        cur.execute(sql_insert_query, tuple_pars)
        conn.commit()
        print("Querying table.")
        cur.execute("select * from File_Upload_Catalog")
        for row in cur:
            item_count += 1
            print(row)
    conn.commit()
    print("RDS table updated.")
    return "Added %d items from RDS MySQL table" %(item_count)


def lambda_handler(event, context):
    # Main
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        bucket_output = "intuit-image-bucket-output"
        bucket_logs_output = "intuit-log-bucket"
        failure_message = "Unprocessable Entity: input object must be a jpg or png."
        
        # parameters to be appended to RDS "File_Upload_Catalog" table 
        File_upload_date = record['eventTime'][0:10]
        print("File_upload_date:", File_upload_date)
        File_upload_time = record['eventTime'][11::]
        print("File_upload_time:", File_upload_time)
        File_name = record['s3']['object']['key']
        print("File_name:", File_name)
        Original_file_size = record['s3']['object']['size']
        print("Original_file_size:", Original_file_size)
        
        # Buckets info
        print("Input bucket name:", bucket)
        print("Output bucket name:", bucket_output)
        print("Log bucket name:", bucket_logs_output)
        
        # if the input object is not an image, do not attempt processing
        if not any(format in File_name.lower() for format in img_formats):
            # create and upload failure log to logs bucket
            log_file = open('/tmp/' + File_name + '.txt', 'w+')
            log_file.write(str(failure_message))
            log_file.close()    
            s3_client.upload_file('/tmp/' + File_name + '.txt', bucket_logs_output, 'failure-' + File_name)
            
            # write failure-status to cloudwatch log stream
            print(File_name, "Unprocessable Entity: input object must be a jpg or png.")
            return {
              "statusCode": 422,
              "body" : json.dumps("Unprocessable Entity: input object must be a jpg or png.")
            }
            
        # if the input object is an image, proceed
        else:
            download_path = '/tmp/{}{}'.format(uuid.uuid4(), File_name)
            print("Log download_path name:", download_path)
            upload_path = '/tmp/resized-{}'.format(File_name)
            print("Log upload_path name:", upload_path)
            # create source directory
            directory = os.path.dirname(download_path)
            print("Log directory name :", directory)
            if not os.path.exists(directory):
                os.makedirs(directory)
            # create target directory
            targetdirectory = os.path.dirname(upload_path)
            print("Log targetdirectory name :", targetdirectory)
            if not os.path.exists(targetdirectory):
                os.makedirs(targetdirectory)
            with open(download_path, 'wb') as data:
                s3_client.download_fileobj(bucket, File_name, data)
            resize_image(download_path, upload_path, reduction_factor)
            
            # get thumbnail size (to be appended to RDS "File_Upload_Catalog" table) 
            file_stats = os.stat(upload_path)
            Thumbnail_size = file_stats.st_size
            print("Thumbnail_size:", Thumbnail_size)            

            # Upload thumbnailed file to output bucket 
            s3_client.upload_file(upload_path, bucket_output, File_name)
            
            # update RDS "File_Upload_Catalog" table
            secret_object = get_secret(secret_name)
            rds_update(secret_object, File_upload_date, File_upload_time, File_name, Original_file_size, Thumbnail_size)
