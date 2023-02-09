# -*- coding: utf-8 -*-

# We need this in order to differentiate between the local and the
# standard email libraries
from __future__ import absolute_import

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.appengine.api.mail import EmailMessage

from appengine_config import DEV, UNICODE_CONTACT_EMAIL_ADDRESS

import sendgrid
from sendgrid.helpers.mail import *

from logging import info, warn


class EmailManager(object):

    default_sender = {
        "name": u"redirectioneaza",
        "email": UNICODE_CONTACT_EMAIL_ADDRESS,
    }

    @staticmethod
    def send_dynamic_email(template_id, email, data):

        if DEV:
            info('Sending dynamic email. Template: {}. Email: {}'.format(template_id, email))
            info('Data: {}'.format(data))
            return True

        message = Mail()
        message.from_email = From(EmailManager.default_sender['email'])
        message.to = To(email)
        message.dynamic_template_data = data
        message.template_id = template_id

        try:
            sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
        except Exception as e:
            print(e)
            return False

        if response.status_code == 202:
            return True
        else:
            warn(response.status_code)
            warn(response.body)
            return False

    @staticmethod
    def send_email(**kwargs):
        """
        kwargs:
            receiver        dict
            sender          dict
            subject         String

            text_template
            html_template
        """

        if DEV or kwargs.get("developement", False):
            info('Called send_email() in DEV mode. Email not being sent.')
            info(u'Receiver: {}. Subject: {}'.format(kwargs.get("receiver"), kwargs.get("subject")))
            info(kwargs.get('text_template'))
            
            return True

        # make sure we have the SMTP env vars
        if not os.environ.get('SMTP_HOST') and not os.environ.get('SMTP_USER'):
            error_message = "Cannot send emails! You have to set either the Sendgrid key or the SMTP details."
            warn( error_message )
            return False

        response = EmailManager.send_smtp_email(**kwargs)
        if response:
            return True

        # if it failed through SMTP, try sendgrid as backup
        warn("Failed to send SMTP email: {0}".format(kwargs.get("subject")))

        try:
            response = EmailManager.send_sendgrid_email(**kwargs)

            # if False then the send failed
            if response is False:
                error_message = "Failed to send email: {0}".format(kwargs.get("subject"))

            return response

        except Exception, e:
            
            warn(e)
            return False


    @staticmethod
    def send_sendgrid_email(**kwargs):
        """method used to send an email using the sendgrid API
        kwargs:
            receiver
            sender
            subject

            text_template
            html_template
        """

        receiver = kwargs.get("receiver")
        sender = kwargs.get("sender", EmailManager.default_sender)
        subject = kwargs.get("subject", "").encode("utf-8")

        # email content
        text_template = kwargs.get("text_template")
        html_template = kwargs.get("html_template", "")

        email = Mail()

        email.from_email = From(sender["email"], sender["name"])
        email.to = To(receiver["email"], receiver["name"])

        email.subject = Subject(subject)

        if html_template:
            email.content = [
                Content("text/html", html_template),
                Content("text/plain", text_template)
            ]
        else:
            email.content = Content("text/plain", text_template)

        sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(email)
        
        if response.status_code == 202:
            return True
        else:
            
            warn(response.status_code)
            warn(response.body)

            return False

 
    @staticmethod
    def send_smtp_email(**kwargs):

        receiver = kwargs.get("receiver")  # dict
        sender = kwargs.get("sender", EmailManager.default_sender)
        subject = kwargs.get("subject", "").encode("utf-8")

        # email content
        text_template = kwargs.get("text_template", "").encode("utf-8")

        # we must format the email address in this way
        receiver_address = u"{0} <{1}>".format(receiver["name"], receiver["email"]).encode("utf-8")
        sender_address = u"{0} <{1}>".format(sender["name"], sender["email"]).encode("utf-8")

        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender_address
        message['To'] = receiver_address

        text_version = MIMEText(text_template, 'plain', 'utf-8')
        
        message.attach(text_version)

        # if we have an html version
        if kwargs.get('html_template'):
            html_template = kwargs.get("html_template", "").encode("utf-8")
            html_version = MIMEText(html_template, 'html', 'utf-8')
            message.attach(html_version)

        try:
            smtp = smtplib.SMTP(os.environ.get('SMTP_HOST'), port=os.environ.get('SMTP_PORT'))
            smtp.ehlo()
            smtp.starttls()
            smtp.login(os.environ.get('SMTP_USER'), os.environ.get('SMTP_PASS'))
            smtp.sendmail(sender_address, receiver_address, message.as_string())
            smtp.quit()

            return True

        except Exception, e:
            warn(e)

            return False
