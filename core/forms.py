from django import forms
from .models import ContactMessage, AdRequest, RepresentativeApplication


class ContactForm(forms.ModelForm):

    class Meta:
        model  = ContactMessage
        fields = ['name', 'phone', 'email', 'subject', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'placeholder': 'পূর্ণ নাম লিখুন',
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': '০১XXXXXXXXX',
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'example@email.com',
        })
        self.fields['message'].widget = forms.Textarea(attrs={
            'rows': 7,
            'placeholder': 'আপনার বার্তা এখানে লিখুন...',
        })

        # Bengali error messages
        for field in self.fields.values():
            field.error_messages = {
                'required': 'এই ঘরটি পূরণ করা আবশ্যক।',
                'invalid':  'সঠিক তথ্য দিন।',
                'max_length': 'অনেক বেশি দীর্ঘ। সংক্ষেপ করুন।',
            }


class AdRequestForm(forms.ModelForm):

    class Meta:
        model  = AdRequest
        fields = ['name', 'phone', 'email', 'ad_type', 'budget', 'duration', 'details']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'নাম লিখুন'})
        self.fields['phone'].widget.attrs.update({'placeholder': '০১XXXXXXXXX'})
        self.fields['email'].widget.attrs.update({'placeholder': 'example@email.com'})
        self.fields['budget'].widget.attrs.update({'placeholder': 'যেমন: ৫০০০', 'min': 0})
        self.fields['details'].widget = forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'আপনার পণ্য বা সেবার বিবরণ এবং বিজ্ঞাপনের উদ্দেশ্য লিখুন...',
        })
        for field in self.fields.values():
            field.error_messages = {
                'required': 'এই ঘরটি পূরণ করা আবশ্যক।',
                'invalid':  'সঠিক তথ্য দিন।',
            }


class RepresentativeApplicationForm(forms.ModelForm):

    class Meta:
        model  = RepresentativeApplication
        fields = [
            'name', 'phone', 'email', 'role', 'district',
            'education', 'experience', 'motivation', 'portfolio', 'cv',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'আপনার পূর্ণ নাম'})
        self.fields['phone'].widget.attrs.update({'placeholder': '০১XXXXXXXXX'})
        self.fields['email'].widget.attrs.update({'placeholder': 'example@email.com'})
        self.fields['district'].widget.attrs.update({'placeholder': 'আপনার জেলার নাম'})
        self.fields['education'].widget.attrs.update({'placeholder': 'সর্বোচ্চ শিক্ষাগত যোগ্যতা'})
        self.fields['portfolio'].widget.attrs.update({'placeholder': 'https://'})
        self.fields['experience'].widget = forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'পূর্বে সাংবাদিকতার কোনো অভিজ্ঞতা থাকলে সংক্ষেপে লিখুন...',
        })
        self.fields['motivation'].widget = forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'সংক্ষেপে আপনার আগ্রহ ও উদ্দেশ্য লিখুন...',
        })
        self.fields['experience'].required = False
        self.fields['portfolio'].required  = False
        self.fields['cv'].required         = False

        for field in self.fields.values():
            field.error_messages = {
                'required': 'এই ঘরটি পূরণ করা আবশ্যক।',
                'invalid':  'সঠিক তথ্য দিন।',
            }

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv:
            max_size = 5 * 1024 * 1024  # 5 MB
            if cv.size > max_size:
                raise forms.ValidationError('ফাইলের আকার সর্বোচ্চ ৫ MB হতে পারে।')
            allowed = ['.pdf', '.doc', '.docx']
            ext = '.' + cv.name.rsplit('.', 1)[-1].lower()
            if ext not in allowed:
                raise forms.ValidationError('শুধুমাত্র PDF, DOC বা DOCX ফাইল আপলোড করা যাবে।')
        return cv
