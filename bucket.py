from google.cloud import storage

credentials = 'cred.json'

def upload_to_bucket(bucket_name, blob_name, path_to_file, no_cache=False):
    storage_client = storage.Client.from_service_account_json(credentials)
    bucket = storage_client.bucket(bucket_name)
    
    blob = bucket.blob(blob_name)
    if blob.exists():
        print(f"Blob {blob_name} already exists in {bucket_name}. Deleting it.")
        blob.delete()
    
    blob = bucket.blob(blob_name)

    if no_cache:
        blob.cache_control = "no-cache, no-store, max-age=0"

    blob.upload_from_filename(path_to_file)
    print(f"Blob {blob_name} was uploaded to {bucket_name}.")

    #returns a public url
    return blob.public_url

def del_bucket(bucket_name):
    storage_client = storage.Client.from_service_account_json(credentials)
    bucket = storage_client.bucket(bucket_name)
    bucket.delete(force=True)
    print(f'bucket {bucket.name} deleted.')

def create_bucket(bucket_name):     
    storage_client = storage.Client.from_service_account_json(credentials)
    bucket = storage_client.bucket(bucket_name)
    bucket.create()
    print(f'bucket {bucket.name} created.')

def list_bucket_blobs(bucket_name):
    storage_client = storage.Client.from_service_account_json(credentials)

    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs())

    for blob in blobs:
        print(blob.name)

def download_blob(bucket_name, source_blob_name, destination_file_name):
    storage_client = storage.Client.from_service_account_json(credentials)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(f'Blob {source_blob_name} downloaded to {destination_file_name}.')

def make_bucket_public(bucket_name):
    storage_client = storage.Client.from_service_account_json(credentials)

    bucket = storage_client.bucket(bucket_name)

    # Set the bucket's default object ACL to allow public read access
    bucket.default_object_acl.all().grant_read()

    # Update the bucket's IAM policy to allow public access to objects
    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.bindings.append(
        {"role": "roles/storage.objectViewer", "members": ["allUsers"]}
    )
    bucket.set_iam_policy(policy)

    print(f"Bucket {bucket_name} is now public.")
    
# ------------------------------------ playground ----------------------------------------------------

def main():
    print('Bucket playground activated.')
    del_bucket('test-aiden-user-upload')
    create_bucket('test-aiden-user-upload')
    make_bucket_public('test-aiden-user-upload')

    #print(upload_to_bucket('test-img-aiden', 'test_image', 'data/img/test_image.jpg', no_cache=True))
            
    #list_bucket_blobs('ecobara-img')

    #download_blob('test-img-aiden', 'test_image', 'test_image_dw.jpg')
    #download_blob('ecobara-img', 'test_audio', 'test_audio_dw.json')

if __name__ == "__main__":
    main()