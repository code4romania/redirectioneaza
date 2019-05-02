from collections import OrderedDict
from datetime import datetime, timedelta, date

from flask import Markup
from flask_admin import Admin
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user

from redirectioneaza import app, db
from redirectioneaza.contact_data import LIST_OF_COUNTIES
from redirectioneaza.models import NgoEntity, User, Donor

"""
Handlers  for admin routing
"""


class CustomAdminIndexView(AdminIndexView):
    """
    Creates the Custom admin Index View
    """

    def is_accessible(self):
        """
        Function to check if user has access to certain page
        :return: True if accessible, False if not
        """

        return current_user.is_admin if current_user.is_authenticated else False

    def render(self, template, **kwargs):
        """
        Overrides the default render behaviour to inject statistics

        :param template:
        :param kwargs:
        :return:
        """

        # TODO: Consider caching these results in the sessions object

        yesterday = datetime.now() - timedelta(days=1)

        last_week = datetime.now() - timedelta(days=7)

        last_month = datetime.now() - timedelta(days=30)

        year_start = date(date.today().year, 1, 1)

        total_donors = Donor.query.count()

        total_ngos = NgoEntity.query.count()

        ngos_ytd = NgoEntity.query.filter(NgoEntity.date_created > year_start).count()

        average_donor_cnt = total_donors / total_ngos if total_ngos > 0 else None

        total_users = User.query.count()

        donations_last_24h = Donor.query.filter(Donor.date_created > yesterday).count()

        donations_last_7d = Donor.query.filter(Donor.date_created > last_week).count()

        donations_last_30d = Donor.query.filter(Donor.date_created > last_month).count()

        donations_ytd = Donor.query.filter(Donor.date_created > year_start).count()

        kwargs['data'] = OrderedDict([('NGOs added Year-to-date', ngos_ytd),
                                      ('Total NGOs', total_ngos),
                                      ('Total Users', total_users),
                                      ('Average donation per NGO', average_donor_cnt),
                                      ('Donations in the last 24h', donations_last_24h),
                                      ('Donations in the last 7 days', donations_last_7d),
                                      ('Donations in the last 30 days', donations_last_30d),
                                      ('Donations Year-to-date', donations_ytd),
                                      ('Total Donations', total_donors)
                                      ])
        return super(AdminIndexView, self).render(template, **kwargs)


def date_created_formatter(view, context, model, name):
    if model.date_created:
        markupstring = f"{model.date_created:%Y-%m-%d %H:%M}"
        return Markup(markupstring)
    else:
        return ""


class UserAdmin(ModelView):
    """
    Defines the UserAdmin administration page
    """

    can_create = False
    can_edit = True

    column_formatters = {
        'date_created': date_created_formatter
    }

    column_labels = {'displayname': 'Display Name',
                     'ngo.name': 'NGO Name',
                     'first_name': 'First Name',
                     'last_name': 'Last Name',
                     'verified': 'Verified?',
                     'admin': 'Admin?',
                     'ngo': 'NGO'
                     }

    column_list = ('first_name', 'last_name', 'email', 'ngo.name', 'admin', 'date_created')

    column_searchable_list = ('first_name', 'last_name', 'email', 'ngo.name')

    form_excluded_columns = ('password_hash',)

    form_widget_args = {
        'date_created': {
            'disabled': True
        }}

    def is_accessible(self):
        """
        Function to check if user has access to certain page
        :return: True if accessible, False if not
        """

        return current_user.is_admin if current_user.is_authenticated else False


class NgoEntityAdmin(ModelView):
    """
    Defines the NgoEntityAdmin administration page
    """

    column_labels = {'num_donors': '# of donors',
                     'users': 'Related users',
                     'description': 'Description',
                     'name': 'Name',
                     'url': 'URL',
                     'email': 'Email',
                     'website': 'Website',
                     'county': 'County',
                     'tel': 'Phone',
                     'form_url': 'Form URL',
                     'verified': 'Verified?',
                     'special_status': 'Special status?',
                     'active': 'Active?',
                     'allow_upload': 'Allow upload?',
                     'cif': 'CIF',
                     'account': 'Bank Account No.'
                     }

    column_list = ('name', 'description', 'email', 'county', 'num_donors')

    column_searchable_list = ('name', 'description', 'email', 'website', 'county')

    form_excluded_columns = ('donors', 'tags')

    def _url_formatter(view, context, model, name):
        if model.email:
            markupstring = f"<a href='mailto:{model.email}'>{model.email}</a>"
            return Markup(markupstring)

        else:
            return ""

    column_formatters = {
        'date_created': date_created_formatter,
        'email': _url_formatter
    }

    form_widget_args = {
        'date_created': {
            'disabled': True
        }}

    form_choices = {'county': [(i, i) for i in LIST_OF_COUNTIES]}

    def is_accessible(self):
        """
        Function to check if user has access to certain page
        :return: True if accessible, False if not
        """

        return current_user.is_admin if current_user.is_authenticated else False


class DonorAdmin(ModelView):
    """
    Defines the DonorAdmin administration page
    """

    can_create = False
    can_edit = False

    column_labels = {'displayname': 'Display Name',
                     'ngo.name': 'NGO Name',
                     'first_name': 'First Name',
                     'last_name': 'Last Name'}

    column_list = ('first_name', 'last_name', 'ngo.name', 'city', 'county', 'date_created')
    column_searchable_list = ('first_name', 'last_name', 'ngo.name')

    column_formatters = {
        'date_created': date_created_formatter
    }

    def is_accessible(self):
        """
        Function to check if user has access to certain page
        :return: True if accessible, False if not
        """

        return current_user.is_admin if current_user.is_authenticated else False


admin = Admin(app,
              index_view=CustomAdminIndexView(name='Home', template='admin/siteadmin.html'),
              template_mode='bootstrap3')

admin.add_view(UserAdmin(User, db.session, name='Users'))
admin.add_view(DonorAdmin(Donor, db.session, name='Donors'))
admin.add_view(NgoEntityAdmin(NgoEntity, db.session, name='NGOs'))
# TODO:  Find a way to replace hardcoded url with url_for.
admin.add_link(MenuLink(name='Back to the site', category='', url='/'))
admin.add_link(MenuLink(name='Logout', category='', url='/logout'))
