"""
Password-reset token generator.
Uses Django's PasswordResetTokenGenerator but with a 3-minute timeout.
"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ShortLivedTokenGenerator(PasswordResetTokenGenerator):
    """
    Tokens expire after PASSWORD_RESET_TIMEOUT seconds.
    We override at the settings level; this class just makes the
    generator importable as a named singleton.
    """
    pass


account_reset_token = ShortLivedTokenGenerator()
