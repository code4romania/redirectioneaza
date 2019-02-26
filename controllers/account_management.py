from flask import url_for, redirect, render_template, request
from flask_login import login_user, current_user, logout_user
from datetime import datetime
from logging import info, warn
from sqlalchemy.exc import IntegrityError
from core import app, login_manager,db
from models.handlers import AccountHandler, user_required, BaseHandler
from models.user import User
from appengine_config import CAPTCHA_PRIVATE_KEY, CAPTCHA_POST_PARAM
from .captcha import submit

@login_manager.user_loader
def load_user(user_id):
    """
    Gets user given a certain user_id
    :param user_id:
    :return: User
    """
    return User.query.get(int(user_id))

class LoginHandler(BaseHandler):
    template_name = 'login.html'
    def get(self):

        self.template_values["title"] = "Contul meu"

        if current_user.is_authenticated:
            return redirect(url_for('contul-meu'))

        return render_template(self.template_name, **self.template_values)

    def post(self):

        email = request.form.get('email')
        password = request.form.get('parola')

        if not email:
             self.template_values["errors"] = "Campul email nu poate fi gol."
             return render_template(self.template_name, **self.template_values)

        if not password:
            self.template_values["errors"] = "Campul parola nu poate fi gol."
            return render_template(self.template_name, **self.template_values)

        captcha_response = submit(request.form.get('g-recaptcha-response'), CAPTCHA_PRIVATE_KEY, request.remote_addr)
        
        # if the captcha is not valid return
        if not captcha_response.is_valid:
            
            self.template_values["errors"] = "Se pare ca a fost o problema cu verificarea reCAPTCHA. Te rugam sa incerci din nou."

            return render_template(self.template_name, **self.template_values)

        _user = User.get_by_email(email)

        if _user is not None and _user.check_password(password):
            login_user(_user)
        
            return redirect(url_for('contul-meu'))
        
        else:
            warn('Invalid email or password: {0}'.format(email))

            self.template_values['email'] = email

            self.template_values["errors"] = "Se pare ca aceasta combinatie de email si parola este incorecta."

        return render_template(self.template_name, **self.template_values)

class LogoutHandler(BaseHandler):
    def get(self):
        logout_user()
        return redirect("/")

class SignupHandler(BaseHandler):
    template_name = 'cont-nou.html'
    def get(self):

        self.template_values["title"] = "Cont nou"
        return render_template(self.template_name, **self.template_values)

    def post(self):
        first_name = request.form.get('nume')
        last_name = request.form.get('prenume')
        
        email = request.form.get('email')
        password = request.form.get('parola')

        if not first_name:
            self.template_values["errors"] = "Campul nume nu poate fi gol."
            return render_template(self.template_name, **self.template_values)

        if not last_name:
            self.template_values["errors"] = "Campul prenume nu poate fi gol."
            return render_template(self.template_name, **self.template_values)

        if not email:
            self.template_values["errors"] = "Campul email nu poate fi gol."
            return render_template(self.template_name, **self.template_values)

        if not password:
            self.template_values["errors"] = "Campul parola nu poate fi gol."
            return render_template(self.template_name, **self.template_values)

        captcha_response = submit(request.form.get('g-recaptcha-response'), CAPTCHA_PRIVATE_KEY, request.remote_addr)

        # if the captcha is not valid return
        if not captcha_response.is_valid:
            
            self.template_values["errors"] = "Se pare ca a fost o problema cu verificarea reCAPTCHA. Te rugam sa incerci din nou."
            return render_template(self.template_name, **self.template_values)

        _user  = User( email = email,\
                       first_name = first_name,\
                       last_name = last_name,\
                       password = password,\
                       verified = False)

        db.session.add(_user)

        # unique_properties = ['email']
        # success, user = self.user_model.create_user(email, unique_properties,
        #     first_name=first_name, last_name=last_name,
        #     email=email, password_raw=password, verified=False
        # )

        try:
            db.session.commit()
        except IntegrityError as e:

            print('DEBUG \n'*5)
            print(e)
            print('DEBUG \n'*5)

            self.template_values["errors"] = "Exista deja un cont cu aceasta adresa."
            
            self.template_values.update({
                "nume": first_name,
                "prenume": last_name,
                "email": email
            })

            return render_template(self.template_name, **self.template_values)

        #self.send_email("signup", user)

        try:
            # login the user after signup
            #self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
            
            login_user(_user)
            
            # redirect to my account
            return redirect(url_for('contul-meu'))
        except Exception as e:
            
            self.template_values["errors"] = "Se pare ca a aparut o problema. Te rugam sa incerci din nou"
            return render_template(self.template_name, **self.template_values)

class ForgotPasswordHandler(AccountHandler):
    """template used to reset a password, it asks for the email address"""
    template_name = 'resetare-parola.html'
    def get(self):
        return render_template(self.template_name, **self.template_values)

    def post(self):
        post = self.request

        email = post.get('email')

        if not email:
            self.template_values["errors"] = "Campul email nu poate fi gol."
            return render_template(self.template_name, **self.template_values)

        captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, post.remote_addr)
        # if the captcha is not valid return
        if not captcha_response.is_valid:
            
            self.template_values["errors"] = "Se pare ca a fost o problema cu verificarea reCAPTCHA. Te rugam sa incerci din nou."
            return render_template(self.template_name, **self.template_values)

        user = self.user_model.get_by_auth_id(email)
        if not user:            
            self.template_values.update({
                "errors": "Se pare ca nu exita un cont cu aceasta adresa!"
            })

            return render_template(self.template_name, **self.template_values)

        self.send_email("reset-password", user)
        
        self.template_values.update({
            "errors": False,
            "found": "Un email a fost trimis catre acea adresa"
        })

        return render_template(self.template_name, **self.template_values)

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
            return render_template(self.template_name, **self.template_values)
        else:
            info('verification type not supported')
            abort(404)

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
                "errors": "Nu uita sa scrii o parola noua."
            })
            return render_template(self.template_name, **self.template_values)

        if password != confirm_password:
            self.template_values.update({
                "errors": "Te rugam sa confirmi parola. A doua parola nu seamana cu prima."
            })
            return render_template(self.template_name, **self.template_values)

        user = self.user
        user.set_password(password)
        user.put()

        # remove signup token, we don't want users to come back with an old link
        self.user_model.delete_signup_token(user.get_id(), old_token)

        # self.redirect(self.uri_for("login"))

        return redirect(url_for('login'))