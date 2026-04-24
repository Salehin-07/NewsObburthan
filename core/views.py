from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.db.models import Prefetch
from django.contrib import messages
from django.views import View
from .models import CorePost, CoreTag
from .forms import ContactForm, AdRequestForm, RepresentativeApplicationForm


POSTS_PER_PAGE = 20

# Cache timeouts (seconds)
POPULAR_TAGS_CACHE_TTL  = 60 * 10   # 10 minutes
PAGE_CACHE_TTL          = 60 * 5    # 5 minutes
RELATED_POSTS_CACHE_TTL = 60 * 10   # 10 minutes


# ─────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────

def _paginate(request, queryset, per_page=POSTS_PER_PAGE):
    """Shared pagination helper — returns a Page object."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    return page_obj


def _popular_tags():
    """
    Tags with at least one published post.
    Cached for 10 minutes — tags change rarely.
    """
    cached = cache.get('popular_tags')
    if cached is None:
        cached = list(
            CoreTag.objects
            .filter(posts__status=CorePost.STATUS_PUBLISHED)
            .distinct()
        )
        cache.set('popular_tags', cached, POPULAR_TAGS_CACHE_TTL)
    return cached


def _published_posts_qs():
    """
    Base queryset for home + tag_feed.
    .only() skips heavy fields (content) not needed in list views.
    """
    return (
        CorePost.objects
        .filter(status=CorePost.STATUS_PUBLISHED)
        .only(
            'id', 'title', 'slug', 'excerpt',
            'cover_image', 'published_at', 'views_count',
            'author_id',
        )
        .select_related('author', 'author__reporter_profile')
        .prefetch_related(
            Prefetch(
                'tags',
                queryset=CoreTag.objects.only('id', 'name', 'slug'),
            )
        )
        .order_by('-published_at')
    )


# ─────────────────────────────────────────────
# Error handlers
# ─────────────────────────────────────────────

def bad_request(request, exception):
    return render(request, '400.html', status=400)


# ─────────────────────────────────────────────
# Public views
# ─────────────────────────────────────────────

def home(request):
    """Home page — all published posts, newest first, paginated."""
    page_number = request.GET.get('page', 1)
    cache_key   = f'home_page_{page_number}'
    page_obj    = cache.get(cache_key)

    if page_obj is None:
        page_obj = _paginate(request, _published_posts_qs())
        cache.set(cache_key, page_obj, PAGE_CACHE_TTL)

    context = {
        'page_obj':     page_obj,
        'popular_tags': _popular_tags(),
        'active_tag':   None,
    }
    return render(request, 'core/home.html', context)


def tag_feed(request, tag):
    """Tag-filtered feed — same layout as home but scoped to one tag."""
    tag_obj = get_object_or_404(CoreTag, slug=tag)

    page_number = request.GET.get('page', 1)
    cache_key   = f'tag_{tag}_{page_number}'
    page_obj    = cache.get(cache_key)

    if page_obj is None:
        posts_qs = _published_posts_qs().filter(tags=tag_obj)
        page_obj = _paginate(request, posts_qs)
        cache.set(cache_key, page_obj, PAGE_CACHE_TTL)

    context = {
        'page_obj':     page_obj,
        'popular_tags': _popular_tags(),
        'active_tag':   tag_obj,
    }
    return render(request, 'core/home.html', context)


def post_detail(request, slug):
    """Full article detail page."""
    cache_key = f'post_{slug}'
    post      = cache.get(cache_key)

    if post is None:
        post = get_object_or_404(
            CorePost.objects
            .select_related('author', 'author__reporter_profile')
            .prefetch_related(
                Prefetch(
                    'tags',
                    queryset=CoreTag.objects.only('id', 'name', 'slug'),
                )
            ),
            slug=slug,
            status=CorePost.STATUS_PUBLISHED,
        )
        cache.set(cache_key, post, PAGE_CACHE_TTL)

    # Single atomic UPDATE — no read-back, no race condition
    post.increment_views()

    # Related posts cached per post PK
    related_cache_key = f'related_{post.pk}'
    related_posts     = cache.get(related_cache_key)

    if related_posts is None:
        tag_ids = [t.pk for t in post.tags.all()]  # already prefetched
        related_posts = list(
            CorePost.objects
            .filter(status=CorePost.STATUS_PUBLISHED, tags__in=tag_ids)
            .exclude(pk=post.pk)
            .only('id', 'title', 'slug', 'cover_image', 'published_at')
            .distinct()
            .order_by('-published_at')[:5]
        )
        cache.set(related_cache_key, related_posts, RELATED_POSTS_CACHE_TTL)

    context = {
        'post':          post,
        'related_posts': related_posts,
        'popular_tags':  _popular_tags(),
        'active_tag':    None,
    }
    return render(request, 'core/post_detail.html', context)


# ─────────────────────────────────────────────
# Form views
# ─────────────────────────────────────────────

class ContactView(View):
    template_name = 'core/contact.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ContactForm()})

    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'আপনার বার্তা সফলভাবে পাঠানো হয়েছে। আমরা শীঘ্রই যোগাযোগ করব।'
            )
            return redirect('contact')
        return render(request, self.template_name, {'form': form})


class PortalView(View):
    template_name = 'core/portal.html'

    def _get_context(self, ad_form=None, rep_form=None,
                     ad_success=False, rep_success=False):
        return {
            'ad_form':     ad_form  or AdRequestForm(),
            'rep_form':    rep_form or RepresentativeApplicationForm(),
            'ad_success':  ad_success,
            'rep_success': rep_success,
        }

    def get(self, request):
        return render(request, self.template_name, self._get_context())

    def post(self, request):
        form_type = request.POST.get('form_type')

        if form_type == 'ad':
            ad_form = AdRequestForm(request.POST)
            if ad_form.is_valid():
                ad_form.save()
                return render(request, self.template_name,
                              self._get_context(ad_success=True))
            return render(request, self.template_name,
                          self._get_context(ad_form=ad_form))

        elif form_type == 'rep':
            rep_form = RepresentativeApplicationForm(request.POST, request.FILES)
            if rep_form.is_valid():
                rep_form.save()
                return render(request, self.template_name,
                              self._get_context(rep_success=True))
            return render(request, self.template_name,
                          self._get_context(rep_form=rep_form))

        return render(request, self.template_name, self._get_context())
