from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name  = 'accounts'
    label = 'accounts'
    verbose_name = 'Accounts & Staff Profiles'

    def ready(self):
        """
        Import signal handlers so Django registers them once all apps
        have been loaded.  This is the canonical Django pattern — never
        import signals at module-level inside models.py or views.py.
        """
        import accounts.signals  # noqa: F401  — side-effect import
