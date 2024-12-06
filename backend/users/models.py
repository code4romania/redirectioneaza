import hashlib
import hmac
import uuid

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Ngo
from users.groups_management import MAIN_ADMIN, NGO_ADMIN, NGO_MEMBER, RESTRICTED_ADMIN


class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    The default Django user model, but change it to use the email address
    instead of the username
    """

    id = models.UUIDField(verbose_name="ID", primary_key=True, unique=True, default=uuid.uuid4, editable=False)

    # We ignore the "username" field because the authentication
    # will be done by email + password
    username = models.CharField(
        verbose_name=_("username"),
        max_length=150,
        unique=False,
        help_text=_("We do not use this field"),
        validators=[],
        blank=True,
        default="",
        editable=False,
    )

    email = models.EmailField(verbose_name=_("email address"), blank=False, null=False, unique=True)
    is_ngohub_user = models.BooleanField(default=False)

    ngo = models.ForeignKey(
        Ngo,
        verbose_name=_("NGO"),
        related_name="users",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # originally: verified
    is_verified = models.BooleanField(verbose_name=_("is verified"), db_index=True, default=False)

    validation_token = models.UUIDField(verbose_name=_("validation token"), blank=True, null=True, editable=False)

    token_timestamp = models.DateTimeField(verbose_name=_("validation token timestamp"), blank=True, null=True)

    old_password = models.CharField(verbose_name=_("old password"), max_length=128, blank=True, null=True)

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=timezone.now)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="email_unique"),
        ]
        permissions = (("can_view_old_dashboard", "Can view the old dashboard"),)

    def get_cognito_id(self):
        social = self.socialaccount_set.filter(provider="amazon_cognito").last()
        if social:
            return social.uid
        return None

    def refresh_token(self, commit=True):
        self.token_timestamp = timezone.now()
        self.validation_token = uuid.uuid4()
        if commit:
            self.save()
        return self.validation_token

    def verify_token(self, token):
        validation_token: uuid.UUID = self.validation_token
        if not validation_token or not token:
            return False
        if hmac.compare_digest(validation_token.hex, token.hex):
            return True
        return False

    def clear_token(self, commit=True):
        self.token_timestamp = None
        self.validation_token = None
        if commit:
            self.save()

    def activate(self, commit: bool = True):
        if self.is_active:
            return

        self.is_active = True

        if commit:
            self.save()

    def deactivate(self, commit: bool = True):
        if not self.is_active:
            return

        self.is_active = False

        if commit:
            self.save()

    @staticmethod
    def old_hash_password(password, method, salt=None, pepper=None):
        """
        Implement the old password hashing algorithm from webapp2
        """
        if method == "plain":
            return password

        method = getattr(hashlib, method, None)
        if not method:
            return None

        if salt:
            h = hmac.new(salt.encode("utf8"), password.encode("utf8"), method)
        else:
            h = method(password)

        if pepper:
            h = hmac.new(pepper.encode("utf8"), h.hexdigest().encode("utf8"), method)

        return h.hexdigest()

    def check_old_password(self, password: str = ""):
        """
        Validate the user password input based on the old webapp2 algorithm
        """
        if not password:
            return False

        if not self.old_password or self.old_password.count("$") < 2:
            return False

        pepper = settings.OLD_SESSION_KEY
        hash_val, method, salt = self.old_password.split("$", 2)

        return hmac.compare_digest(self.old_hash_password(password, method, salt, pepper), hash_val)

    @staticmethod
    def create_admin_login_url(next_url=""):
        """
        Create a link to the Django Admin login page with a custom "next" parameter
        """
        return "{}?next={}".format(reverse("admin:login"), next_url)

    @property
    def is_admin(self):
        return self.groups.filter(name__in=(MAIN_ADMIN, RESTRICTED_ADMIN)).exists()

    @property
    def is_ngo_admin(self):
        return self.groups.filter(name=NGO_ADMIN).exists()

    @property
    def is_ngo_member(self):
        return self.groups.filter(name__in=(NGO_ADMIN, NGO_MEMBER)).exists()


class GroupProxy(Group):
    class Meta:
        proxy = True

        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
