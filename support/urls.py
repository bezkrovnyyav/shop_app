from django.urls import include, path
from support.views import *


urlpatterns = [
    path('tickets/', support_main_page, name='support_main_page'),
    path('all_tickets/', all_ticket, name='all_ticket_page'),
    path('answer_ticket/<int:pk>', answer_ticket_support, name='answer_ticket_support_page'),
    path('ticket/<int:pk>', answer_ticket, name='answer_ticket_page'),
]