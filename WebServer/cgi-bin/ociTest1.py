# The second part of the code should be used by the receiving CGI
# This part will read the file from the object storage and delete the file itself and also the preauthenticated request

# Uncomment the following lines if you are using this code in a different
# file:

import cgi
import urllib.parse
import oci
import pandas as pd
import ObjectStoragePersistance as OP

print("Content-type:text/html\r\n\r\n")

# bucket_name = 'Balazs-Test-Bucket'
# file_path='C:\\Users\\BMOLNAR\\.oci\\config'
# config=oci.config.from_file(file_location=file_path)
# object_storage = oci.object_storage.ObjectStorageClient(config=config)  # This needs to be done also in the second part if that is in a different scrpt.
# +region=oci.config.get_config_value_or_default(config,'region')
# namespace_name=object_storage.get_namespace().data

form = cgi.FieldStorage()
url_unencoded=form['file_location'].value
filename=url_unencoded.rsplit('/',1)[-1]
path=url_unencoded.rsplit('/',1)[0]
url=path+'/'+urllib.parse.quote(filename)
par_id=form['par_id'].value

#OP.LoadFromObjectStorage(url,'test1.csv',par_id) # if we want to create a local file from obect sorage

df=pd.read_csv(url) # or if we want to read directly the url
print(df.to_html())
OP.DeleteObject(url,par_id)

# #deletes the unused file

# object_storage.delete_object(
#     # namespace_name=oci.config.get_config_value_or_default(config,'tenancy'),
#     namespace_name=namespace_name,
#     bucket_name=bucket_name,
#     object_name=filename
# )

# # Delete unused preauthenticated request
# delete_preauthenticated_request_response = object_storage.delete_preauthenticated_request(
#     namespace_name=namespace_name,
#     bucket_name=bucket_name,
#     par_id=par_id,
#     opc_client_request_id=namespace_name+"EXAMPLE-opcClientRequestId-Value")

# # Get the data from response
# print(delete_preauthenticated_request_response.headers)

