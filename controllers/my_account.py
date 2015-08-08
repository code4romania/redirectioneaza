

from google.appengine.ext.ndb import Key, put_multi


from models.handlers import AccountHandler, user_required
from models.models import NgoEntity

class MyAccountHandler(AccountHandler):
    template_name = 'ngo/my-account.html'

    @user_required
    def get(self):

        user = self.user
        self.template_values["user"] = user

        self.render()

    def post(self):
        
        user = self.user
        self.template_values["user"] = user

        ong_nume = self.request.get('ong-nume')
        ong_logo = self.request.get('ong-logo')
        ong_descriere = self.request.get('ong-descriere')
        ong_adresa = self.request.get('ong-adresa')
        
        ong_url = self.request.get('ong-url')
        
        if not ong_nume and not ong_descriere and not ong_adresa and not ong_url:
            self.template_values["errors"] = "Te rugam sa completezi datele din formular."
            self.render()
            return

        ngo_entity_number = NgoEntity.query(NgoEntity.key == Key.("NgoEntity", ong_url)).count(1)

        if ngo_entity_number > 0:
            self.template_values["errors"] = "Din pacate acest url este luat deja."
            self.render()
            return

        new_ngo = NgoEntity(
            id = ong_url,
            name = ong_nume,
            desciption = ong_descriere,
            address = ong_adresa
        )

        # link this user with the ngo
        # the ngo has a key even though we haven't saved it, we offered it an unique id
        user.ngo = ngo.key
        
        # use put_multi to save rpc calls
        put_multi(new_ngo, user)

        # do a refresh
        self.redirect(self.uri_for("contul-meu"))