import boto3
import botocore
import io

class S3Handler:
    def __init__(self, bucket_name: str, region_name: str = 'us-east-1'):
        self.__s3_client = boto3.client('s3')
        self.__bucket_name = bucket_name
        self.__s3_region = region_name

    def upload_file(self, file_path: str, object_name: str) -> None:
        try:
            with open(file_path, 'rb') as file:            
                self.__s3_client.upload_fileobj(io.BytesIO(file.read()), self.__bucket_name, object_name)
                print(f"File {file_path} uploaded to {self.__bucket_name}/{object_name}.")
        except botocore.exceptions.NoCredentialsError:
            print("❌ AWS credentials not found. Run 'aws configure'.")
        except botocore.exceptions.PartialCredentialsError:
            print("❌ Incomplete AWS credentials.")
        except botocore.exceptions.ClientError as e:
            print(f"❌ AWS Client Error: {e}")
        except FileNotFoundError:
            print("❌ Local file not found. Check FILE_PATH.")

    def get_s3_url(self, object_key: str) -> str:
        try:
            return f"https://{self.__bucket_name}.s3.{self.__s3_region}.amazonaws.com/{object_key}"
        except Exception as e:
            print(f"❌ Error generating S3 URL: {e}")
            return None
        
    def download_file(self, object_key: str, download_path: str) -> None:
        try:
            self.__s3_client.download_file(self.__bucket_name, object_key, download_path)
            print(f"File {object_key} downloaded to {download_path}.")
        except botocore.exceptions.NoCredentialsError:
            print("❌ AWS credentials not found. Run 'aws configure'.")
        except botocore.exceptions.PartialCredentialsError:
            print("❌ Incomplete AWS credentials.")
        except botocore.exceptions.ClientError as e:
            print(f"❌ AWS Client Error: {e}")
        except FileNotFoundError:
            print("❌ Local file not found. Check FILE_PATH.")
        except Exception as e:
            print(f"❌ Error downloading file: {e}")

    def download_last_x_images(self, prefix: str, x: int) -> None:
        try:
            response = self.__s3_client.list_objects_v2(Bucket=self.__bucket_name, Prefix=prefix)
            if 'Contents' in response:
                objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)[:x]
                for obj in objects:
                    object_key = obj['Key']
                    download_path = f"downloaded_{object_key.split('/')[-1]}"
                    self.download_file(object_key, download_path)
            else:
                print("❌ No objects found with the specified prefix.")
        except botocore.exceptions.NoCredentialsError:
            print("❌ AWS credentials not found. Run 'aws configure'.")
        except botocore.exceptions.PartialCredentialsError:
            print("❌ Incomplete AWS credentials.")
        except botocore.exceptions.ClientError as e:
            print(f"❌ AWS Client Error: {e}")
        except Exception as e:
            print(f"❌ Error downloading last {x} images: {e}")