from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('login/',   views.staff_login,  name='login'),
    path('logout/',  views.staff_logout, name='logout'),

    # ── Password reset (3-minute token) ───────────────────────────────────────
    path('forgot-password/',                              views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/',              views.reset_password,  name='reset_password'),

    # ── Profile ───────────────────────────────────────────────────────────────
    path('profile/',    views.profile,   name='profile'),
    path('dashboard/',  views.dashboard, name='dashboard'),

    # ── Post CRUD ─────────────────────────────────────────────────────────────
    path('posts/new/',           views.post_create, name='post_create'),
    path('posts/<int:pk>/edit/', views.post_edit,   name='post_edit'),
    path('posts/<int:pk>/delete/', views.post_delete, name='post_delete'),
]
