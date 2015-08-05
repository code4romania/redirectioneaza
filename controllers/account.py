

from models.handlers import LoginHandler

class LoginHandler(LoginHandler):
    def get(self):
        self._serve_page()

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        try:
            user = self.auth.get_user_by_password(username, password, remember=True)

            self.redirect(self.uri_for('home'))
        
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            logging.info('Login failed for user %s because of %s', username, type(e))
            self._serve_page(True)

    def _serve_page(self, failed=False):
        username = self.request.get('username')
        params = {
            'username': username,
            'failed': failed
        }
        self.render_template('login.html', params)

class LogoutHandler(LoginHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect("/")

class SignupHandler(LoginHandler):
    def get(self):

        self.set_template("login.html")
        self.render()

    def post(self):
        # user_name = self.request.get('username')
        email = self.request.get('email')
        first_name = self.request.get('name')
        last_name = self.request.get('lastname')
        
        password = self.request.get('password')

        success, user = self.user_model.create_user(email,
            unique_properties=['email'],
            first_name=first_name, last_name=last_name,
            email=email, password_raw=password, verified=False
        )

        if not success: #user_data is a tuple
            self.display_message('Unable to create user for email %s because of \
                duplicate keys %s' % (email, user))
            return

        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)

        verification_url = self.uri_for('verification', type='v', user_id=user_id,
                signup_token=token, _full=True)

        msg = 'Send an email to user in order to verify their address. \
                They will be able to do so by visiting  <a href="{url}">{url}</a>'

        self.display_message(msg.format(url=verification_url))


class VerificationHandler(LoginHandler):

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
            logging.info('Could not find any user with id "%s" signup token "%s"', user_id, signup_token)
            self.abort(404)

        # store user data in the session
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        if verification_type == 'v':
            # remove signup token, we don't want users to come back with an old link
            self.user_model.delete_signup_token(user.get_id(), signup_token)

            if not user.verified:
                user.verified = True
                user.put()

            self.display_message('User email address has been verified.')
            return
        elif verification_type == 'p':
            # supply user to the page
            params = {
                'user': user,
                'token': signup_token
            }
            self.render_template('resetpassword.html', params)
        else:
            logging.info('verification type not supported')
            self.abort(404)