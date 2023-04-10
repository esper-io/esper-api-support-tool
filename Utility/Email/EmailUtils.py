import smtplib, ssl

from email.message import EmailMessage
from Utility.Logging.ApiToolLogging import ApiToolLog

from Utility.Resource import installSslCerts


class EmailUtils:
    def __init__(self, login, password, to_addrs):
        self.ssl_port = 465  # For SSL
        self.tls_port = 587  # For TLS
        self.password = password
        self.login = login
        self.to_addrs = to_addrs
        self.do_ssl = None

        installSslCerts()

        # Create a secure SSL context
        self.context = ssl.create_default_context()


    def isReadyToSend(self):
        return self.password and self.login and self.to_addrs

    def _sendEmailFromServer(self, server, subject, msg):
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

    def _sendEmailViaSSl(self, subject, msg):
        with smtplib.SMTP_SSL(
            "smtp.gmail.com", self.ssl_port, context=self.context
        ) as server:
            self.do_ssl = True
            self._sendEmailFromServer(server, subject, msg)

    def _sendEmailViaTls(self, subject, msg):
        try:
            with smtplib.SMTP(
                "smtp.gmail.com", self.tls_port
            ) as server:
                server.starttls()
                self._sendEmailFromServer(server, subject, msg)
        except Exception as e:
            ApiToolLog().LogError(e)

    def sendEmail(self, subject, msg):
        if self.login and self.password:
            if self.do_ssl or self.do_ssl is None:
                try:
                    self._sendEmailViaSSl(subject, msg)
                except Exception as e:
                    self.do_ssl = False
                    ApiToolLog().LogError(e)
                    ApiToolLog().LogResponse("Retrying with SMTP")
                    self._sendEmailViaTls(subject, msg)
            else:
                self._sendEmailViaTls(subject, msg)
