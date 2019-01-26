# -*- coding: utf-8 -*-

import os

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
            return EmailManager.send_sendgrid_email(**kwargs)
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
                info( content[0]['value'] )
            
                if len(content) == 2:
                    info( content[1] )
            
            return True

