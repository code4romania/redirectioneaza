from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from donations.models import Ngo


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

    # We ignore the "username" field because the authentication
    # will be done by email + password
    username = models.CharField(
        verbose_name=_("username"),
        max_length=150,
        unique=True,
        help_text=_("We do not use this field"),
        validators=[],
        null=True,
        editable=False,
    )

    email = models.EmailField(
        verbose_name=_("email address"), blank=False, null=False, unique=True
    )

    ngo = models.ForeignKey(
        Ngo,
        verbose_name=_("NGO"),
        related_name="users",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="email_unique"),
        ]
        permissions = []
