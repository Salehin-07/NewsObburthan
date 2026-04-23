from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.views import View
from .models import CorePost, CoreTag
from .forms import ContactForm, AdRequestForm, RepresentativeApplicationForm


POSTS_PER_PAGE = 20


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
    """Tags that have at least one published post, used everywhere."""
    return CoreTag.objects.filter(
        posts__status=CorePost.STATUS_PUBLISHED
    ).distinct()


def bad_request(request, exception):
    return render(request, '400.html', status=400)

def home(request):
    """Home page — all published posts, newest first, paginated."""
    posts_qs = (
        CorePost.objects
        .filter(status=CorePost.STATUS_PUBLISHED)
        .select_related('author', 'author__reporter_profile')
        .prefetch_related('tags')
    )
    context = {
        'page_obj':     _paginate(request, posts_qs),
        'popular_tags': _popular_tags(),
        'active_tag':   None,
    }
    return render(request, 'core/home.html', context)


def tag_feed(request, tag):
    """Tag-filtered feed — same layout as home but scoped to one tag."""
    tag_obj = get_object_or_404(CoreTag, slug=tag)
    posts_qs = (
        CorePost.objects
        .filter(status=CorePost.STATUS_PUBLISHED, tags=tag_obj)
        .select_related('author', 'author__reporter_profile')
        .prefetch_related('tags')
    )
    context = {
        'page_obj':     _paginate(request, posts_qs),
        'popular_tags': _popular_tags(),
        'active_tag':   tag_obj,
    }
    return render(request, 'core/home.html', context)


def post_detail(request, slug):
    """Full article detail page."""
    post = get_object_or_404(
        CorePost.objects
        .select_related('author', 'author__reporter_profile')
        .prefetch_related('tags'),
        slug=slug,
        status=CorePost.STATUS_PUBLISHED,
    )

    # Increment view count (non-blocking F-expression update)
    post.increment_views()

    # Related posts: same tag(s), exclude current, newest 5
    related_posts = (
        CorePost.objects
        .filter(status=CorePost.STATUS_PUBLISHED, tags__in=post.tags.all())
        .exclude(pk=post.pk)
        .distinct()
        .order_by('-published_at')[:5]
    )

    context = {
        'post':          post,
        'related_posts': related_posts,
        'popular_tags':  _popular_tags(),
        'active_tag':    None,
    }
    return render(request, 'core/post_detail.html', context)



class ContactView(View):
    """
    GET  — যোগাযোগ পাতা দেখান
    POST — বার্তা সংরক্ষণ করুন
    """

    template_name = 'core/contact.html'

    def get(self, request):
        form = ContactForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'আপনার বার্তা সফলভাবে পাঠানো হয়েছে। আমরা শীঘ্রই যোগাযোগ করব।'
            )
            return redirect('contact')
        # Re-render with errors
        return render(request, self.template_name, {'form': form})


class PortalView(View):
    """
    GET  — পোর্টাল পাতা দেখান (বিজ্ঞাপন + প্রতিনিধি ট্যাব)
    POST — form_type অনুযায়ী আবেদন সংরক্ষণ করুন
    """

    template_name = 'core/portal.html'

    def _get_context(self, ad_form=None, rep_form=None,
                     ad_success=False, rep_success=False):
        return {
            'ad_form':    ad_form  or AdRequestForm(),
            'rep_form':   rep_form or RepresentativeApplicationForm(),
            'ad_success': ad_success,
            'rep_success': rep_success,
        }

    def get(self, request):
        return render(request, self.template_name, self._get_context())

    def post(self, request):
        form_type = request.POST.get('form_type')

        # ── বিজ্ঞাপন আবেদন ──
        if form_type == 'ad':
            ad_form = AdRequestForm(request.POST)
            if ad_form.is_valid():
                ad_form.save()
                ctx = self._get_context(ad_success=True)
                return render(request, self.template_name, ctx)
            ctx = self._get_context(ad_form=ad_form)
            return render(request, self.template_name, ctx)

        # ── প্রতিনিধি আবেদন ──
        elif form_type == 'rep':
            rep_form = RepresentativeApplicationForm(request.POST, request.FILES)
            if rep_form.is_valid():
                rep_form.save()
                ctx = self._get_context(rep_success=True)
                return render(request, self.template_name, ctx)
            ctx = self._get_context(rep_form=rep_form)
            return render(request, self.template_name, ctx)

        # অজানা form_type
        return render(request, self.template_name, self._get_context())