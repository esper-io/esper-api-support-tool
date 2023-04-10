import smtplib, ssl

from email.message import EmailMessage
from Utility.Logging.ApiToolLogging import ApiToolLog

from Utility.Resource import installSslCerts


class EmailUtils:
    def __init__(self, login, password, to_addrs):
        self.port = 465  # For SSL
        self.password = password
        self.login = login
        self.to_addrs = to_addrs

        # Create a secure SSL context
        self.context = ssl.create_default_context()

        installSslCerts()

    def isReadyToSend(self):
        return self.password and self.login and self.to_addrs

    def sendEmail(self, subject, msg):
        if self.login and self.password:
            try:
                with smtplib.SMTP_SSL(
                    "smtp.gmail.com", self.port, context=self.context
                ) as server:
                    server.login(self.login, self.password)
                    server.set_debuglevel(1)
                    sentMsg = EmailMessage()
                    sentMsg.set_content(msg)

                    sentMsg["Subject"] = subject
                    sentMsg["From"] = self.login
                    if type(self.to_addrs) == list:
                        sentMsg["To"] = ", ".join(self.to_addrs)
                    elif type(self.to_addrs) == str:
                        sentMsg["To"] = self.to_addrs
                    server.send_message(sentMsg)
            except Exception as e:
                ApiToolLog().LogError(e)
