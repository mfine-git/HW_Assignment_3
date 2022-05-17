# Homework Assignement: DevOps Craft - Photo Processing app. 

## <ins>Guidelines:</ins>
 - Use GitOps to deploy this (Jenkins or CodeBuild & CodePipelines in AWS) 
 - Business problem (short summary)
 - Solution design - architecture diagram (incorporating operational excellence, security, reliability, performance efficiency and cost optmization pillars in your solution)
 - Demonstrate end-to-end solution
 - Issues encountered during the implementation (highlight steps taken to isolate the fault and resolve the issue)
 - Lessons learned
 - Enhancement opportunities
 - Use username suffix in all resources you create (i.e. username-lambda, s3://username-image-bucket-input,  s3://username-image-bucket-output)

## Photo processing application.

### ***<ins>Background:</ins>***
Suppose you have a photo-sharing  application. People use your app to upload photos and the app stores these photos in an Amazon S3 bucket.
Then, your app creates thumbnail versions of each user's photos and displays them on the user's profile page.
In this scenario you may choose to create a Lambda function that creates a thumbnail automatically.

### ***<ins>Task:</ins>***
- A) Develop Lambda function code that can read the photo object from the S3 bucket, create a thumbnail version and save it to another S3 bucket.
- B) On failure
  1) Notify the Operational Center (current yourself) via email.
  2) Log failure detail in S3 bucket
- C) On success, update the File Upload Catalog (table) in RDS capturing following details:
  1. File upload date
  2. File upload time
  3. File name
  4. Original file size
  5. Thumbnail size 
- D) Create static website for resized images

### ***<ins>Success criteria:</ins>***
1) Upload empty file (not photo) into S3 bucket (simulate failure in image processing)
   - A) Get an email on the failure.
2) Upload photo into S3 bucket
   - A) Get a resized image version of the photo in output bucket (result)
   - B) Query database and get result of 5 smallest thumbnails. This should include all details mentioned in task C
3) Access resized photo from the world using browser
4) Create a private GitHub repository and push the code there - make sure you use comments and documentation in your code. Include all files/commands/scripts/etc. you used to accomplish the task.
5) Share the git repository permissions with [seladnac@gmail.com](seladnac@gmail.com) and [a4a-secrnd-devops-aaaacfomf7qfn26nvrelz3a5f4@intuit.org.slack.com](a4a-secrnd-devops-aaaacfomf7qfn26nvrelz3a5f4@intuit.org.slack.com)


# ***<ins>How to use this project</ins>***

## ***Prerequisites (Predeployed AWS infrastructure):***
`IMPORTANT: all resources in this project must be created in "us-east-1" region to prevent unexpected behaviour.`

1) <ins>VPC (Virtual Private Cloud)</ins>
   - A) VPC > Your VPCs > Create VPC (Default VPC, VPC ID: vpc-XXXX. Note: may cause security issues)
   - B) VPC > Subnets > Create Subnet (6 Default Subnets, Subnet IDs: subnet-XXXX, subnet-YYYY, ... )
   - C) VPC > Security Groups > Create Security Group (Default Security Group: sg-XXXX )
   - D) VPC > Security Groups > Default Security Group > Edit inbound/outbound rules > Add rule (Added Inbound and Outbound Security group rules for All traffic from Anywhere for All ports. Note: may cause security issues)
   - E) VPC > Endpoints > Create endpoint (to access AWS services in VPC)
        - intuit-VPC-endpoint-S3, Service name: com.amazonaws.us-east-1.s3, Gateway - for S3
        - intuit-VPC-endpoint-SM, Service name: com.amazonaws.us-east-1.secretsmanager, Interface - for Secrets Manager
#### *Related links:* 
- [https://stackoverflow.com/questions/39779962/access-aws-s3-from-lambda-within-vpc](https://stackoverflow.com/questions/39779962/access-aws-s3-from-lambda-within-vpc)
- [https://aws.amazon.com/blogs/security/how-to-connect-to-aws-secrets-manager-service-within-a-virtual-private-cloud/#:~:text=Open%20the%20Amazon%20VPC%20console,amazonaws.](https://aws.amazon.com/blogs/security/how-to-connect-to-aws-secrets-manager-service-within-a-virtual-private-cloud/#:~:text=Open%20the%20Amazon%20VPC%20console,amazonaws.)

2) <ins>IAM (Identity and Access Management)</ins>
   - IAM > Roles > Create Role > AWS service > Lambda > next > Add policies >  Create role
   - Added "intuit-s3tos3" role for Lambda with following Permissions policies:
     - AmazonS3FullAccess (Allows access to S3)
     - SecretsManagerReadWrite (Allows access to Secret Manager)
     - AWSXRayDaemonWriteAccess (Allows access to Cloudwatch)
     - AWSLambdaBasicExecutionRole (Allows access to Cloudwatch)
     - AWSLambdaVPCAccessExecutionRole (Allows access to RDS)

3) <ins>S3 (Simple Storage Service)</ins> 
   - S3 > Block Public Access settings for this account > Unblock all public access (to allow Static website hosting).
   - A) S3 > Buckets > Create bucket name: intuit-image-bucket-input (not public) - for uploaded files.
   - B) S3 > Buckets > Create bucket name: intuit-log-bucket (not public) - for non-image file's failure logs 
   - C) S3 > Buckets > Create bucket name: intuit-image-bucket-output (Static website hosting, Publicly accessible, has Bucket website endpoint) - for thumbnailed images and static web hosting.
     - (Index document: index.html > Error document: error.html)
    ```
    Bucket policy:
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::intuit-image-bucket-output/*"
            }
        ]
    }
    ```
  
4) <ins>RDS (Relational Database Service)</ins> 
   - RDS > Create database > Standard create > MySQL > DB instance identifier: intuit-db-identifier > Initial database name: intuit_database  > Master username: XXXX > Master password: XXXX > Database port: 3306 > Default VPC > All related subnet groups > Default security group

5) <ins>Secret Manager</ins> 
   - Secret Manager > Store new secret > Credentials for Amazon RDS database > Encryption key: aws/secretsmanager > Secret name: RDSsecret

## ***IMPLEMENTATION:***

### <ins>Static Web Server:</ins>  
  1. From Project GitHub repo > Upload all content in "/static_web_server/" into root of S3 "intuit-image-bucket-output"
  2. Access Web Server Endpoint from global browser via:
     - [Main page](http://intuit-image-bucket-output.s3-website-us-east-1.amazonaws.com/)
     - Download single image using following pattern: http://intuit-image-bucket-output.s3-website-us-east-1.amazonaws.com/<image_name>
     - [Error page](http://intuit-image-bucket-output.s3-website-us-east-1.amazonaws.com/<non_existent_image)
#### *Related links:* 
 - [https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteAccessPermissionsReqd.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteAccessPermissionsReqd.html)
 - [https://medium.com/@kyle.galbraith/how-to-host-a-website-on-s3-without-getting-lost-in-the-sea-e2b82aa6cd38](https://medium.com/@kyle.galbraith/how-to-host-a-website-on-s3-without-getting-lost-in-the-sea-e2b82aa6cd38)
 - [https://docs.aws.amazon.com/AmazonS3/latest/userguide/HostingWebsiteOnS3Setup.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/HostingWebsiteOnS3Setup.html)

### <ins>Lambda function:</ins>  
 - In this project, we create AWS Lambda function that triggered upon receiving the file in the S3 source bucket. Lambda will resize and upload image-format files to another S3 bucket. In case the uploaded file is not image, related failure-log will be created in third bucket.  
 - Lambda will update RDS table with required image parameters.
 - Lambda function (Runtime: Python3.8) will be deployed using Jenkins. Process logs are stored and can be monitored in CloudWatch.
#### *Related links:* 
 - [https://towardsdatascience.com/how-to-create-an-object-detection-solution-with-aws-and-python-8b20690686c5](https://towardsdatascience.com/how-to-create-an-object-detection-solution-with-aws-and-python-8b20690686c5)
 - [https://docs.aws.amazon.com/lambda/latest/dg/services-rds-tutorial.html](https://docs.aws.amazon.com/lambda/latest/dg/services-rds-tutorial.html)
 - [https://pynative.com/python-mysql-execute-parameterized-query-using-prepared-statement/](https://pynative.com/python-mysql-execute-parameterized-query-using-prepared-statement/)

### <ins>Jenkins (tested on ver 2.332.3, Window10):</ins>
- Configure:
  - GitHub hook with project repository 
  - Global credentials "jenkins-integration" in "username, password" format.
- Open Jenkins in browser: http://localhost:8080/
- Create new item > name: intuit_pipeline > Freestyle project > OK > 
- Source Code Management > Git: V > Repository URL: https://github.com/mfine-git/Photo_Processing_App > Credentials: XXXX > Branch Specifier: */main 
- Build > Add build step > AWS Lambda deployment > AWS Access Key Id: XXXX > AWS Secret Key: XXXX > AWS Region: us-east-1 > Function Name: intuit-lambda-jenkins > Description: Managed by Jenkins > Role: arn:aws:iam::XXXX:role/intuit-s3tos3 > Artifact Location: lambda_function.zip > Handler Name: lambda_function.lambda_handler > Memory Size: 128 > Timeout: 5 > Runtime: python3.8 > Update Mode: Code and Configuration > Publish new version: V > Subnets: all 6 (subnet-XXXX,...) > Security Groups: sg-XXXX > Save
- Build Now > Build #X > Console Ouptut
#### *Related links:* 
 - [https://plugins.jenkins.io/aws-lambda/](https://plugins.jenkins.io/aws-lambda/)
 - [https://www.middlewareinventory.com/blog/deploy-aws-lambda-jenkins/](https://www.middlewareinventory.com/blog/deploy-aws-lambda-jenkins/)

### <ins>Lambda post-deployment:</ins>
 - After lamda deployed, following configurations need to be added manualy (Known gap. May be covered via using AWS SAM framework. See AWS_SAM_file.yaml in project folder)
   1. S3 bucket  trigger
      - Lambda > Functions > intuit-lambda-jenkins > Add trigger > S3 > Bucket: intuit-image-bucket-input > Event type: All objects create events > Recursive invocation: V > Add
   2. Layers (ZIP archive that contains libraries). PyMysql and Pillow in current setup.
      - Lambda > Layers > Add a layer > Specify an ARN: arn:aws:lambda:us-east-1:770693421928:layer:Klayers-python38-Pillow:15 > Add
      - Lambda > Layers > Add a layer > Specify an ARN: arn:aws:lambda:us-east-1:770693421928:layer:Klayers-python38-PyMySQL:4 > Add
#### *Related links:*
 - [https://github.com/keithrozario/Klayers](https://github.com/keithrozario/Klayers)
 - [https://stackoverflow.com/questions/57197283/aws-lambda-cannot-import-name-imaging-from-pil](https://stackoverflow.com/questions/57197283/aws-lambda-cannot-import-name-imaging-from-pil)
 - [https://github.com/keithrozario/Klayers/blob/master/deployments/python3.8/arns/us-east-1.csv](https://github.com/keithrozario/Klayers/blob/master/deployments/python3.8/arns/us-east-1.csv)

### <ins>Configure e-mail notificaions (alarm):</ins>
 - CloudWatch > Log groups > /aws/lambda/intuit-lambda-jenkins: V > Actions > edit retention settings > 1 week (example) > Save.
 - CloudWatch > Log groups > /aws/lambda/intuit-lambda-jenkins > Metric filetrs > Create metric filter > Filter pattern: "Unprocessable Entity: input object must be a jpg or png." > Next > Filter name: intuit_unprocessable_entity > Metric namespace: intuit_namespace > Metric name: intuit_metric > Metric value: 1 > Default value: 0 > Next > Create metric filter.
 - Upload "not image" file to S3 "intuit-image-bucket-input" in order to create Event in Log stream.
 - CloudWatch > All alarms > Create alarm > Select metric > intuit_namespace > Metrics with no dimensions > intuit_metric: V > Select metric > Statistics: Maximum, Period: 1 min > Static > Greater > than: 0 > Missing data treatment: Treat missing data as good > Next > Alarm state trigger: In alarm > Select an SNS topic: Create new topic: intuit_sns_topic > emal: abc@def.com > Create topic > Next > Alarm name: intuit_alarm > Alarm description: Unprocessable Entity > Next > Create alarm.
 - Confirm Subscription to "intuit_sns_topic" SNS topic via email.
 - Upload "not image" file to S3 "intuit-image-bucket-input".

### <ins>Success criteria:</ins>
 - Upload all context  of "/upload_files/" folder (github project) to "intuit-image-bucket-input" and find thumbnailed versions in "intuit-image-bucket-output". 
 - See failure logs for non-image files in "intuit-log-bucket". 
 - Check e-mail notification. 
 - Query RDS "File_Upload_Catalog" table
   - MySQL Workbench 8.0 CE > Database > Manage connection > New > Connection name: intuit-db-identifier > Host name: XXXXX.XXXXX..us-east-1.rds.amazonaws.com > Port: 3306 > Username: XXXX > Password: XXXX > Close.
   - Query database and get results that include all details mentioned in task C.
     - (Database > Connect to database > OK > intuit_database > Tables > File_Upload_Catalog > Right click: Select Rows - Limit 1000)
   - Query database and get result of 5 smallest thumbnails. This should include all details mentioned in task C.
     - Execute: `SELECT * FROM intuit_database.File_Upload_Catalog order by Thumbnail_size DESC LIMIT 5;`
       - (Known gap: current query showing recognized Thumbnail size value as a text (can be solved by correting data type from varchar(255) to int in Lambda function)
   - Note: Drop "File_Upload_Catalog" table to clean up upload history in RDS
#### *Related links:*  
 - [https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ConnectToInstance.html](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ConnectToInstance.html)














