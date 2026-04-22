"""
accounts/signals.py

Watches CorePost saves and awards +50 credits to the author's
AccountProfile the first time a post transitions to 'published'.

Why a separate signals file?
  - Keeps models.py clean.
  - AccountsConfig.ready() imports this, ensuring Django registers
    the handler only once, after all apps are fully loaded.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import CorePost


@receiver(post_save, sender=CorePost)
def award_credit_on_publish(sender, instance, created, **kwargs):
    """
    Award +50 credits to the author the FIRST TIME a post goes live.

    Detection strategy:
      - We cannot rely on `created` alone (draft → published is an update).
      - We store nothing extra on CorePost, so we use a trick:
        compare `instance.status` against the DB value that existed
        *before* this save by doing a lightweight DB query.
        Because post_save fires after the save, we check the pre-save
        state by looking at `update_fields` or by keeping a pre_save sentinel.

    We use Django's `pre_save` sentinel pattern via a module-level dict
    (see pre_award_sentinel below) set by the pre_save receiver.
    """
    pass   # Real logic is split across pre_save + post_save below.


# ── Implementation using pre_save to capture previous status ─────────────────

from django.db.models.signals import pre_save

# Module-level dict: { post_pk: previous_status }
# Populated by pre_save, consumed by post_save.
_prev_status: dict = {}


@receiver(pre_save, sender=CorePost)
def _capture_pre_publish_status(sender, instance, **kwargs):
    """Record the post's status in the DB *before* this save."""
    if instance.pk:
        try:
            _prev_status[instance.pk] = (
                CorePost.objects
                .filter(pk=instance.pk)
                .values_list('status', flat=True)
                .get()
            )
        except CorePost.DoesNotExist:
            _prev_status[instance.pk] = None
    else:
        # Brand-new post — no previous status exists.
        _prev_status[instance.pk] = None


@receiver(post_save, sender=CorePost)
def _award_credit_on_first_publish(sender, instance, created, **kwargs):
    """
    Award +50 credits when a post transitions to 'published' for the
    first time (draft → published OR brand-new post saved as published).
    """
    prev = _prev_status.pop(instance.pk, None)
    is_now_published = instance.status == CorePost.STATUS_PUBLISHED
    was_not_published = prev != CorePost.STATUS_PUBLISHED

    if is_now_published and was_not_published:
        # Only award if there's a real author with a profile
        author = instance.author
        if author is None:
            return
        try:
            profile = author.account_profile
            profile.award_publish_credit()
        except Exception:
            # Never crash the save pipeline over a credit operation
            pass
