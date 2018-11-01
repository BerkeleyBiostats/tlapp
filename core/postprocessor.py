import boto3
import datetime
import io
import json
import logging
import os
import subprocess
import sys
import tarfile
import tempfile
import traceback
import uuid
from urllib.parse import urlparse, urlunparse
from django.conf import settings
from django.template import loader, Context
from bs4 import BeautifulSoup
from core import models

logger = logging.getLogger('django')

def change_image_links(html, job_id):
    logger.info("Replacing relative image links with S3 signed urls")
    s3 = boto3.client("s3")
    bucket = "tlapp"

    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")

    for tag in img_tags:

        src = tag.get("src")

        # Some Rmd documents embed images directly in the html with
        # data attributes.
        if src.startswith("data:"):
            continue

        key = job_id + "/" + src
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=60 * 60 * 24 * 30,
        )

        tag["src"] = url

    return soup.prettify()


def post_process_outputs(job):

    s3 = boto3.resource("s3")

    parts = urlparse(job.output_url)
    output_zip_key = parts.path[1:]  # Remove leading slash

    output_path = "/tmp/%s" % output_zip_key
    logger.info("Downloading job outputs to %s" % output_path)

    s3.Object("tlapp", output_zip_key).download_file(output_path)

    tar = tarfile.open(output_path)
    tar.extractall(path="/tmp")
    tar.close()

    # Upload all the files unzipped
    output_dirname = output_zip_key[:-7]
    f = []
    k = []
    output_path = os.path.join("/tmp", output_dirname)
    for (dirpath, dirnames, filenames) in os.walk(output_path):
        keypath = dirpath[len("/tmp/") :]
        keys = [os.path.join(keypath, name) for name in filenames]
        filenames = [os.path.join(dirpath, name) for name in filenames]
        f.extend(filenames)
        k.extend(keys)

    logger.info("Files to upload to s3:")
    logger.info(zip(f, k))

    for filename, key in zip(f, k):
        s3.Object("tlapp", key).upload_file(filename)

    report_path = os.path.join(output_path, "REPORT.html")
    if os.path.exists(report_path):
        logger.info("Found a report")
        with open(report_path) as f:
            job.report_html = f.read()
            job.report_html = change_image_links(job.report_html, output_dirname)
    else:
        logger.info("Didn't find a report")


def handle_a_job():
    # Pick off a random job that hasn't been postprocessed
    job = (
        models.ModelRun.objects.filter(
            status=models.ModelRun.status_choices["executed"]
        )
        .order_by("?")
        .first()
    )

    if job is None:
        return 0

    job.status = models.ModelRun.status_choices["postprocessing"]
    job.postprocessing_attempted_at = datetime.datetime.utcnow()
    job.save()

    try:
        post_process_outputs(job)
        job.status = models.ModelRun.status_choices["success"]
    except:
        traceback.print_exc()
        job.postprocessing_traceback = traceback.format_exc()
        job.status = models.ModelRun.status_choices["error"]
    finally:
        job.save()

    return 1
