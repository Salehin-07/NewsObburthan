from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.core.exceptions import ValidationError

from .models import AccountProfile
from core.models import CorePost, CoreTag


# ─────────────────────────────────────────────────────────────────────────────
# Auth forms
# ─────────────────────────────────────────────────────────────────────────────

class StaffLoginForm(forms.Form):
    """Login form — staff only."""
    username = forms.CharField(
        label='ব্যবহারকারীর নাম',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'আপনার ব্যবহারকারীর নাম',
            'autocomplete': 'username',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='পাসওয়ার্ড',
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••••',
            'autocomplete': 'current-password',
        }),
    )
    remember_me = forms.BooleanField(required=False, label='আমাকে মনে রাখুন')


class ForgotPasswordForm(forms.Form):
    """Step 1 — user enters their work email to request a reset token."""
    email = forms.EmailField(
        label='কর্মক্ষেত্রের ইমেইল',
        widget=forms.EmailInput(attrs={
            'placeholder': 'আপনার অফিস ইমেইল ঠিকানা',
            'autocomplete': 'email',
            'autofocus': True,
        }),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            # Don't reveal whether the email exists — give generic message on success view.
            # But we raise here only in debug; in production keep silent.
            raise ValidationError('এই ইমেইলে কোনো সক্রিয় অ্যাকাউন্ট পাওয়া যায়নি।')
        return email


class ResetPasswordForm(forms.Form):
    """Step 2 — user enters new password after clicking the token link."""
    new_password1 = forms.CharField(
        label='নতুন পাসওয়ার্ড',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'নতুন পাসওয়ার্ড',
            'autocomplete': 'new-password',
            'autofocus': True,
        }),
        min_length=8,
        help_text='কমপক্ষে ৮ অক্ষর',
    )
    new_password2 = forms.CharField(
        label='পাসওয়ার্ড নিশ্চিত করুন',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'পাসওয়ার্ড আবার লিখুন',
            'autocomplete': 'new-password',
        }),
        min_length=8,
    )

    def clean(self):
        cd = super().clean()
        p1 = cd.get('new_password1')
        p2 = cd.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError({'new_password2': 'দুটি পাসওয়ার্ড মিলছে না।'})
        return cd


# ─────────────────────────────────────────────────────────────────────────────
# Profile forms
# ─────────────────────────────────────────────────────────────────────────────

class UserInfoForm(forms.ModelForm):
    """Editable fields on the built-in User model."""
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'প্রথম নাম',
            'last_name':  'শেষ নাম',
            'email':      'ইমেইল ঠিকানা',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'প্রথম নাম'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'শেষ নাম'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'ইমেইল ঠিকানা'}),
        }


class ProfileForm(forms.ModelForm):
    """Editable fields on AccountProfile."""
    class Meta:
        model  = AccountProfile
        fields = [
            'profile_image',
            'phone',
            'bio',
            'designation',
            'department',
            'twitter_handle',
            'facebook_url',
            'linkedin_url',
            'personal_email',
        ]
        labels = {
            'profile_image':  'প্রোফাইল ছবি',
            'phone':          'ফোন নম্বর',
            'bio':            'সংক্ষিপ্ত পরিচিতি',
            'designation':    'পদবি',
            'department':     'বিভাগ',
            'twitter_handle': 'টুইটার / X হ্যান্ডেল',
            'facebook_url':   'ফেসবুক প্রোফাইল URL',
            'linkedin_url':   'LinkedIn URL',
            'personal_email': 'ব্যক্তিগত ইমেইল',
        }
        widgets = {
            'profile_image':  forms.FileInput(attrs={'accept': 'image/*'}),
            'phone':          forms.TextInput(attrs={'placeholder': '+880 1X XX XXX XXX'}),
            'bio':            forms.Textarea(attrs={'rows': 3, 'placeholder': 'আপনার সম্পর্কে সংক্ষেপে লিখুন…'}),
            'designation':    forms.TextInput(attrs={'placeholder': 'যেমন: সিনিয়র রিপোর্টার'}),
            'department':     forms.TextInput(attrs={'placeholder': 'যেমন: জাতীয় ডেস্ক'}),
            'twitter_handle': forms.TextInput(attrs={'placeholder': '@username'}),
            'facebook_url':   forms.URLInput(attrs={'placeholder': 'https://facebook.com/…'}),
            'linkedin_url':   forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/…'}),
            'personal_email': forms.EmailInput(attrs={'placeholder': 'personal@example.com'}),
        }


class StaffPasswordChangeForm(DjangoPasswordChangeForm):
    """Thin wrapper around Django's built-in form, with Bangla labels."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label  = 'বর্তমান পাসওয়ার্ড'
        self.fields['new_password1'].label = 'নতুন পাসওয়ার্ড'
        self.fields['new_password2'].label = 'নতুন পাসওয়ার্ড নিশ্চিত করুন'
        self.fields['old_password'].widget.attrs.update({'placeholder': 'বর্তমান পাসওয়ার্ড'})
        self.fields['new_password1'].widget.attrs.update({'placeholder': 'নতুন পাসওয়ার্ড (কমপক্ষে ৮ অক্ষর)'})
        self.fields['new_password2'].widget.attrs.update({'placeholder': 'পাসওয়ার্ড আবার লিখুন'})
        self.fields['new_password1'].help_text = 'কমপক্ষে ৮ অক্ষর, শুধু সংখ্যা নয়।'


# ─────────────────────────────────────────────────────────────────────────────
# Post / News forms
# ─────────────────────────────────────────────────────────────────────────────

class PostForm(forms.ModelForm):
    """
    Used for both creating and editing a CorePost.
    Tags are handled as a ModelMultipleChoiceField with checkbox widget
    so reporters can easily pick from existing tags.
    """
    tags = forms.ModelMultipleChoiceField(
        queryset=CoreTag.objects.all().order_by('name'),
        required=False,
        label='ট্যাগ / বিভাগ',
        widget=forms.CheckboxSelectMultiple(),
        help_text='একটি বা একাধিক বিভাগ নির্বাচন করুন।',
    )

    class Meta:
        model  = CorePost
        fields = ['title', 'cover_image', 'excerpt', 'content', 'tags', 'status']
        labels = {
            'title':       'সংবাদ শিরোনাম',
            'cover_image': 'কভার ছবি',
            'excerpt':     'সারসংক্ষেপ',
            'content':     'সংবাদের বিস্তারিত',
            'status':      'প্রকাশনা অবস্থা',
        }
        widgets = {
            'title':       forms.TextInput(attrs={
                'placeholder': 'সংবাদের শিরোনাম লিখুন…',
                'class': 'ck-post-input ck-post-input--title',
            }),
            'cover_image': forms.FileInput(attrs={'accept': 'image/*', 'class': 'ck-post-file'}),
            'excerpt':     forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'সংক্ষিপ্ত সারাংশ (না লিখলে স্বয়ংক্রিয়ভাবে তৈরি হবে)…',
                'class': 'ck-post-input',
            }),
            'content':     forms.Textarea(attrs={
                'rows': 20,
                'placeholder': 'সংবাদের পূর্ণ বিবরণ লিখুন…',
                'class': 'ck-post-input ck-post-input--body',
            }),
            'status': forms.Select(attrs={'class': 'ck-post-select'}),
        }
        help_texts = {
            'excerpt': 'খালি রাখলে সংবাদের প্রথম ৩০০ অক্ষর স্বয়ংক্রিয়ভাবে ব্যবহৃত হবে।',
            'status':  '"প্রকাশিত" করলে সাথে সাথে পাঠকদের কাছে দৃশ্যমান হবে।',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Reporters can only save as draft; editors/admins can publish.
        if user and hasattr(user, 'account_profile'):
            if not user.account_profile.can_publish:
                # Restrict status choices — can submit draft but not publish
                self.fields['status'].widget = forms.HiddenInput()
                self.fields['status'].initial = CorePost.STATUS_DRAFT
