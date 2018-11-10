import boto3

def generate_s3_urls(remote_output_folder):
    s3 = boto3.client("s3")
    bucket = "tlapp"
    zipped_outputs_filename = remote_output_folder + ".tar.gz"
    key = zipped_outputs_filename
    put_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=60 * 60 * 24 * 30,
        HttpMethod="PUT",
    )
    get_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=60 * 60 * 24 * 30
    )

    return {
        "get": get_url,
        "put": put_url
    }