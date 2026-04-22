from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class AccountProfile(models.Model):
    """
    Extended profile for all newspaper staff accounts.
    Normal (public) users do NOT get accounts — this is staff-only.
    """

    # ── Core link ─────────────────────────────────────────────────────────────
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='account_profile',
    )

    # ── Personal details ──────────────────────────────────────────────────────
    profile_image = models.ImageField(
        upload_to='accounts/photos/',
        blank=True,
        null=True,
        verbose_name='Profile Photo',
    )
    phone        = models.CharField(max_length=20, blank=True, verbose_name='Phone Number')
    bio          = models.TextField(
        max_length=600,
        blank=True,
        verbose_name='Short Bio',
        help_text='Shown on bylines and the reporter profile page.',
    )
    designation  = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Job Title / Designation',
        help_text='e.g. Senior Reporter, Photo Editor',
    )
    department   = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Department',
        help_text='e.g. National Desk, Sports, Features',
    )

    # ── Social / contact ──────────────────────────────────────────────────────
    twitter_handle = models.CharField(max_length=80, blank=True, verbose_name='Twitter / X Handle')
    facebook_url   = models.URLField(blank=True, verbose_name='Facebook Profile URL')
    linkedin_url   = models.URLField(blank=True, verbose_name='LinkedIn Profile URL')
    personal_email = models.EmailField(blank=True, verbose_name='Personal / Alternate Email')

    # ── Role flags ────────────────────────────────────────────────────────────
    is_reporter     = models.BooleanField(default=False, verbose_name='Is Reporter',
                                          help_text='Can create and edit their own posts.')
    is_editor       = models.BooleanField(default=False, verbose_name='Is Editor',
                                          help_text='Can publish, unpublish, and edit any post.')
    is_photographer = models.BooleanField(default=False, verbose_name='Is Photographer',
                                          help_text='Primarily uploads photos and captions.')
    is_columnist    = models.BooleanField(default=False, verbose_name='Is Columnist',
                                          help_text='Writes opinion / column pieces.')
    is_admin        = models.BooleanField(default=False, verbose_name='Is Admin',
                                          help_text='Full administrative access (mirrors Django staff).')
    is_active_staff = models.BooleanField(default=True, verbose_name='Active Staff',
                                          help_text='Uncheck to disable without deleting the account.')

    # ── Employment info ───────────────────────────────────────────────────────
    employee_id  = models.CharField(max_length=40, blank=True, verbose_name='Employee ID')
    joining_date = models.DateField(null=True, blank=True, verbose_name='Date of Joining')

    # ── Credits ───────────────────────────────────────────────────────────────
    credits = models.IntegerField(
        default=0,
        verbose_name='Credits',
        help_text=(
            'Earned automatically: +50 when a post is first published, '
            '-50 if a published post is deleted within 60 days of publication. '
            'Cannot go below 0.'
        ),
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Credit helpers ────────────────────────────────────────────────────────

    def award_publish_credit(self):
        """
        Atomically award +50 credits for a newly published post.
        Uses F() to avoid race conditions.
        """
        AccountProfile.objects.filter(pk=self.pk).update(
            credits=models.F('credits') + 50
        )
        self.refresh_from_db(fields=['credits'])

    def deduct_early_delete_credit(self):
        """
        Deduct 50 credits when a published post is deleted within 60 days.
        Credits are floored at 0 — they never go negative.
        """
        # Re-fetch fresh value before computing new balance
        self.refresh_from_db(fields=['credits'])
        new_val = max(0, self.credits - 50)
        AccountProfile.objects.filter(pk=self.pk).update(credits=new_val)
        self.refresh_from_db(fields=['credits'])

    # ── General helpers ───────────────────────────────────────────────────────

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def can_write(self):
        """True if the user can create/edit posts."""
        return self.is_reporter or self.is_editor or self.is_columnist or self.is_admin

    @property
    def can_publish(self):
        """True if the user can change post status to Published."""
        return self.is_editor or self.is_admin or self.user.is_superuser

    @property
    def roles_display(self):
        """Human-readable comma-separated list of active roles."""
        roles = []
        if self.is_admin:        roles.append('অ্যাডমিন')
        if self.is_editor:       roles.append('সম্পাদক')
        if self.is_reporter:     roles.append('সাংবাদিক')
        if self.is_columnist:    roles.append('কলামিস্ট')
        if self.is_photographer: roles.append('আলোকচিত্রী')
        return ', '.join(roles) if roles else 'কর্মী'

    def __str__(self):
        return f"{self.display_name} ({self.roles_display})"

    class Meta:
        verbose_name        = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'
        ordering            = ['user__first_name', 'user__last_name']


# ── Auto-create profile whenever a new User is saved ─────────────────────────
@receiver(post_save, sender=User)
def create_account_profile(sender, instance, created, **kwargs):
    if created:
        AccountProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_account_profile(sender, instance, **kwargs):
    if hasattr(instance, 'account_profile'):
        instance.account_profile.save()
