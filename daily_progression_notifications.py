import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from twilio.rest import Client


class DailyProgressionNotifications:
    def __init__(self, email_config, sms_config):
        """
        Initialize the daily progression notifications module.
        Args:
            email_config (dict): Dictionary containing email configuration (e.g., SMTP server, port, credentials).
            sms_config (dict): Dictionary containing SMS configuration (e.g., Twilio account SID, auth token, phone numbers).
        """
        self.email_config = email_config
        self.sms_config = sms_config
        self.client = Client(sms_config["account_sid"], sms_config["auth_token"])

    def send_email_notification(self, recipient, subject, body):
        """
        Send an email notification.
        Args:
            recipient (str): Recipient email address.
            subject (str): Email subject.
            body (str): Email body.
        """
        msg = MIMEMultipart()
        msg["From"] = self.email_config["username"]
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(
            self.email_config["smtp_server"], self.email_config["smtp_port"]
        )
        server.starttls()
        server.login(self.email_config["username"], self.email_config["password"])
        server.sendmail(self.email_config["username"], recipient, msg.as_string())
        server.quit()

    def send_sms_notification(self, recipient, message):
        """
        Send an SMS notification.
        Args:
            recipient (str): Recipient phone number.
            message (str): SMS message.
        """
        self.client.messages.create(
            body=message, from_=self.sms_config["from_number"], to=recipient
        )

    def generate_daily_report(self, data):
        """
        Generate a daily progression report.
        Args:
            data (DataFrame): Data containing daily progression information.
        Returns:
            str: Generated report.
        """
        report = f"Daily Progression Report\n\n"
        report += data.to_string(index=False)
        return report

    def send_notifications(self, data, email_recipients, sms_recipients):
        """
        Send daily progression notifications via email and SMS.
        Args:
            data (DataFrame): Data containing daily progression information.
            email_recipients (list): List of email recipients.
            sms_recipients (list): List of SMS recipients.
        """
        report = self.generate_daily_report(data)

        # Send email notifications
        for recipient in email_recipients:
            self.send_email_notification(recipient, "Daily Progression Report", report)

        # Send SMS notifications
        for recipient in sms_recipients:
            self.send_sms_notification(recipient, report)
