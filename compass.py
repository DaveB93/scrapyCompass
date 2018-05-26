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


class Mailer():
    def __init__(self, account, password):
        self.account = account
        self.password = password

    def initNew(self, val):
        message =  'Compass balance initialized it is \'{}\''.format(val)
        sendemail(self.account, self.password, "Compass Balance initialized", message)

    def valueLow(self, balanceCents, expectedBalanceCents, compassCardLastStoredValueCents):
        message =  'Compass balance should be \'${:.2f}\' instead it is \'${:.2f}\',  Previous Balance was \'${:.2f}\''.format(expectedBalanceCents/100, balanceCents/100, compassCardLastStoredValueCents/100)
        sendemail(self.account, self.password, "Compass Balance is different", message)

    def valueOkay(self):
        print( "value is fine")

    def balanceUnexpectedLessThanAutoload(self, balanceCents, expectedBalanceCents, compassCardLastStoredValueCents):
        message = 'Balance is higher than expected but lower than autoload?  previous balance \'${:.2f}\' it should be atleast \'${:.2f}\' actual balance \'${:.2f}\''.format(compassCardLastStoredValueCents/100,expectedBalanceCents/100, balanceCents/100)
        sendemail(self.account, self.password, "Compass Balance Higher Than Expected", message)

    def balanceUnexpectedGreaterThanAutoload(self, balanceCents, expectedBalanceCents, compassCardLastStoredValueCents):
        message = 'Balance is higher than expected and higher than autoload?  previous balance \'${:.2f}\' it should be \'${:.2f}\' actual balance \'${:.2f}\''.format(compassCardLastStoredValueCents/100,expectedBalanceCents/100, balanceCents/100)
        sendemail(self.account, self.password, "Compass Balance Higher Than Expected", message)




class compassSpider(Spider):
    name = "compasscard"
    allowed_domains = ["compasscard.ca"]
    config = configparser.ConfigParser()

    def read_or_init_config(self):
        if os.path.isfile(configfileName):
            self.config.read(configfileName)

        if (hasattr(self, 'reconfig')) or (not 'config' in self.config) or (not 'version' in self.config['config']) or (self.config['config']['version'] != "1") or (not os.path.isfile(configfileName)):
            self.config["email"] = {
                "account": inputWithDefault('gmail account', self.config, 'email/account'), 
                "password": inputWithDefault('gmail account password', self.config, 'email/password')
            }
            self.config["compass"] = {
                "compassCardNumber": inputWithDefault('Compass Card Number', self.config, 'compass/compassCardNumber'), 
                "compassCardCVN": inputWithDefault('Compass Card CVN', self.config, 'compass/compassCardCVN'),
                "compassCardMaxChange": inputWithDefault('Compass Card Stored Value allowed maximum change between runs (0 for Monthly pass)', self.config, 'compass/compassCardMaxChange'),
                "compassCardLastStoredValue": INIT_STORED_VALUE,
                "compassCardAutoLoad": inputWithDefault('Compass Card Autoload Amount (0 for no Autoload)', self.config, 'compass/compassCardAutoLoad')
            }
            self.config["config"] = {
                "version" : "1"
            }
            with open(configfileName, 'w') as cfgfile:
                self.config.write(cfgfile)
                cfgfile.close()
        self.mailer = Mailer(self.config['email']['account'], self.config['email']['password'])




    def updateStoredValue(self,val):
        self.config['compass']['compassCardLastStoredValue'] = val
        with open(configfileName, 'w') as cfgfile:
            self.config.write(cfgfile)
            cfgfile.close()

    def start_requests(self):
        self.read_or_init_config()
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
        self.parse2(val)
        self.updateStoredValue(val)

    def parse2(self, val):
        balanceCents = int(round(float(val.strip('$'))*100))
        maxChangeCents = int(round(float(self.config['compass']['compassCardMaxChange'].strip('$'))*100))
        compassCardLastStoredValueCents = int(round(float(self.config['compass']['compassCardLastStoredValue'].strip('$'))*100))
        expectedBalanceCents = compassCardLastStoredValueCents - maxChangeCents


        if (compassCardLastStoredValueCents == INIT_STORED_VALUE_AS_CENTS):
            self.mailer.initNew(val)
        elif (balanceCents < expectedBalanceCents):
            self.mailer.valueLow(balanceCents, expectedBalanceCents, compassCardLastStoredValueCents)
        elif (balanceCents > compassCardLastStoredValueCents):
            #if we auto loaded for the expected value this will be fine.  if there was a manual reload for more, or a refund ?
            compassCardAutoLoadCents = int(round(float(self.config['compass']['compassCardAutoLoad'].strip('$'))*100))
            balanceWithAutoload = expectedBalanceCents + compassCardAutoLoadCents
            if (balanceCents == balanceWithAutoload):
                expectedBalanceCents = balanceWithAutoload
                self.mailer.valueOkay()
            elif (balanceCents > balanceWithAutoload):
                self.mailer.balanceUnexpectedGreaterThanAutoload(balanceCents, expectedBalanceCents, compassCardLastStoredValueCents)
            else:
                self.mailer.balanceUnexpectedLessThanAutoload(balanceCents, expectedBalanceCents, compassCardLastStoredValueCents)

        else:
            self.mailer.valueOkay()




