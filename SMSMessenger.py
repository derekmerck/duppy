# Send SMS Messages

import textwrap
import yaml
import smtplib
import logging
import os

class SMSMessenger:

    services = textwrap.dedent('''
        # Sender relay servers
        gmail.com: 'smtp.gmail.com:587'

        ---
        # Receiver device gateways
        alltel:     message.alltel.com
        att:        txt.att.net
        boost:      myboostmobile.com
        nextel:     messaging.sprintpcs.com
        sprint:     messaging.sprintpcs.com
        t-mobile:   tmomail.net
        uscellular: email.uscc.net
        verizon:    vtext.com
        virgin:     vmobl.com
        ''')

    relays, gateways = yaml.load_all(services)

    def __init__(self, relay_useraddr, relay_pword, from_name=None):
        tmp = relay_useraddr.split('@')
        self.relay_user = tmp[0]
        self.relay_server = self.relays[tmp[1]]
        self.relay_pword = relay_pword
        self.logger = logging.getLogger('SMSMessenger')

        if from_name:
            self.from_addr = '{0} <{1}>'.format(from_name, relay_useraddr)
        else:
            self.from_addr = self.relay_user

    def message(self, number, carrier, msg):
        to_addr = '%s@%s' % (number, self.gateways[carrier])
        SMSMessenger.send_message(self.relay_server, self.relay_user, self.relay_pword, self.from_addr, to_addr, msg)

    @staticmethod
    def send_message(relay_server, relay_username, relay_password, from_addr, to_addr, msg):
        server = smtplib.SMTP(relay_server)
        server.starttls()
        server.login(relay_username, relay_password)
        logging.debug(from_addr)
        logging.debug(to_addr)
        logging.debug(msg.encode(encoding='UTF-8'))
        server.sendmail(from_addr, to_addr, msg.encode(encoding='UTF-8'))
        server.quit()


def test_sms():
    relay_user = os.environ['relay_user']
    relay_pword = os.environ['relay_pword']
    from_name = os.environ['from_name']
    phone_number = os.environ['phone_number']
    carrier = os.environ['carrier']

    m = SMSMessenger( relay_user, relay_pword, from_name )
    m.message( phone_number, carrier, 'MAX ALERT | Room 1 | V.TACH | Current HR 120 bpm | Current SpO2 85 % ' )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_sms()
