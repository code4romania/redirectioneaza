from logging import warning

from flask import url_for, redirect, render_template, request, abort
from flask_login import login_user, current_user, logout_user
from sqlalchemy.exc import IntegrityError

from redirectioneaza import login_manager, db
from redirectioneaza.config import CAPTCHA_PRIVATE_KEY
from redirectioneaza.handlers.base import BaseHandler
from redirectioneaza.handlers.captcha import submit
from redirectioneaza.models import User


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

        if current_user.is_authenticated and not current_user.is_admin:
            return redirect(url_for('contul-meu'))

        elif current_user.is_authenticated and current_user.is_admin:
            return redirect(url_for('admin.index'))

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
            self.template_values[
                "errors"] = "Se pare ca a fost o problema cu verificarea reCAPTCHA. Te rugam sa incerci din nou."

            return render_template(self.template_name, **self.template_values)

        _user = User.get_by_email(email)

        if _user is not None and _user.check_password(password):

            login_user(_user)

            if current_user.is_authenticated and not current_user.is_admin:
                return redirect(url_for('contul-meu'))

            elif current_user.is_authenticated and current_user.is_admin:
                return redirect(url_for('admin.index'))

        else:
            warning('Invalid email or password: {0}'.format(email))

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
        last_name = request.form.get('nume')
        first_name = request.form.get('prenume')

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
            self.template_values[
                "errors"] = "Se pare ca a fost o problema cu verificarea reCAPTCHA. Te rugam sa incerci din nou."
            return render_template(self.template_name, **self.template_values)

        # noinspection PyArgumentList
        # See https://stackoverflow.com/questions/49465166/incorrect-call-arguments-for-new-in-pycharm
        _user = User(email=email,
                     first_name=first_name,
                     last_name=last_name,
                     password=password,
                     verified=False)

        db.session.add(_user)

        # unique_properties = ['email']
        # success, user = self.user_model.create_user(email, unique_properties,
        #     first_name=first_name, last_name=last_name,
        #     email=email, password_raw=password, verified=False
        # )

        try:
            db.session.commit()
        except IntegrityError as e:

            self.template_values["errors"] = "Exista deja un cont cu aceasta adresa."

            self.template_values.update({
                "nume": first_name,
                "prenume": last_name,
                "email": email
            })

            return render_template(self.template_name, **self.template_values)

        self.send_email("signup", _user)

        try:
            # login the user after signup
            # self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

            login_user(_user)

            # redirect to my account
            return redirect(url_for('contul-meu'))
        except Exception as e:

            self.template_values["errors"] = "Se pare ca a aparut o problema. Te rugam sa incerci din nou"
            return render_template(self.template_name, **self.template_values)


class ForgotPasswordHandler(BaseHandler):
    """template used to reset a password, it asks for the email address"""
    template_name = 'resetare-parola.html'

    def get(self):
        return render_template(self.template_name, **self.template_values)

    def post(self):

        email = request.form.get('email')

        if not email:
            self.template_values["errors"] = "Campul email nu poate fi gol."
            return render_template(self.template_name, **self.template_values)

        captcha_response = submit(request.form.get('g-recaptcha-response'), CAPTCHA_PRIVATE_KEY, request.remote_addr)

        # if the captcha is not valid return
        if not captcha_response.is_valid:
            self.template_values[
                "errors"] = "Se pare ca a fost o problema cu verificarea reCAPTCHA. Te rugam sa incerci din nou."

            return render_template(self.template_name, **self.template_values)

        user = User.query.filter_by(email=email).first()

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


class VerificationHandler(BaseHandler):
    """handler used to:
            verify new account
            reset user password
    """

    template_name = 'parola-noua.html'

    def get(self, token):

        verification = self.confirm_token(token)

        if not verification.result:
            return abort(404)

        _user = User.query.filter_by(email=verification.email).first()

        if not _user:
            raise NotImplementedError("No such user is found even though token is valid")

        if current_user != _user and current_user.is_authenticated:
            raise NotImplementedError("Cannot confirm - another user is already logged in.")

        if verification.type == 'v':

            if not _user.verified:

                _user.verified = True

                db.session.add(_user)

                db.session.commit()

                return redirect(url_for("contul-meu"))

            else:
                raise NotImplementedError("User is already verified, let him know his token is no longer good")

        elif verification.type == 'p':
            self.template_values.update({
                "token": token
            })
            return render_template(self.template_name, **self.template_values)

        else:
            raise NotImplementedError("Verification type not supported")


class SetPasswordHandler(BaseHandler):
    """handler used to get the submited data in the reset password form"""

    template_name = 'parola-noua.html'

    # TODO Look into setting up token invalidation after successful action

    def post(self):

        verification = self.confirm_token(request.form.get('token'))

        if not verification.result:
            return abort(404)

        password = request.form.get('parola')

        confirm_password = request.form.get('confirma-parola')

        if not password:
            self.template_values.update({
                "errors": "Nu uita sa scrii o parola noua."
            })
            return render_template(self.template_name, **self.template_values)

        if password != confirm_password:
            self.template_values.update({
                "errors": "Te rugam sa confirmi parola. A doua parola nu este identica cu prima."
            })
            return render_template(self.template_name, **self.template_values)

        _user = User.query.filter_by(email=verification.email).first()

        if not _user:
            raise NotImplementedError("No such user is found even though token is valid")

        _user.password = password

        db.session.merge(_user)

        db.session.commit()

        return redirect(url_for('login'))
