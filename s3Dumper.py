#!/usr/bin/env python

from argparse import ArgumentParser
import requests
import xmltodict
import sys
import os
import shutil
import traceback
from queue import Queue
from threading import Thread, Lock


bucket_q = Queue()
download_q = Queue()

def print_banner():
        print('''\nDescription:
        s3Dumper is a tool to quickly dump a public AWS S3 buckets to look for loot.
        @ok_bye_now'''
        )   

def bucket_worker():
    while True:
        item = bucket_q.get()
        try:
            fetch(item)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print(e)
        bucket_q.task_done()

def downloadWorker():
    print('Download worker running...')
    while True:
        item = download_q.get()
        try:
            downloadFile(item)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print(e)
        download_q.task_done()

def fetch(url):
    print('Fetching ' + url + '...')
    response = requests.get(url)
    if response.status_code == 403 or response.status_code == 404:
        status403(url)
    if response.status_code == 200:
        if "Content" in response.text:
            returnedList=parseS3Repsone(response,url.split("/?")[0])
            nextElem = "{}/?marker={}".format(url.split("/?")[0],returnedList[-1])
            bucket_q.put(nextElem)

def parseS3Repsone(response,line):
    print("Parsing "+line.rstrip() + '...')
    objects=xmltodict.parse(response.text)
    Keys = []
    try:
        contents = objects['ListBucketResult']['Contents']
        if not isinstance(contents, list):
            contents = [contents]
        for child in contents:
            Keys.append(child['Key'])
    except:
        pass

    for words in Keys:
        words = (str(words)).rstrip()
        collectable = line+'/'+words
        queue_up_download(collectable)
    return Keys

def queue_up_download(filepath):
    download_q.put(filepath)
    print('Collectable: {}'.format(filepath))

def downloadFile(filename):
    global arguments
    
    print('Downloading {}'.format(filename) + '...')
    local_path = get_make_directory_return_filename_path(filename)
    local_filename = (filename.split('/')[-1]).rstrip()
    print('local {}'.format(local_path))
    if local_filename =="":
        print("Directory..\n")
    else:
        r = requests.get(filename.rstrip(), stream=True)
        if 'Content-Length' in r.headers:
            if int(r.headers['Content-Length']) > arguments.maxsize:
                print("This file is greater than the specified max size... skipping...\n")
            else:
                with open(local_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        r.close()

directory_lock = Lock()

def get_directory_lock():
    directory_lock.acquire()

def release_directory_lock():
    directory_lock.release()

def get_make_directory_return_filename_path(url):
    global arguments
    bits = url.split('/')
    directory = arguments.savedir
    for i in range(2,len(bits)-1):
        directory = os.path.join(directory, bits[i])
    try:
        get_directory_lock()
        if not os.path.isdir(directory):
            os.makedirs(directory)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(e)
    finally:
        release_directory_lock()

    return os.path.join(directory, bits[-1]).rstrip()

def main():
    global arguments
    parser = ArgumentParser()
    parser.add_argument("-b", dest="bucket", required=True, help="Bucket you want to dump") 
    parser.add_argument("-t", dest="threads", type=int, required=False, default=8, help="Number of threads.")
    parser.add_argument("-m", dest="maxsize", type=int, required=False, default=104857600, help="Maximum file size to download.")
    parser.add_argument("-d", dest="savedir", required=False, default='dump', help="directory where to dump files")
    

    if len(sys.argv) == 1:
        print_banner()
        parser.error("No arguments given.")
        parser.print_usage
        sys.exit()

    
    # output parsed arguments into a usable object
    arguments = parser.parse_args()

    # start up bucket workers
    for i in range(0,arguments.threads):
        print('Starting thread...')
        t = Thread(target=bucket_worker)
        t.daemon = True
        t.start()
       
    # start download workers 
    for i in range(1, arguments.threads):
        t = Thread(target=downloadWorker)
        t.daemon = True
        t.start()


    bucket = 'http://'+arguments.bucket+'.s3.amazonaws.com'
    print('Queuing {}'.format(bucket) + '...')
    bucket_q.put(bucket)

    bucket_q.join()
    download_q.join()

if __name__ == "__main__":
    main()