from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, phone, password=None, **extra_fields):
        """Create save and return a new user"""
        if not phone:
            raise ValueError("User must have a phone number.")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, phone, password):
        """Create and return a new superuser"""
        user = self.create_user(phone, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    phone = PhoneNumberField(unique=True)
    email = models.EmailField(max_length=255, unique=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_partner = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone"
