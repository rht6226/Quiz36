from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login', views.login, name='login'),
    path('signup', views.signup, name='signup'),
    path('logout', views.logout, name='logout'),
    path('profile', views.profile, name ='profile'),
    path('dashboard', views.dash, name='dashboard'),
    path('edit_profile', views.update_profile, name='edit_profile'),
    path('profile/<slug:username>', views.public_profile, name='profile'),
    path('login/remove_session',views.destroy_prev_session,name='destroy_prev_session'),
    # password reset urls
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # password change url
    path('change_password/', views.change_password, name='change_password'),

]
