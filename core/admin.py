from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils import timezone

from .models import CorePost, CoreTag, CoreReporterProfile, ContactMessage, AdRequest, RepresentativeApplication, Advertisement


# ─────────────────────────────────────────────────────────────────────────────
# CoreTag
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(CoreTag)
class CoreTagAdmin(admin.ModelAdmin):
    list_display  = ('name', 'slug', 'post_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    @admin.display(description='Posts')
    def post_count(self, obj):
        return obj.posts.filter(status=CorePost.STATUS_PUBLISHED).count()


# ─────────────────────────────────────────────────────────────────────────────
# CorePost
# ─────────────────────────────────────────────────────────────────────────────

@admin.action(description='Publish selected posts')
def make_published(modeladmin, request, queryset):
    updated = 0
    for post in queryset.filter(status=CorePost.STATUS_DRAFT):
        post.status = CorePost.STATUS_PUBLISHED
        post.save()   # triggers the signal that awards credits
        updated += 1
    modeladmin.message_user(request, f'{updated} post(s) published.')


@admin.action(description='Revert to draft')
def make_draft(modeladmin, request, queryset):
    queryset.update(status=CorePost.STATUS_DRAFT)


@admin.register(CorePost)
class CorePostAdmin(admin.ModelAdmin):
    list_display   = (
        'title', 'author', 'status_badge', 'tag_list',
        'views_count', 'reading_time', 'published_at',
    )
    list_filter    = ('status', 'tags', 'published_at')
    search_fields  = ('title', 'content', 'author__username', 'author__first_name')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields  = ('author',)
    filter_horizontal = ('tags',)
    date_hierarchy = 'published_at'
    ordering       = ('-published_at', '-created_at')
    actions        = [make_published, make_draft]
    readonly_fields = ('views_count', 'published_at', 'created_at', 'updated_at', 'reading_time_display')

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'cover_image', 'excerpt', 'content'),
        }),
        ('Classification', {
            'fields': ('tags',),
        }),
        ('Publication', {
            'fields': ('status', 'published_at'),
        }),
        ('Stats (read-only)', {
            'fields': ('views_count', 'reading_time_display', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Custom display helpers ────────────────────────────────────────────────

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        if obj.status == CorePost.STATUS_PUBLISHED:
            return mark_safe(
                '<span style="background:#dcfce7;color:#15803d;padding:2px 8px;'
                'border-radius:99px;font-size:11px;font-weight:700;">প্রকাশিত</span>'
            )
        return mark_safe(
            '<span style="background:#f3f4f6;color:#6b7280;padding:2px 8px;'
            'border-radius:99px;font-size:11px;font-weight:700;">খসড়া</span>'
        )

    @admin.display(description='Tags')
    def tag_list(self, obj):
        return ', '.join(t.name for t in obj.tags.all()) or '—'

    @admin.display(description='Reading time')
    def reading_time_display(self, obj):
        return f'{obj.reading_time} মিনিট'

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('author')
            .prefetch_related('tags')
        )


# ─────────────────────────────────────────────────────────────────────────────
# CoreReporterProfile
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(CoreReporterProfile)
class CoreReporterProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'phone', 'joined_at', 'post_count')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    raw_id_fields = ('user',)
    readonly_fields = ('joined_at',)

    @admin.display(description='Posts')
    def post_count(self, obj):
        return CorePost.objects.filter(author=obj.user).count()



@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display   = ('name', 'email', 'subject', 'is_read', 'created')
    list_filter    = ('subject', 'is_read', 'created')
    search_fields  = ('name', 'email', 'message')
    ordering       = ('-created',)
    list_editable  = ('is_read',)
    readonly_fields = ('created',)

    fieldsets = (
        ('প্রেরকের তথ্য', {
            'fields': ('name', 'phone', 'email')
        }),
        ('বার্তা', {
            'fields': ('subject', 'message')
        }),
        ('অবস্থা', {
            'fields': ('is_read', 'created')
        }),
    )


@admin.register(AdRequest)
class AdRequestAdmin(admin.ModelAdmin):
    list_display   = ('name', 'email', 'phone', 'ad_type', 'budget', 'duration', 'status', 'created')
    list_filter    = ('ad_type', 'status', 'duration', 'created')
    search_fields  = ('name', 'email', 'phone', 'details')
    ordering       = ('-created',)
    list_editable  = ('status',)
    readonly_fields = ('created',)

    fieldsets = (
        ('আবেদনকারীর তথ্য', {
            'fields': ('name', 'phone', 'email')
        }),
        ('বিজ্ঞাপনের বিবরণ', {
            'fields': ('ad_type', 'budget', 'duration', 'details')
        }),
        ('পরিচালনা', {
            'fields': ('status', 'notes', 'created')
        }),
    )


@admin.register(RepresentativeApplication)
class RepresentativeApplicationAdmin(admin.ModelAdmin):
    list_display   = ('name', 'role', 'district', 'phone', 'email', 'status', 'created')
    list_filter    = ('role', 'status', 'created')
    search_fields  = ('name', 'email', 'phone', 'district', 'motivation')
    ordering       = ('-created',)
    list_editable  = ('status',)
    readonly_fields = ('created',)

    fieldsets = (
        ('আবেদনকারীর তথ্য', {
            'fields': ('name', 'phone', 'email')
        }),
        ('পদ ও অবস্থান', {
            'fields': ('role', 'district')
        }),
        ('যোগ্যতা ও অভিজ্ঞতা', {
            'fields': ('education', 'experience', 'motivation', 'portfolio', 'cv')
        }),
        ('পরিচালনা', {
            'fields': ('status', 'notes', 'created')
        }),
    )


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display  = ('title', 'placement', 'show_every', 'priority', 'is_active', 'preview_thumb', 'expires_at', 'created')
    list_filter   = ('is_active', 'placement', 'created')
    list_editable = ('is_active', 'priority', 'show_every')
    search_fields = ('title', 'description')
    ordering      = ('-priority', '-created')
    readonly_fields = ('created', 'preview_thumb')

    fieldsets = (
        ('মূল তথ্য', {
            'fields': ('title', 'description', 'placement', 'priority')
        }),
        ('মিডিয়া', {
            'fields': ('image', 'video', 'preview_thumb'),
            'description': 'ছবি অথবা ভিডিও — যেকোনো একটি দিন।',
        }),
        ('লিংক ও সময়সীমা', {
            'fields': ('ad_redirect_url', 'show_every', 'expires_at')
        }),
        ('অবস্থা', {
            'fields': ('is_active', 'created')
        }),
    )

    def preview_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:48px;border-radius:3px;object-fit:cover;" />',
                obj.image.url
            )
        if obj.video:
            return format_html('<span style="color:#c9a84c;">🎬 ভিডিও</span>')
        return '—'
    preview_thumb.short_description = 'প্রিভিউ'