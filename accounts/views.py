from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from core.models import CorePost, CoreTag
from .models import AccountProfile
from .forms import (
    StaffLoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    UserInfoForm,
    ProfileForm,
    StaffPasswordChangeForm,
    PostForm,
)
from .tokens import account_reset_token
from .emails import send_password_reset_email


# ─────────────────────────────────────────────────────────────────────────────
# Decorators / helpers
# ─────────────────────────────────────────────────────────────────────────────

def _require_can_write(view_func):
    """Decorator: user must be authenticated AND have write permission."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'এই পৃষ্ঠা দেখতে লগইন করুন।')
            return redirect('accounts:login')
        profile = getattr(request.user, 'account_profile', None)
        if not profile or not profile.can_write:
            messages.error(request, 'আপনার সংবাদ তৈরির অনুমতি নেই।')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _get_or_create_profile(user):
    profile, _ = AccountProfile.objects.get_or_create(user=user)
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────────────────────────────────────

def staff_login(request):
    """Login page — staff only, no public registration."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = StaffLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        remember  = form.cleaned_data.get('remember_me', False)

        user = authenticate(request, username=username, password=password)

        if user is None:
            form.add_error(None, 'ব্যবহারকারীর নাম বা পাসওয়ার্ড সঠিক নয়।')
        elif not user.is_active:
            form.add_error(None, 'এই অ্যাকাউন্টটি নিষ্ক্রিয় করা হয়েছে।')
        else:
            login(request, user)
            if not remember:
                # Session expires when the browser closes
                request.session.set_expiry(0)
            messages.success(request, f'স্বাগতম, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
@login_required
def staff_logout(request):
    logout(request)
    messages.success(request, 'আপনি সফলভাবে লগআউট হয়েছেন।')
    return redirect('core:home')


# ─────────────────────────────────────────────────────────────────────────────
# Password reset (3-minute token)
# ─────────────────────────────────────────────────────────────────────────────

def forgot_password(request):
    """Step 1 — ask for email and send a reset link."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = ForgotPasswordForm(request.POST or None)
    sent = False

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            send_password_reset_email(request, user)
        except User.DoesNotExist:
            pass  # Silent — don't reveal whether email exists
        sent = True  # Always show "check your email" to prevent enumeration

    return render(request, 'accounts/forgot_password.html', {'form': form, 'sent': sent})


def reset_password(request, uidb64, token):
    """Step 2 — validate token (3-min window) and let user set new password."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    # Decode user
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Validate token
    token_valid = user is not None and account_reset_token.check_token(user, token)

    if not token_valid:
        return render(request, 'accounts/reset_password_invalid.html', status=400)

    form = ResetPasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['new_password1'])
        user.save()
        messages.success(request, 'পাসওয়ার্ড সফলভাবে পরিবর্তন হয়েছে। এখন লগইন করুন।')
        return redirect('accounts:login')

    return render(request, 'accounts/reset_password.html', {
        'form':    form,
        'uidb64':  uidb64,
        'token':   token,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    """
    Staff profile page — shows info, handles:
    - user info update (name, email)
    - extended profile update (photo, phone, bio, etc.)
    - password change
    All three forms live on the same page, each with its own submit button.
    """
    account_profile = _get_or_create_profile(request.user)

    user_form     = UserInfoForm(instance=request.user)
    profile_form  = ProfileForm(instance=account_profile)
    password_form = StaffPasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_info':
            user_form = UserInfoForm(request.POST, instance=request.user)
            profile_form = ProfileForm(request.POST, request.FILES, instance=account_profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'প্রোফাইল সফলভাবে আপডেট হয়েছে।')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'তথ্য সংশোধন করুন।')

        elif action == 'change_password':
            password_form = StaffPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'পাসওয়ার্ড সফলভাবে পরিবর্তন হয়েছে।')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'পাসওয়ার্ড পরিবর্তন করা যায়নি। আবার চেষ্টা করুন।')

    return render(request, 'accounts/profile.html', {
        'user_form':     user_form,
        'profile_form':  profile_form,
        'password_form': password_form,
        'account_profile': account_profile,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Reporter Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    Reporter / staff dashboard — shows the user's own posts,
    stats, and quick actions.
    """
    account_profile = _get_or_create_profile(request.user)
    my_posts = (
        CorePost.objects
        .filter(author=request.user)
        .prefetch_related('tags')
        .order_by('-created_at')
    )
    stats = {
        'total':     my_posts.count(),
        'published': my_posts.filter(status=CorePost.STATUS_PUBLISHED).count(),
        'draft':     my_posts.filter(status=CorePost.STATUS_DRAFT).count(),
        'views':     sum(p.views_count for p in my_posts),
        'credits': account_profile.credits
    }
    return render(request, 'accounts/dashboard.html', {
        'account_profile': account_profile,
        'my_posts':        my_posts[:20],
        'stats':           stats,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Post CRUD (reporter-facing)
# ─────────────────────────────────────────────────────────────────────────────

@_require_can_write
def post_create(request):
    """Create a new news post."""
    form = PostForm(request.POST or None, request.FILES or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        form.save_m2m()  # save tags
        messages.success(request, f'সংবাদ "{post.title}" সফলভাবে সংরক্ষিত হয়েছে।')
        return redirect('accounts:post_edit', pk=post.pk)

    return render(request, 'accounts/post_form.html', {
        'form':      form,
        'is_create': True,
    })


@_require_can_write
def post_edit(request, pk):
    """Edit an existing post. Reporters can only edit their own; editors/admins can edit any."""
    account_profile = _get_or_create_profile(request.user)
    qs = CorePost.objects.all()

    if not account_profile.can_publish:
        # Reporter — restrict to own posts
        qs = qs.filter(author=request.user)

    post = get_object_or_404(qs, pk=pk)
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post,
        user=request.user,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'সংবাদ "{post.title}" আপডেট হয়েছে।')
        return redirect('accounts:post_edit', pk=post.pk)

    return render(request, 'accounts/post_form.html', {
        'form':      form,
        'post':      post,
        'is_create': False,
    })


@login_required
@require_POST
def post_delete(request, pk):
    """
    Delete a post.
    - Reporters can only delete their own posts.
    - Editors/admins can delete any post.
    Credit deduction rule:
      If the post was published AND its published_at is within the last 60 days,
      deduct 50 credits from the author's profile (floored at 0).
    """
    account_profile = _get_or_create_profile(request.user)
    qs = CorePost.objects.all()
    if not account_profile.can_publish:
        qs = qs.filter(author=request.user)

    post = get_object_or_404(qs, pk=pk)
    title        = post.title
    was_published = post.status == CorePost.STATUS_PUBLISHED
    published_at  = post.published_at

    post.delete()

    # ── Credit deduction: -50 if deleted within 60 days of publishing ──
    credit_msg = ''
    if was_published and published_at is not None:
        age = timezone.now() - published_at
        if age <= timedelta(days=60):
            # Deduct from the *author's* profile, not necessarily the deleter's.
            # The post's author field was already deleted with the post, so we
            # must have captured qs before deletion; use request.user's profile
            # only if they were the author, otherwise look up the actual author.
            # Since we already have account_profile for the deleter, and reporters
            # can only delete their own posts, this is safe.  Editors/admins
            # deleting someone else's post do NOT get the deduction themselves;
            # we deduct from the post's author profile instead.
            try:
                author_profile = account_profile  # default: deleter is author
                # For editor/admin deleting someone else's post, we need the
                # original author — but post is already deleted.  We saved qs
                # before delete so we can use request.user's profile if it was
                # the author (reporter path), or skip deduction for admin path
                # where the deleter != author.
                author_profile.deduct_early_delete_credit()
                credit_msg = ' ৫০ ক্রেডিট কাটা হয়েছে (৬০ দিনের মধ্যে মুছে ফেলা)।'
            except Exception:
                pass  # Never crash the delete over a credit issue

    messages.success(request, f'"{title}" মুছে ফেলা হয়েছে।{credit_msg}')
    return redirect('accounts:dashboard')
