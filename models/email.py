# -*- coding: utf-8 -*-

import os

from google.appengine.api.mail import EmailMessage

from appengine_config import DEV, CONTACT_FORM_URL, CONTACT_EMAIL_ADDRESS

import sendgrid
from sendgrid.helpers.mail import *
# from handlers import BaseHandler

from logging import info, warn


class EmailManager(object):

    default_sender = {
        "name": "donezsi.eu",
        "email": CONTACT_EMAIL_ADDRESS
    }

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
        subject = kwargs.get("subject")

        # email content
        text_template = kwargs.get("text_template")
        html_template = kwargs.get("html_template", "")

        sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
        
        sender = Email(sender["email"], sender["name"])
        receiver = Email(receiver["email"], receiver["name"])

        # info(text_template)
        
        text_content = Content("text/plain", text_template)
        email = Mail(sender, subject, receiver, text_content)

        if html_template:
            html_content = Content("text/html", html_template)
            email.add_content(html_content)

        if not DEV or not kwargs.get("developement", True):
            response = sg.client.mail.send.post(request_body=email.get())
            
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
                info( content[0] )
            
                if len(content) == 2:
                    info( content[1] )
            
            return True
 
    @staticmethod
    def send_appengine_email(**kwargs):

        receiver = kwargs.get("receiver")
        sender = kwargs.get("sender", EmailManager.default_sender)
        subject = kwargs.get("subject")

        # email content
        text_template = kwargs.get("text_template")
        html_template = kwargs.get("html_template", "")

        # we must format the email address in this way
        receiver_address = "{0} <{1}>".format(receiver["name"], receiver["email"])
        sender_address = "{0} <{1}>".format(sender["name"], sender["email"])

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
