from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Your name',
                'autocomplete': 'name',
                'required': True,
            }
        ),
        label='Name',
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'you@example.com',
                'autocomplete': 'email',
                'required': True,
            }
        ),
        label='Email address',
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Subject', 'required': True}
        ),
        label='Subject',
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'placeholder': 'Your message',
                'rows': 6,
                'required': True,
            }
        ),
        label='Message',
    )


class NewsletterForm(forms.Form):
    email = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'you@example.com',
                'autocomplete': 'email',
                'required': True,
            }
        ),
    )