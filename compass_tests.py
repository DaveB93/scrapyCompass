import unittest
from compass import compassSpider
from compass import Mailer
from enum import Enum



class MailerState(Enum):
    UNINITIALIZED = 1
    INITNEWCALLED = 2
    VALUELOWCALLED = 3
    VALUEOKAYCALLED = 4
    BALANCEUNEXPECTEDLTAUTOLOADCALLED = 5
    BALANCEUNEXPECTEDGTAUTOLOADCALLED = 6


class MockMailer(Mailer):
    def __init__(self, account, password):
        self.state = MailerState.UNINITIALIZED

    def initNew(self, val):
        self.state = MailerState.INITNEWCALLED

    def valueLow(self, balanceCents, expectedBalanceCents, compassCardLastStoredValueCents):
        self.state = MailerState.VALUELOWCALLED

    def valueOkay(self):
        self.state = MailerState.VALUEOKAYCALLED

    def balanceUnexpectedLessThanAutoload(self, balanceCents, expectedBalanceCents, compassCardLastStoredValueCents):
        self.state = MailerState.BALANCEUNEXPECTEDLTAUTOLOADCALLED

    def balanceUnexpectedGreaterThanAutoload(self, balanceCents, expectedBalanceCents, compassCardLastStoredValueCents):
        self.state = MailerState.BALANCEUNEXPECTEDGTAUTOLOADCALLED




class TestSpider(unittest.TestCase):
    def test_one(self):
        spider = compassSpider()
        spider.config["compass"] = {
                "compassCardMaxChange": 3.25,
                "compassCardLastStoredValue": 15.75,
                "compassCardAutoLoad": 10
                }
        spider.mailer = MockMailer("", "")
        spider.parse2("11.75")
        self.assertEqual(spider.mailer.state, MailerState.VALUELOWCALLED)

    def test_two(self):
        spider = compassSpider()
        spider.config["compass"] = {
                "compassCardMaxChange": 3.25,
                "compassCardLastStoredValue": 9,
                "compassCardAutoLoad": 10
                }
        spider.mailer = MockMailer("", "")
        spider.parse2("15.75")
        #print(spider.mailer.state)
        self.assertEqual(spider.mailer.state, MailerState.VALUEOKAYCALLED)

    def test_three(self):
        spider = compassSpider()
        spider.config["compass"] = {
                "compassCardMaxChange": 3.25,
                "compassCardLastStoredValue": 9,
                "compassCardAutoLoad": 10
                }
        spider.mailer = MockMailer("", "")
        spider.parse2("16.75")
        self.assertEqual(spider.mailer.state, MailerState.BALANCEUNEXPECTEDGTAUTOLOADCALLED)

    def test_four(self):
        spider = compassSpider()
        spider.config["compass"] = {
                "compassCardMaxChange": 3.25,
                "compassCardLastStoredValue": 9,
                "compassCardAutoLoad": 10
                }
        spider.mailer = MockMailer("", "")
        spider.parse2("14.70")
        self.assertEqual(spider.mailer.state, MailerState.BALANCEUNEXPECTEDLTAUTOLOADCALLED)

    def test_five(self):
        spider = compassSpider()
        spider.config["compass"] = {
                "compassCardMaxChange": 3.25,
                "compassCardLastStoredValue": 15.75,
                "compassCardAutoLoad": 10
                }
        spider.mailer = MockMailer("", "")
        spider.parse2("13.55")
        self.assertEqual(spider.mailer.state, MailerState.VALUEOKAYCALLED)

    def test_six(self):
        spider = compassSpider()
        spider.config["compass"] = {
                "compassCardMaxChange": 3.25,
                "compassCardLastStoredValue": 13.55,
                "compassCardAutoLoad": 10
                }
        spider.mailer = MockMailer("", "")
        spider.parse2("10.30")
        self.assertEqual(spider.mailer.state, MailerState.VALUEOKAYCALLED)


if __name__ == '__main__':
    unittest.main()
