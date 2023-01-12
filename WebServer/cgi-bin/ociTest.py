#!/usr/bin/env python3

import cgi
import io
import oci
import logging as log
import datetime

import ObjectStoragePersistance as OP


log.basicConfig(level=log.INFO)
log.info('Balazs: process started\n')

print("Content-Type: text/html")
print()

# Create a form field storage object to hold the submitted form data
form = cgi.FieldStorage()

# Check if the file field is present in the form data
if 'file' not in form:
    print("Error: no file was uploaded")
    exit()

# Get the file object from the form data
file_item = form['file']

# Check if the file is a normal file or an uploaded file
if not file_item.file:
    print("Error: the file is not an uploaded file")
    exit()

# Read the contents of the file into a bytes object
file_contents = file_item.file.read()

log.info('Balazs:file contents loaded\n')

f = open('test.csv', 'wb')
f.write(file_contents)
f.close()

url,par_id=OP.SaveToObjectStorage('test.csv')


""" # Create an in-memory buffer for the file contents
buffer = io.BytesIO(file_contents)

# Set the name of the bucket and the key (filename) for the object
bucket_name = 'Balazs-Test-Bucket'
key = file_item.filename

# Connect to OCI Object Storage using the default profile
file_path='C:\\Users\\BMOLNAR\\.oci\\config'
log.info('Balazs: config file path:',file_path)
config=oci.config.from_file(file_location=file_path)
object_storage = oci.object_storage.ObjectStorageClient(config=config)

# Create the object in the bucket
object_storage.put_object(
    namespace_name=object_storage.get_namespace().data,
    bucket_name=bucket_name,
    object_name=key,
    put_object_body=buffer
)

# Get the URL of the object
region=oci.config.get_config_value_or_default(config,'region')
namespace_name=object_storage.get_namespace().data

# url="https://objectstorage.{}.oraclecloud.com/n/{}/b/{}/o/{}".format(region,namespace_name,bucket_name,key)  # Works only with buckets that has Public access

create_preauthenticated_request_response = object_storage.create_preauthenticated_request(
    namespace_name=namespace_name,
    bucket_name=bucket_name,
    create_preauthenticated_request_details=oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name=key+'_Request',
        access_type="AnyObjectReadWrite",
        time_expires=(datetime.datetime.now()+ datetime.timedelta(days=1, hours=3)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), # The link will expire within a day 
        bucket_listing_action="Deny",
        object_name=key),
    opc_client_request_id=namespace_name+"EXAMPLE-opcClientRequestId-Value")


# Get the data from response
import urllib.parse
# print(create_preauthenticated_request_response.data)
par_id=create_preauthenticated_request_response.data.id
url="https://objectstorage.{}.oraclecloud.com{}{}".format(region,create_preauthenticated_request_response.data.access_uri,urllib.parse.quote(key)) """

import urllib.parse
print('File is uploaded to an object storage')
print('<a href="{}">click here to download the file from Object Storage</a>'.format(url))
print('<br>')
print('<a href="ociTest1.py?file_location={}&par_id={}">Use this link to invoke</a>'.format(url,urllib.parse.quote(par_id)))

