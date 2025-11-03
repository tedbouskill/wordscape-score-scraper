from google.cloud import storage
from threading import Lock

from cls_env_config import EnvConfigSingleton as EnvConfig

class GCSClientHelperSingleton:
    _instance = None
    _lock = Lock()

    def __new__(cls, key_file_path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GCSClientHelperSingleton, cls).__new__(cls)
                if key_file_path:
                    cls._instance.client = storage.Client.from_service_account_json(key_file_path)
                else:
                    raise ValueError("A key file path must be provided to initialize GCS client.")
        return cls._instance

    def get_client(self):
        return self.client

    def file_exists_in_gcs(self, bucket_name, gcs_path):
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        return blob.exists()

    def upload_to_gcs(self, bucket_name, file_path, gcs_path):
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(file_path)

    def download_from_gcs(self, bucket_name, gcs_path):
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        return blob.download_as_string()

def main():
    config = EnvConfig()

    key_file_path = config.get('GCPCredentials')['Google_Patent_Publications']['keyfile_path']

    gcs_client_singleton = GCSClientHelperSingleton(key_file_path)
    gcs_client = gcs_client_singleton.get_client()

    gcs_client.get_bucket('uspto-xmlarchives')

# Now `gcs_client` can be used in the rest of your code.
