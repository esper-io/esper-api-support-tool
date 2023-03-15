import smtplib, ssl

from os.path import basename
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


class EmailUtils:
    def __init__(self, login, password, to_addrs):
        self.port = 465  # For SSL
        self.password = password
        self.login = login
        self.to_addrs = to_addrs

        # Create a secure SSL context
        self.context = ssl.create_default_context()

    def isReadyToSend(self):
        return self.password and self.login and self.to_addrs

    def sendEmail(self, subject, msg):
        if self.login and self.password:
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

    def sendEmailWithAttachment(self, subject, text, files=None):
        msg = MIMEMultipart()
        msg["From"] = self.login
        if type(self.to_addrs) == list:
            msg["To"] = ", ".join(self.to_addrs)
        elif type(self.to_addrs) == str:
            msg["To"] = self.to_addrs
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject

        msg.attach(MIMEText(text))

        if type(files) == list:
            for f in files or []:
                with open(f, "rb") as fil:
                    part = MIMEApplication(fil.read(), Name=basename(f))
                # After the file is closed
                part["Content-Disposition"] = 'attachment; filename="%s"' % basename(f)
                msg.attach(part)
        elif type(files) == str:
            with open(files, "rb") as fil:
                part = MIMEApplication(fil.read(), Name=basename(files))
            # After the file is closed
            part["Content-Disposition"] = 'attachment; filename="%s"' % basename(files)
            msg.attach(part)

        with smtplib.SMTP_SSL(
            "smtp.gmail.com", self.port, context=self.context
        ) as server:
            server.login(self.login, self.password)
            server.set_debuglevel(1)

            server.sendmail(self.login, self.to_addrs, msg.as_string())
