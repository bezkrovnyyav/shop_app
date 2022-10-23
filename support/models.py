from django.db import models
from accounts.models import CustomUser


# Create your models here.
class Ticket(models.Model):
    status_choices = [
        ('new', 'Новый'),
        ('open', 'Открытый'),
        ('close', 'Закрыт'),
        ('reminder', 'В напоминании'),
        ('answer', 'Отвечен'),
    ]

    title = models.CharField(default='Title', max_length=300)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    status = models.CharField(default='new', choices=status_choices, max_length=30)
    date_create = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    message = models.TextField(default='')
    support_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    date_msg = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.ticket
