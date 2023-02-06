# -*- coding: utf-8 -*-

# We need this in order to differentiate between the local and the
# standard email libraries
from __future__ import absolute_import

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.appengine.api.mail import EmailMessage

from appengine_config import DEV, CONTACT_EMAIL_ADDRESS

import sendgrid
from sendgrid.helpers.mail import *

from logging import info, warn


class EmailManager(object):

    default_sender = {
        "name": "redirectioneaza",
        "email": CONTACT_EMAIL_ADDRESS
    }

    @staticmethod
    def send_dynamic_email(template_id, email, data):

        if not DEV:
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
        else:
            info('Sending dynamic email. Template: {}. Email: {}'.format(template_id, email))
            info('Data: {}'.format(data))

            return True

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

        # If there is no Sendgrid API Key, try to use the SMTP service
        if not os.environ.get('SENDGRID_API_KEY'):
            if not os.environ.get('SMTP_HOST') and not os.environ.get('SMTP_USER'):
                error_message = "Cannot send emails! You have to set either the Sendgrid key or the SMTP details."
                warn( error_message )
                return False
            else:
                response = EmailManager.send_smtp_email(**kwargs)
                if response is False:
                    error_message = "Failed to send SMTP email: {0}{1}".format(kwargs.get("subject"), kwargs.get("receiver")["email"])
                    warn( error_message )
                    return False
                else:
                    return True

        # There is a Sendgrid API Key set
        try:

            response = EmailManager.send_sendgrid_email(**kwargs)

            # if False then the send failed
            if response is False:
                
                # try appengine's mail API
                response = EmailManager.send_appengine_email(**kwargs)
                
                # if this doesn't work either, give up
                if response is False:
                    error_message = "Failed to send email: {0}{1}".format(kwargs.get("subject"), kwargs.get("receiver")["email"])
                    warn( error_message )
                    return False

            return True

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
        text_template = kwargs.get("text_template", "").encode("utf-8")
        html_template = kwargs.get("html_template", "").encode("utf-8")

        email = Mail()

        email.from_email = From(sender["email"].encode("utf-8"), sender["name"].encode("utf-8"))
        email.to = To(receiver["email"].encode("utf-8"), receiver["name"].encode("utf-8"))

        email.subject = Subject(subject)

        if html_template:
            email.content = [
                Content("text/html", html_template),
                Content("text/plain", text_template)
            ]
        else:
            email.content = Content("text/plain", text_template)


        if not DEV or not kwargs.get("developement", True):
            sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(email)
            
            if response.status_code == 202:
                return True
            else:
                
                warn(response.status_code)
                warn(response.body)

                return False
        else:
            info(email.get()['personalizations'])

            content = email.get()['content']
            if content:
                info( content[0]['value'] )
            
                if len(content) == 2:
                    info( content[1] )
            
            return True
 
    @staticmethod
    def send_appengine_email(**kwargs):

        receiver = kwargs.get("receiver")
        sender = kwargs.get("sender", EmailManager.default_sender)
        subject = kwargs.get("subject", "").encode("utf-8")

        # email content
        text_template = kwargs.get("text_template", "").encode("utf-8")
        html_template = kwargs.get("html_template", "").encode("utf-8")

        # we must format the email address in this way
        receiver_address = "{0} <{1}>".format(receiver["name"], receiver["email"]).encode("utf-8")
        sender_address = "{0} <{1}>".format(sender["name"], sender["email"]).encode("utf-8")

        try:
            # create a new email object
            message = EmailMessage(sender=sender_address, to=receiver_address, subject=subject)

            # add the text body
            message.body = text_template

            if html_template:
                message.html = html_template

            if DEV:
                info(message.body)

            # send the email
            # on dev the email is not actually sent just logged in the terminal
            message.send()

            return True

        except Exception, e:
            warn(e)

            return False

    @staticmethod
    def send_smtp_email(**kwargs):

        receiver = kwargs.get("receiver")
        sender = kwargs.get("sender", EmailManager.default_sender)
        subject = kwargs.get("subject", "").encode("utf-8")

        # email content
        text_template = kwargs.get("text_template", "").encode("utf-8")
        html_template = kwargs.get("html_template", "").encode("utf-8")

        # we must format the email address in this way
        receiver_address = "{0} <{1}>".format(receiver["name"], receiver["email"]).encode("utf-8")
        sender_address = "{0} <{1}>".format(sender["name"], sender["email"]).encode("utf-8")

        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender_address
        message['To'] = receiver_address

        text_version = MIMEText(text_template, 'plain', 'utf-8')
        html_version = MIMEText(html_template, 'html', 'utf-8')
        
        message.attach(text_version)
        if html_template:
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