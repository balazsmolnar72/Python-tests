# With this test file I would like to test how to transfer an uploaded file to another cgi process in an ephemeral environment 
# like functions or microservices using the OCI object storage 


#The first part of the code should be used in the sender CGI
# This part will read a file (uploaded file or any file in a filesystem) uploads to OCI Object storage 
# creates a temporary pre-authenticated request url, which can be transferred to another cgi 

#!/usr/bin/env python3

import io
import oci
import datetime

import pandas as pd


file_item=open('Install Base.csv','rb')
file_contents = file_item.read()

print('Balazs:file contents loaded\n')

# Create an in-memory buffer for the file contents
buffer = io.BytesIO(file_contents)

# Set the name of the bucket and the key (filename) for the object
bucket_name = 'Balazs-Test-Bucket'
import random
import string
randomString=''.join(random.choice(string.ascii_letters) for i in range(5))

key = datetime.datetime.now().strftime('%Y%m%d%H%M%S%fZ')+randomString+'Install Base.csv'

# Connect to OCI Object Storage using the default profile
file_path='C:\\Users\\BMOLNAR\\.oci\\config'
config=oci.config.from_file(file_location=file_path)
object_storage = oci.object_storage.ObjectStorageClient(config=config)  # This needs to be done also in the second part if that is in a different scrpt.

# Create the object in the bucket
object_storage.put_object(
    # namespace_name=oci.config.get_config_value_or_default(config,'tenancy'),
    namespace_name=object_storage.get_namespace().data,
    bucket_name=bucket_name,
    object_name=key,
    put_object_body=buffer
)

# Get the URL of the object
region=oci.config.get_config_value_or_default(config,'region')
namespace_name=object_storage.get_namespace().data

# url="https://objectstorage.{}.oraclecloud.com/n/{}/b/{}/o/{}".format(region,namespace_name,bucket_name,key)  # Works only with buckets that has Public access

print((datetime.datetime.now()+ datetime.timedelta(days=1, hours=3)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

create_preauthenticated_request_response = object_storage.create_preauthenticated_request(
    namespace_name=namespace_name,
    bucket_name=bucket_name,
    create_preauthenticated_request_details=oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name=key+'_Request',
        access_type="AnyObjectReadWrite",
        time_expires=(datetime.datetime.now()+ datetime.timedelta(days=1, hours=48)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        bucket_listing_action="Deny",
        object_name=key),
    opc_client_request_id=namespace_name+"EXAMPLE-opcClientRequestId-Value")


# Get the data from response
import urllib.parse
print(create_preauthenticated_request_response.data)
par_id=create_preauthenticated_request_response.data.id
url="https://objectstorage.{}.oraclecloud.com{}{}".format(region,create_preauthenticated_request_response.data.access_uri,urllib.parse.quote(key))

print(url)
print(par_id)

#import urllib.parse
# print('<a href="<your CGI location>?file_location={}&par_id={}">Use this link to invoke</a>'.format(url,urllib.parse.quote(par_id)))

# The second part of the code should be used by the receiving CGI
# This part will read the file from the object storage and delete the file itself and also the preauthenticated request

# Uncomment the following lines if you are using this code in a different
# file:

# import cgi
# import oci
# import pandas as pd
# import urllib.parse

# bucket_name = 'Balazs-Test-Bucket'
# file_path='C:\\Users\\BMOLNAR\\.oci\\config'
# config=oci.config.from_file(file_location=file_path)
# object_storage = oci.object_storage.ObjectStorageClient(config=config)  # This needs to be done also in the second part if that is in a different scrpt.
# 'region=oci.config.get_config_value_or_default(config,'region')
# namespace_name=object_storage.get_namespace().data
# form = cgi.FieldStorage()
# url_unencoded=form['file_location'].value
# filename=url_unencoded.rsplit('/',1)[-1]
# path=url_unencoded.rsplit('/',1)[0]
# url=path+'/'+urllib.parse.quote(filename)
# par_id=form['par_id'].value


df=pd.read_csv(url)
print(df)

#deletes the unused file

object_storage.delete_object(
    namespace_name=namespace_name,
    bucket_name=bucket_name,
    object_name=key
)

# Delete unused preauthenticated request
delete_preauthenticated_request_response = object_storage.delete_preauthenticated_request(
    namespace_name=namespace_name,
    bucket_name=bucket_name,
    par_id=par_id,
    opc_client_request_id=namespace_name+"EXAMPLE-opcClientRequestId-Value")

# Get the data from response
print(delete_preauthenticated_request_response.headers)

