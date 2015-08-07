

from models.handlers import AccountHandler
from account import user_required



class MyAccountHandler(AccountHandler):
    template_name = 'ngo/contul-meu.html'
    
    @user_required
    def get(self):
        user = self.user
        self.template_values["user"] = self.user

    	self.render()

