#!/usr/bin/env python3

import io
import oci
import datetime
import urllib.parse

config_file_path='C:\\Users\\BMOLNAR\\.oci\\config'
config=oci.config.from_file(file_location=config_file_path)
object_storage = oci.object_storage.ObjectStorageClient(config=config)
region=oci.config.get_config_value_or_default(config,'region')
namespace_name=object_storage.get_namespace().data
bucket_name = 'Balazs-Test-Bucket'

def SaveToObjectStorage(filename):
    file_item=open(filename,'rb')
    file_contents = file_item.read()
    buffer = io.BytesIO(file_contents)

    import random
    import string
    randomString=''.join(random.choice(string.ascii_letters) for i in range(5))
    key = datetime.datetime.now().strftime('%Y%m%d%H%M%S%fZ')+randomString+'#'+filename
    object_storage.put_object(      # create the object in Object storage
        namespace_name=object_storage.get_namespace().data,
        bucket_name=bucket_name,
        object_name=key,
        put_object_body=buffer
    )
    create_preauthenticated_request_response = object_storage.create_preauthenticated_request(
    namespace_name=namespace_name,
    bucket_name=bucket_name,
    create_preauthenticated_request_details=oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        name=key+'_Request',
        access_type="AnyObjectReadWrite",
        time_expires=(datetime.datetime.now()+ datetime.timedelta(days=1, hours=0)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        bucket_listing_action="Deny",
        object_name=key),
    opc_client_request_id=namespace_name+"EXAMPLE-opcClientRequestId-Value")
    par_id=create_preauthenticated_request_response.data.id
    url="https://objectstorage.{}.oraclecloud.com{}{}".format(region,create_preauthenticated_request_response.data.access_uri,urllib.parse.quote(key))
    return url,par_id

def LoadFromObjectStorage(url,filename,par_id=''):

    if type(url) is tuple:
        par_id=url[-1]
        url=url[0]
    import urllib
    webf = urllib.request.urlopen(url)
    
    content = webf.read()
    f = open(filename, 'wb')
    f.write(content)
    f.close()

    # object_storage.delete_object(
    #     namespace_name=namespace_name,
    #     bucket_name=bucket_name,
    #     object_name=url.rsplit('/',1)[-1]
    # )

    # if par_id!='':
    #     # Delete unused preauthenticated request
    #     delete_preauthenticated_request_response = object_storage.delete_preauthenticated_request(
    #         namespace_name=namespace_name,
    #         bucket_name=bucket_name,
    #         par_id=par_id,
    #         opc_client_request_id=namespace_name+"EXAMPLE-opcClientRequestId-Value")
    DeleteObject(url,par_id)

def DeleteObject(url, par_id):

    object_storage.delete_object(
        namespace_name=namespace_name,
        bucket_name=bucket_name,
        object_name=urllib.parse.unquote(url).rsplit('/',1)[-1]
    )

    if par_id!='':
        # Delete unused preauthenticated request
        delete_preauthenticated_request_response = object_storage.delete_preauthenticated_request(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            par_id=par_id,
            opc_client_request_id=namespace_name+"EXAMPLE-opcClientRequestId-Value")
    


# TO test the functionality of this module
# url,par_id=SaveToObjectStorage('test.csv')
# LoadFromObjectStorage(url,'test1.csv',par_id)

# f=open('test1.csv','r')
# txt=f.read()
# print(txt)



