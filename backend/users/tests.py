# Create your tests here.
import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _

from users.models import User
from users.groups_management import MAIN_ADMIN, NGO_ADMIN, NGO_MEMBER, RESTRICTED_ADMIN


class UserModelTests(TestCase):
    def setUp(self):
        # Create groups for role tests
        self.main_admin_group = Group.objects.create(name=MAIN_ADMIN)
        self.ngo_admin_group = Group.objects.create(name=NGO_ADMIN)
        self.ngo_member_group = Group.objects.create(name=NGO_MEMBER)
        self.restricted_admin_group = Group.objects.create(name=RESTRICTED_ADMIN)

    def test_create_user_defaults(self):
        user = User.objects.create_user(email="user@example.com", password="secret")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password("secret"))
        self.assertEqual(user.email, "user@example.com")

    def test_create_superuser_success(self):
        superuser = User.objects.create_superuser(email="admin@example.com", password="adminpass")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.check_password("adminpass"))

    def test_create_superuser_invalid_flags(self):
        # is_staff must be True
        with self.assertRaisesMessage(ValueError, _("Superuser must have is_staff=True.")):
            User.objects.create_superuser(email="x@example.com", password="pass", is_staff=False)
        # is_superuser must be True
        with self.assertRaisesMessage(ValueError, "Superuser must have is_superuser=True."):
            User.objects.create_superuser(email="y@example.com", password="pass", is_superuser=False)

    def test_refresh_and_verify_token(self):
        user = User.objects.create_user(email="t@example.com", password="pw")
        # Initially no token
        self.assertIsNone(user.validation_token)
        self.assertIsNone(user.token_timestamp)

        token = user.refresh_token()
        self.assertIsNotNone(user.validation_token)
        self.assertIsNotNone(user.token_timestamp)
        self.assertEqual(token, user.validation_token)

        # verify matching token
        self.assertTrue(user.verify_token(token))
        # verify with wrong token
        wrong = uuid.uuid4()
        self.assertFalse(user.verify_token(wrong))
        # verify when token cleared
        user.clear_token()
        self.assertFalse(user.verify_token(token))

    def test_clear_token(self):
        user = User.objects.create_user(email="clear@example.com", password="pw")
        user.refresh_token()
        user.clear_token()
        self.assertIsNone(user.validation_token)
        self.assertIsNone(user.token_timestamp)

    def test_activate_deactivate(self):
        user = User.objects.create_user(email="act@example.com", password="pw")
        # default is_active=True from AbstractUser
        user.deactivate()
        self.assertFalse(user.is_active)
        # calling again should not error
        user.deactivate()
        user.activate()
        self.assertTrue(user.is_active)
        # calling again should not error
        user.activate()

    def test_create_admin_login_url(self):
        url_no_next = User.create_admin_login_url()
        self.assertIn(reverse("admin:login"), url_no_next)
        self.assertTrue(url_no_next.endswith("?next="))

        next_path = "/dashboard/"
        url_with_next = User.create_admin_login_url(next_url=next_path)
        self.assertTrue(url_with_next.endswith(f"?next={next_path}"))

    def test_group_properties(self):
        user = User.objects.create_user(email="grp@example.com", password="pw")
        # no groups
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_ngo_admin)
        self.assertFalse(user.is_ngo_member)

        # main admin
        user.groups.add(self.main_admin_group)
        self.assertTrue(user.is_admin)
        self.assertFalse(user.is_ngo_admin)
        self.assertFalse(user.is_ngo_member)
        user.groups.clear()

        # restricted admin
        user.groups.add(self.restricted_admin_group)
        self.assertTrue(user.is_admin)
        user.groups.clear()

        # ngo admin
        user.groups.add(self.ngo_admin_group)
        self.assertTrue(user.is_ngo_admin)
        self.assertTrue(user.is_ngo_member)
        self.assertFalse(user.is_admin)
        user.groups.clear()

        # ngo member
        user.groups.add(self.ngo_member_group)
        self.assertTrue(user.is_ngo_member)
        self.assertFalse(user.is_ngo_admin)
        self.assertFalse(user.is_admin)
