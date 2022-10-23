from django.urls import path
from django.urls import include
from accounts.views import *


urlpatterns = [
    path('register/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('is_user_exist/', is_user_exist, name='is_user_exist'),
    path('subscribes/', subscribes, name='subscribe'),
    path('mailing_promotions/', mailing_promotions, name='mailing_promotions')
]