from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import math


class CoreReporterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reporter_profile')
    photo = models.ImageField(upload_to='reporters/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    joined_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — Reporter"

    class Meta:
        verbose_name = "Reporter Profile"
        verbose_name_plural = "Reporter Profiles"


class CoreTag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class CorePost(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True, blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='core_posts'
    )
    cover_image = models.ImageField(upload_to='posts/covers/', blank=True, null=True)
    excerpt = models.TextField(
        max_length=400,
        blank=True,
        help_text="Short summary shown on listing pages. Auto-generated if left blank."
    )
    content = models.TextField()
    tags = models.ManyToManyField(CoreTag, blank=True, related_name='posts')
    views_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Computed helpers ──────────────────────────────────────────────────────

    @property
    def reading_time(self):
        """Estimated reading time in minutes (avg 200 words/min for Bangla)."""
        word_count = len(self.content.split())
        minutes = math.ceil(word_count / 200)
        return max(1, minutes)

    @property
    def display_excerpt(self):
        """Return saved excerpt or auto-strip first 200 chars of content."""
        if self.excerpt:
            return self.excerpt
        plain = self.content[:200]
        return plain + "…" if len(self.content) > 200 else plain

    def increment_views(self):
        CorePost.objects.filter(pk=self.pk).update(views_count=models.F('views_count') + 1)

    # ── Slug generation ───────────────────────────────────────────────────────

    def _make_slug(self):
        base = slugify(self.title, allow_unicode=True)
        if not base:
            base = f"post-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        slug = base
        counter = 1
        while CorePost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._make_slug()
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        if not self.excerpt and self.content:
            self.excerpt = self.content[:300] + ("…" if len(self.content) > 300 else "")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = "Post"
        verbose_name_plural = "Posts"


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('সংবাদ পাঠান',        'সংবাদ পাঠান'),
        ('মতামত / মন্তব্য',    'মতামত / মন্তব্য'),
        ('তথ্য সংশোধন',        'তথ্য সংশোধন'),
        ('বিজ্ঞাপন সংক্রান্ত', 'বিজ্ঞাপন সংক্রান্ত'),
        ('অভিযোগ',             'অভিযোগ'),
        ('অন্যান্য',           'অন্যান্য'),
    ]

    name    = models.CharField('নাম',          max_length=150)
    phone   = models.CharField('মোবাইল',       max_length=20, blank=True)
    email   = models.EmailField('ইমেইল')
    subject = models.CharField('বিষয়',         max_length=60, choices=SUBJECT_CHOICES)
    message = models.TextField('বার্তা')
    is_read = models.BooleanField('পড়া হয়েছে', default=False)
    created = models.DateTimeField('তারিখ',     default=timezone.now)

    class Meta:
        verbose_name        = 'যোগাযোগ বার্তা'
        verbose_name_plural = 'যোগাযোগ বার্তাসমূহ'
        ordering            = ['-created']

    def __str__(self):
        return f'{self.name} — {self.subject} ({self.created.strftime("%d %b %Y")})'


class AdRequest(models.Model):
    """বিজ্ঞাপনের আবেদন"""

    AD_TYPE_CHOICES = [
        ('হোমপেজ ব্যানার',         'হোমপেজ ব্যানার'),
        ('ইনলাইন বিজ্ঞাপন',        'ইনলাইন বিজ্ঞাপন'),
        ('বিজ্ঞপ্তি / প্রেস রিলিজ', 'বিজ্ঞপ্তি / প্রেস রিলিজ'),
        ('স্পনসর কন্টেন্ট',        'স্পনসর কন্টেন্ট'),
        ('সোশ্যাল মিডিয়া বুস্ট',  'সোশ্যাল মিডিয়া বুস্ট'),
        ('অন্যান্য',               'অন্যান্য'),
    ]

    DURATION_CHOICES = [
        ('১ সপ্তাহ', '১ সপ্তাহ'),
        ('১ মাস',    '১ মাস'),
        ('৩ মাস',    '৩ মাস'),
        ('৬ মাস',    '৬ মাস'),
        ('১ বছর',    '১ বছর'),
    ]

    STATUS_CHOICES = [
        ('pending',   'মুলতুবি'),
        ('contacted', 'যোগাযোগ হয়েছে'),
        ('confirmed', 'নিশ্চিত'),
        ('rejected',  'বাতিল'),
    ]

    name     = models.CharField('নাম / প্রতিষ্ঠান',  max_length=200)
    phone    = models.CharField('মোবাইল',             max_length=20)
    email    = models.EmailField('ইমেইল')
    ad_type  = models.CharField('বিজ্ঞাপনের ধরন',    max_length=60, choices=AD_TYPE_CHOICES)
    budget   = models.DecimalField('বাজেট (টাকা)',    max_digits=12, decimal_places=2, null=True, blank=True)
    duration = models.CharField('মেয়াদ',              max_length=20, choices=DURATION_CHOICES, blank=True)
    details  = models.TextField('বিবরণ')
    status   = models.CharField('অবস্থা',             max_length=20, choices=STATUS_CHOICES, default='pending')
    notes    = models.TextField('অভ্যন্তরীণ নোট',     blank=True)
    created  = models.DateTimeField('তারিখ',          default=timezone.now)

    class Meta:
        verbose_name        = 'বিজ্ঞাপন আবেদন'
        verbose_name_plural = 'বিজ্ঞাপন আবেদনসমূহ'
        ordering            = ['-created']

    def __str__(self):
        return f'{self.name} — {self.ad_type} ({self.created.strftime("%d %b %Y")})'


class RepresentativeApplication(models.Model):
    """প্রতিনিধি / সাংবাদিক পদে আবেদন"""

    ROLE_CHOICES = [
        ('জেলা প্রতিনিধি',    'জেলা প্রতিনিধি'),
        ('উপজেলা প্রতিনিধি',  'উপজেলা প্রতিনিধি'),
        ('স্টাফ রিপোর্টার',   'স্টাফ রিপোর্টার'),
        ('ফটো সাংবাদিক',      'ফটো সাংবাদিক'),
        ('ভিডিও জার্নালিস্ট', 'ভিডিও জার্নালিস্ট'),
        ('অনুসন্ধানী সাংবাদিক', 'অনুসন্ধানী সাংবাদিক'),
    ]

    STATUS_CHOICES = [
        ('pending',   'মুলতুবি'),
        ('reviewed',  'পর্যালোচিত'),
        ('shortlisted', 'শর্টলিস্টেড'),
        ('selected',  'নির্বাচিত'),
        ('rejected',  'বাতিল'),
    ]

    name        = models.CharField('পূর্ণ নাম',           max_length=200)
    phone       = models.CharField('মোবাইল',              max_length=20)
    email       = models.EmailField('ইমেইল')
    role        = models.CharField('আবেদনের পদ',          max_length=60, choices=ROLE_CHOICES)
    district    = models.CharField('জেলা / এলাকা',        max_length=100)
    education   = models.CharField('শিক্ষাগত যোগ্যতা',   max_length=200)
    experience  = models.TextField('পূর্ব অভিজ্ঞতা',      blank=True)
    motivation  = models.TextField('আবেদনের কারণ')
    portfolio   = models.URLField('পোর্টফোলিও লিংক',      blank=True)
    cv          = models.FileField('জীবনবৃত্তান্ত (CV)',  upload_to='cvs/%Y/%m/', blank=True, null=True)
    status      = models.CharField('অবস্থা',              max_length=20, choices=STATUS_CHOICES, default='pending')
    notes       = models.TextField('অভ্যন্তরীণ নোট',      blank=True)
    created     = models.DateTimeField('তারিখ',           default=timezone.now)

    class Meta:
        verbose_name        = 'প্রতিনিধি আবেদন'
        verbose_name_plural = 'প্রতিনিধি আবেদনসমূহ'
        ordering            = ['-created']

    def __str__(self):
        return f'{self.name} — {self.role} — {self.district} ({self.created.strftime("%d %b %Y")})'


class Advertisement(models.Model):
    """বিজ্ঞাপন — সাইটে প্রদর্শিত বিজ্ঞাপন"""

    PLACEMENT_CHOICES = [
        ('inline',  'ইনলাইন (নিউজফিডের মাঝে)'),
        ('banner',  'ব্যানার (হেডার/ফুটার)'),
        ('sidebar', 'সাইডবার'),
    ]

    title           = models.CharField('শিরোনাম', max_length=200)
    description     = models.TextField('বিবরণ',   blank=True, null=True)
    image           = models.ImageField('ছবি',     upload_to='ads/images/%Y/%m/', blank=True, null=True)
    video           = models.FileField('ভিডিও',    upload_to='ads/videos/%Y/%m/', blank=True, null=True)
    ad_redirect_url = models.URLField('রিডাইরেক্ট URL', blank=True, null=True)
    placement       = models.CharField('স্থান',    max_length=20, choices=PLACEMENT_CHOICES, default='inline')
    is_active       = models.BooleanField('সক্রিয়', default=True)
    show_every      = models.PositiveIntegerField(
        'প্রতি কত পোস্টে দেখাবে',
        default=7,
        help_text='৫–২০ এর মধ্যে একটি সংখ্যা দিন'
    )
    priority        = models.PositiveIntegerField('অগ্রাধিকার', default=0, help_text='বেশি সংখ্যা = বেশি অগ্রাধিকার')
    created         = models.DateTimeField('তৈরি',  default=timezone.now)
    expires_at      = models.DateTimeField('মেয়াদ শেষ', blank=True, null=True)

    class Meta:
        verbose_name        = 'বিজ্ঞাপন'
        verbose_name_plural = 'বিজ্ঞাপনসমূহ'
        ordering            = ['-priority', '-created']

    def __str__(self):
        return self.title

    @property
    def is_valid(self):
        """মেয়াদ শেষ হয়নি এবং সক্রিয় আছে কিনা পরীক্ষা করুন"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True