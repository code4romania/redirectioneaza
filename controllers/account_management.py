# -*- coding: utf-8 -*-

from models.handlers import AccountHandler, user_required
from webapp2_extras.auth import InvalidPasswordError, InvalidAuthIdError

from appengine_config import CAPTCHA_PRIVATE_KEY, CAPTCHA_POST_PARAM

from captcha import submit

from logging import info, warn

class LoginHandler(AccountHandler):
    template_name = 'login.html'
    def get(self):

        self.template_values["title"] = "Contul meu"

        # if the user is logged in just redirect
        if self.user_info:
            self.redirect(self.uri_for("contul-meu"))

        self.render()

    def post(self):
        post = self.request

        email = post.get('email')
        password = post.get('parola')

        if not email:
            self.template_values["errors"] = u"Câmpul email nu poate fi gol."
            self.render()
            return

        if not password:
            self.template_values["errors"] = u"Câmpul parola nu poate fi gol."
            self.render()
            return

        captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, post.remote_addr)

        # if the captcha is not valid return
        if not captcha_response.is_valid:
            
            self.template_values["errors"] = u"Se pare că a fost o problemă cu verificarea reCAPTCHA. Te rugăm să încerci din nou."
            self.render()
            return

        try:
            user = self.auth.get_user_by_password(email, password, remember=True)
            # succes
            self.redirect(self.uri_for('contul-meu'))
        
        except (InvalidAuthIdError, InvalidPasswordError) as e:

            warn('Invalid email or password: {0}'.format(email))

            self.template_values['email'] = email
            self.template_values["errors"] = u"Se pare că această combinație de email și parolă este incorectă."
            self.render()


class LogoutHandler(AccountHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect("/")

class SignupHandler(AccountHandler):
    template_name = 'cont-nou.html'
    def get(self):

        self.template_values["title"] = "Cont nou"
        self.render()

    def post(self):
        post = self.request

        first_name = post.get('nume')
        last_name = post.get('prenume')
        
        email = post.get('email')
        password = post.get('parola')

        if not first_name:
            self.template_values["errors"] = u"Câmpul nume nu poate fi gol."
            self.render()
            return

        if not last_name:
            self.template_values["errors"] = u"Câmpul prenume nu poate fi gol."
            self.render()
            return

        if not email:
            self.template_values["errors"] = u"Câmpul email nu poate fi gol."
            self.render()
            return

        if not password:
            self.template_values["errors"] = u"Câmpul parola nu poate fi gol."
            self.render()
            return

        captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, post.remote_addr)

        # if the captcha is not valid return
        if not captcha_response.is_valid:
            
            self.template_values["errors"] = u"Se pare că a fost o problemă cu verificarea reCAPTCHA. Te rugăm să încerci din nou."
            self.render()
            return

        unique_properties = ['email']
        success, user = self.user_model.create_user(email, unique_properties,
            first_name=first_name, last_name=last_name,
            email=email, password_raw=password, verified=False
        )

        if not success: #user_data is a tuple
            self.template_values["errors"] = u"Există deja un cont cu această adresă."
            
            self.template_values.update({
                "nume": first_name,
                "prenume": last_name,
                "email": email
            })

            self.render()
            return

        self.send_email("signup", user)

        try:
            # login the user after signup
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
            # redirect to my account
            self.redirect(self.uri_for('contul-meu'))
        except Exception as e:
            self.template_values["errors"] = u"Se pare că a aparut o problemă. Te rugăm să încerci din nou"
            self.render()

class ForgotPasswordHandler(AccountHandler):
    """template used to reset a password, it asks for the email address"""
    template_name = 'resetare-parola.html'
    def get(self):
        self.render()

    def post(self):
        post = self.request

        email = post.get('email')

        if not email:
            self.template_values["errors"] = u"Câmpul email nu poate fi gol."
            self.render()
            return

        captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, post.remote_addr)
        # if the captcha is not valid return
        if not captcha_response.is_valid:
            
            self.template_values["errors"] = u"Se pare că a fost o problemă cu verificarea reCAPTCHA. Te rugăm să încerci din nou."
            self.render()
            return

        user = self.user_model.get_by_auth_id(email)
        if user:
            self.send_email("reset-password", user)
        
        self.template_values.update({
            "errors": False,
            "found": u"Dacă adresa este asociată unui cont, vei primi în scurt timp un e-mail cu instrucțiuni de resetare a parolei."
        })

        self.render()

class VerificationHandler(AccountHandler):
    """handler used to:
            verify new account
            reset user password
    """
    
    template_name = 'parola-noua.html'
    def get(self, *args, **kwargs):
        user = None
        user_id = kwargs['user_id']
        signup_token = kwargs['signup_token']
        verification_type = kwargs['type']

        # it should be something more concise like
        # self.auth.get_user_by_token(user_id, signup_token
        # unfortunately the auth interface does not (yet) allow to manipulate
        # signup tokens concisely
        user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token, 'signup')

        if not user:
            info('Could not find any user with id "%s" signup token "%s"', user_id, signup_token)
            self.abort(404)

        # store user data in the session
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        if verification_type == 'v':
            # remove signup token, we don't want users to come back with an old link
            self.user_model.delete_signup_token(user.get_id(), signup_token)

            if not user.verified:
                user.verified = True
                user.put()

            self.redirect(self.uri_for("contul-meu"))

        elif verification_type == 'p':
            # supply user to the page
            self.template_values.update({
                "token": signup_token
            })
            self.render()
        else:
            info('verification type not supported')
            self.abort(404)

class SetPasswordHandler(AccountHandler):
    """handler used to get the submited data in the reset password form"""

    template_name = 'parola-noua.html'
    
    @user_required
    def post(self):
        password = self.request.get('parola')
        confirm_password = self.request.get('confirma-parola')
        old_token = self.request.get('token')

        if not password:
            self.template_values.update({
                "errors": u"Nu uita să scrii o parolă nouă."
            })
            self.render()
            return

        if password != confirm_password:
            self.template_values.update({
                "errors": u"Te rugăm să confirmi parola. A doua parolă nu seamană cu prima."
            })
            self.render()
            return

        user = self.user
        user.set_password(password)
        user.put()

        # remove signup token, we don't want users to come back with an old link
        self.user_model.delete_signup_token(user.get_id(), old_token)

        self.redirect(self.uri_for("login"))