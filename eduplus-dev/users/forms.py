from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('student', 'Étudiant'),
        ('instructor', 'Instructeur'),
    )
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label="Type d'utilisateur")

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "password1", "password2", "user_type")

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data.get('user_type')
        user.user_type = user_type
        user.is_instructor = (user_type == 'instructor')
        # Génère un username unique si besoin
        base_username = self.cleaned_data["email"].split("@")[0]
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
        counter += 1
        user.username = username
        if commit:
          user.save()
        return user