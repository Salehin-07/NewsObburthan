import random
from django.utils import timezone
from .models import Advertisement


def advertisements(request):
    """
    সব সক্রিয় ও মেয়াদ-শেষ-না-হওয়া বিজ্ঞাপন context-এ পাঠায়।
    ads.html এই ডেটা ব্যবহার করে JS-এর মাধ্যমে প্রতি ৫–২০ পোস্টে দেখায়।
    """
    now = timezone.now()

    active_ads = Advertisement.objects.filter(
        is_active=True,
    ).filter(
        # মেয়াদ শেষ হয়নি বা মেয়াদ সেট করা হয়নি
        expires_at__isnull=True
    ) | Advertisement.objects.filter(
        is_active=True,
        expires_at__gt=now
    )

    active_ads = active_ads.order_by('-priority', '-created')

    # JSON-serializable format তৈরি করুন
    ads_data = []
    for ad in active_ads:
        ads_data.append({
            'id':          ad.pk,
            'title':       ad.title,
            'description': ad.description or '',
            'image':       ad.image.url if ad.image else '',
            'video':       ad.video.url if ad.video else '',
            'redirect':    ad.ad_redirect_url or '',
            'show_every':  max(5, min(20, ad.show_every)),  # ৫–২০ এর মধ্যে রাখুন
        })

    return {
        'site_ads':       ads_data,
        'site_ads_count': len(ads_data),
    }
