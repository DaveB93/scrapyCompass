# scrapyCompass
a scrapy crawler for checking a compass card balance and alerting if it is wrong

## Setup

Requires python 3 and Scrapy

Get scrapy here: [https://scrapy.org/]

Before you run this, you should collect the following
- your compass card
- your compass card cvn
- your email ( currently it's set up for gmail )
- your gmail password ( you'll want to generate an app specific password, see instructions below if you need help)
- the maximum amount you expect your balance to change between runs

## Running

### To Run:
 `scrapy runspider compass.py`

  if it is your first run, you will be asked to set up some info, which will be stored in a local file called compassConfig.ini

### To Automate:
 
#### On Windows:
  Make a batch file with the above command and create a scheduled task. 

  I personally have it set to run once a day about an hour after I last usually travel.


### To Re-set up:
 Either modify the .ini file directly or run 
  `scrapy runspider compass.py -a reconfig=1`


## Generating an App password for your Google account

1. Go to https://myaccount.google.com/security?utm_source=OGB&utm_medium=act#signin 
1. Click on App passwords
1. Verify your identity with Google
1. in the dropdown at the bottom, enter a custom name (that you'll remember for the app password)
1. click Generate
1. make a copy of this password, you'll only get it once
