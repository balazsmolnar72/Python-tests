#!/usr/bin/env python3

import cgi
import io
import oci
import logging as log

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

# Create an in-memory buffer for the file contents
buffer = io.BytesIO(file_contents)

# Set the name of the bucket and the key (filename) for the object
bucket_name = 'Balazs-Test-Bucket'
key = file_item.filename

# Connect to OCI Object Storage using the default profile
file_path='C:\\Users\\BMOLNAR\\.oci>'
log.info('Balazs: config file path:',file_path)
config=oci.config.from_file(file_location=file_path)
object_storage = oci.object_storage.ObjectStorageClient(config=config)

# Create the object in the bucket
object_storage.put_object(
    namespace_name=oci.config.get_config().get('tenancy'),
    bucket_name=bucket_name,
    object_name=key,
    data=buffer
)

# Get the URL of the object
url = object_storage.get_object_url(
    namespace_name=oci.config.get_config().get('tenancy'),
    bucket_name=bucket_name,
    object_name=key
)

# Return the URL to the user
print(url)
