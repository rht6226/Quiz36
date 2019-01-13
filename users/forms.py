from django import forms
from .models import Profile
from django.contrib.auth.models import User

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',)

        widgets = {
            'first_name' : forms.TextInput(attrs={'class':'form-control '}),
            'last_name' : forms.TextInput(attrs={'class':'form-control'}),
            'email' : forms.TextInput(attrs={'class':'form-control'}),
            }

class DateInput(forms.DateInput):
    input_type = 'date'

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('DOB', 'college', 'bio', 'profilepic')

        widgets = {
            'DOB': DateInput(attrs={'class': 'form-control '}),
            'bio': forms.Textarea(attrs={'class':'form-control '}),
            'college' : forms.TextInput(attrs={'class':'form-control '}),
            }
