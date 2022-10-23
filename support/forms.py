from django import forms
from support.models import *
import requests


class SupportAnswer(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message', ]
    
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

class TicketStatus(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status',]
    
    def __init__(self, *args, **kwargs):
        super(TicketStatus, self).__init__(*args, **kwargs)
        self.initial['status'] = 'answer'