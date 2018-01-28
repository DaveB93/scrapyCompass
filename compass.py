from scrapy.item import Item, Field
from scrapy.http import FormRequest
from scrapy.spiders import Spider
from scrapy.utils.response import open_in_browser
import smtplib
import email
from email.message import EmailMessage

emailAcct = ''
emailPassword = ''
expectedBalance = '$14.35' # expected value $XX.XX   ( I didn't strip off the $ at the front)
compassCardNumber = ''
compassCardCVN = ''


def sendemail(expectedVal, val):
    sender = emailAcct
    receivers = [sender]
    user = sender
    passw = emailPassword

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
    msg['Subject'] = "Compass Balance is different"  

    msg.set_content('Compass balance should be \'' + expectedVal+ '\' instead it is \'' +  val + '\'')
    server.sendmail(user,receivers,msg.as_string())


class compassSpider(Spider):
    name = "compasscard"
    allowed_domains = ["compasscard.ca"]
    start_urls = ["https://www.compasscard.ca"]

    def parse(self, response):
        formdata = {'ctl00$Content$ucCardInput$txtSerialNumber': compassCardNumber,
                'ctl00$Content$ucCardInput$txtCvn': compassCardCVN, 
                'ctl00$Content$btnCheckBalance':'Continue as guest'}
        yield FormRequest.from_response(response,
                                        formdata=formdata,
                                        clickdata={'name': 'ctl00$Content$btnCheckBalance'},
                                        callback=self.parse1)

    def parse1(self, response):
        val = response.css("span.value-text-style::text").extract()[0].strip()
        if (val != expectedBalance):
            sendemail(expectedBalance, val)
        else:
            print( "value is fine")


