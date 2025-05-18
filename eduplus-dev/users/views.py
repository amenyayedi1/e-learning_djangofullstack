from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth import logout

@login_required
def profile(request):
    """Affiche le profil de l'utilisateur connecté"""
    return render(request, 'users/profile.html')
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Identifiants invalides.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

from .forms import CustomUserCreationForm

def custom_register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès. Connectez-vous.")
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})
from django.contrib.auth import logout
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def payout_settings(request):
    # À personnaliser selon tes besoins
    return render(request, 'users/payout_settings.html')
def custom_logout(request):
    """Déconnecte l'utilisateur et le redirige vers la page de connexion"""
    logout(request)
    return redirect('users:login')
@login_required
def profile_edit(request):
    """Permet à l'utilisateur de modifier son profil"""
    # Cette vue sera développée davantage dans la prochaine phase
    return render(request, 'users/profile_edit.html')


def instructor_list(request):
    """Affiche la liste des enseignants"""
    instructors = CustomUser.objects.filter(is_instructor=True, is_active=True)
    return render(request, 'users/instructor_list.html', {'instructors': instructors})


def instructor_detail(request, pk):
    """Affiche le détail d'un enseignant"""
    instructor = get_object_or_404(CustomUser, pk=pk, is_instructor=True, is_active=True)
    return render(request, 'users/instructor_detail.html', {'instructor': instructor})


def notification_settings(request):
    return render(request, 'users/notification_settings.html')

def privacy_settings(request):
    
    return render(request, 'users/privacy_settings.html')

def delete_account(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        return redirect('users:login')  # Redirige vers la page de connexion après la suppression
    return redirect('users:profile')  