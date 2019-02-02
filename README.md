# Multi_threaded HTTP Downloader
This is downloader with has capability to dwonload files from http links using multiple threads and mutiple TCP connections.

To run this file.
give arguments like this
python client.py -n No_of_threads_connection -i Intervaltime -r Resume -f URL_of_file -o Directory_to_storeFile


-n No_of_threads_connections must be number. 1 show single connection or one thread for downloading.

-i Intervaltime is time after which speed and complete matrix should be shown. it is considered in second.

-r Resume, it is binary value 1/0. 1 means Is this file already existed in given directory if yes then it will resume else will download from start. 0 means resume is disable and download file from start.

-f URL_of_file, it is url of file which is to be downloaded. it should be http. It does not support https.

-o Directory_to_storeFile, it is path where file will be downloaded.
