# scrapyCompass
a scrapy crawler for checking a compass card balance and alerting if it is wrong

# Setup

requires python 3 and Scrapy
Get scrapy here: https://scrapy.org/
edit compass.py and input 
 * your compass card
 * your compass card cvn
 * your email ( currently it's set up for gmail )
 * your gmail password ( you'll want to generate an app specific password )
 * your expected balance

# Running

To run:
 scrapy runspider compass.py

To automate:
 
 on windows:
  make a batch file with the above command and create a scheduled task
