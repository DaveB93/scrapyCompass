from scrapy.item import Item, Field
from scrapy.http import FormRequest,Request
from scrapy.spiders import Spider
from scrapy.utils.response import open_in_browser
import smtplib
import email
from email.message import EmailMessage
import configparser
import os

configfileName = 'compassConfig.ini'
INIT_STORED_VALUE = '$-9999'
INIT_STORED_VALUE_AS_CENTS = -999900

def sendemail(sender, passw, subject, message):
    receivers = [sender]
    user = sender

    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    server = smtplib.SMTP()
    server.connect(smtp_host,smtp_port)
    server.ehlo()
    server.starttls()
    server.login(user,passw)

    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = ", ".join(receivers)
    msg['Subject'] = subject

    msg.set_content(message)
    server.sendmail(user,receivers,msg.as_string())

def inputWithDefault(askFor, config, path):
    splitpath = path.split('/')
    if splitpath[0] in config and splitpath[1] in config[splitpath[0]]:
        question = "{} [{}]:".format(askFor, config[splitpath[0]][splitpath[1]])
        return input(question) or config[splitpath[0]][splitpath[1]]
    else:
        question = '{}:'.format(askFor)
        return input(question)


class compassSpider(Spider):
    name = "compasscard"
    allowed_domains = ["compasscard.ca"]
    config = configparser.ConfigParser()

    def start_requests(self):
        if os.path.isfile(configfileName):
            self.config.read(configfileName)

        if (hasattr(self, 'reconfig')) or (not os.path.isfile(configfileName)):
            self.config["email"] = {
                "account": inputWithDefault('gmail account', self.config, 'email/account'), 
                "password": inputWithDefault('gmail account password', self.config, 'email/password')
            }
            self.config["compass"] = {
                "compassCardNumber": inputWithDefault('Compass Card Number', self.config, 'compass/compassCardNumber'), 
                "compassCardCVN": inputWithDefault('Compass Card CVN', self.config, 'compass/compassCardCVN'),
                "compassCardMaxChange": inputWithDefault('Compass Card Stored Value allowed maximum change between runs (0 for Monthly pass)', self.config, 'compass/compassCardMaxChange'),
                "compassCardLastStoredValue": INIT_STORED_VALUE
            }
            with open(configfileName, 'w') as cfgfile:
                self.config.write(cfgfile)
                cfgfile.close()
        yield Request("https://www.compasscard.ca")


    def parse(self, response):
        formdata = {'ctl00$Content$ucCardInput$txtSerialNumber': self.config['compass']['compassCardNumber'],
                'ctl00$Content$ucCardInput$txtCvn': self.config['compass']['compassCardCVN'], 
                'ctl00$Content$btnCheckBalance':'Continue as guest'}
        yield FormRequest.from_response(response,
                                        formdata=formdata,
                                        clickdata={'name': 'ctl00$Content$btnCheckBalance'},
                                        callback=self.parse1)

    def parse1(self, response):
        val = response.css("span.value-text-style::text").extract()[0].strip()
        cents_int = int(round(float(val.strip('$'))*100))
        maxChangeCents = int(round(float(self.config['compass']['compassCardMaxChange'].strip('$'))*100))
        compassCardLastStoredValue = int(round(float(self.config['compass']['compassCardLastStoredValue'].strip('$'))*100))
        expectedBalance = compassCardLastStoredValue - maxChangeCents
        if (compassCardLastStoredValue == INIT_STORED_VALUE_AS_CENTS):
            message =  'Compass balance initialized it is \'{}\''.format(val)
            sendemail(self.config['email']['account'], self.config['email']['password'], "Compass Balance initialized", message)
        elif (cents_int < expectedBalance):
            message =  'Compass balance should be \'${:.2f}\' instead it is \'${:.2f}\''.format(expectedBalance/100, cents_int/100)
            sendemail(self.config['email']['account'], self.config['email']['password'], "Compass Balance is different", message)
        else:
            print( "value is fine")
        self.config['compass']['compassCardLastStoredValue'] = val
        with open(configfileName, 'w') as cfgfile:
            self.config.write(cfgfile)
            cfgfile.close()





