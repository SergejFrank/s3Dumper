# s3Dumper

 #### s3Dumper is a tool to quickly dump a public AWS S3 buckets to look for loot.
## Pre-Requisites
Non-Standard Python Libraries:

* xmltodict
* requests

### Install with virtualenv
```
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage:

    usage: s3Dumper.py [-h] -b BUCKET [-t THREADS] [-m MAXSIZE] [-d SAVEDIR]

    optional arguments:
      -h, --help  show this help message and exit
      -b BUCKET   Bucket you want to dump
      -t THREADS  Number of threads.
      -m MAXSIZE  Maximum file size to download.
      -d SAVEDIR  directory where to dump files

  
     python s3Dumper.py -b BucketName -g
