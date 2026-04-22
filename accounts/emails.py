"""
Email helpers for the accounts app.
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

from .tokens import account_reset_token


def send_password_reset_email(request, user):
    """
    Build a signed reset URL (valid for PASSWORD_RESET_TIMEOUT seconds,
    defaulting to 180 s = 3 minutes as set in settings) and email it
    to the user's registered address.
    """
    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_reset_token.make_token(user)

    reset_url = request.build_absolute_uri(
        f'/accounts/reset-password/{uid}/{token}/'
    )

    subject = 'ছাত্রকন্ঠ — পাসওয়ার্ড পুনরুদ্ধার'

    text_body = (
        f"প্রিয় {user.get_full_name() or user.username},\n\n"
        f"আপনার পাসওয়ার্ড পুনরায় সেট করতে নিচের লিঙ্কে ক্লিক করুন:\n\n"
        f"{reset_url}\n\n"
        f"এই লিঙ্কটি মাত্র ৩ মিনিটের জন্য কার্যকর।\n\n"
        f"যদি আপনি এই অনুরোধ না করে থাকেন, এই ইমেইল উপেক্ষা করুন।\n\n"
        f"— ছাত্রকন্ঠ কারিগরি দল"
    )

    html_body = render_to_string('accounts/email/reset_password.html', {
        'user':      user,
        'reset_url': reset_url,
    })

    send_mail(
        subject      = subject,
        message      = text_body,
        from_email   = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@chatrokontho.com'),
        recipient_list = [user.email],
        html_message = html_body,
        fail_silently = False,
    )
