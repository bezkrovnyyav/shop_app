from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
from accounts.managers import CustomUserManager
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token


courier_model = Group.objects.get_or_create(name = 'Courier')
user_model = Group.objects.get_or_create(name = 'User')
moder_model = Group.objects.get_or_create(name = 'Moder')


class CustomUser(AbstractUser):
    username = models.CharField(blank=True, null=True, max_length=100,
                                validators=[UnicodeUsernameValidator()])
    email = models.EmailField(_('email address'), unique=True)
    balance = models.FloatField(default=0)
    id_tg = models.IntegerField(blank = True, null=True)



    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


    @classmethod
    def is_user_email(self, email):
        try:
            user = self.objects.get(email=email)
            return True
        except ObjectDoesNotExist:
            return False


class Subscribe(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    is_promo = models.BooleanField(default=False, verbose_name='Акции')
    is_answer_support = models.BooleanField(default=False, verbose_name='Уведомления об ответе службы поддержки')
    is_create_order = models.BooleanField(default=False, verbose_name='Офорлмение заказа')
    is_get_digit_file = models.BooleanField(default=False, verbose_name='Получать цифровые файлы с заказа')
    is_authorization = models.BooleanField(default=False, verbose_name='Успешной авторизации в аккаунт')


