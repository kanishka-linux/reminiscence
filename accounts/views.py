from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse

def signup(request):
    if settings.ALLOW_ANY_ONE_SIGNUP:
        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                auth_login(request, user)
                return redirect('home')
        else:
            form = UserCreationForm()
        return render(request, 'signup.html', {'form': form})
    else:
        return HttpResponse('<html>Sorry! New Sign UP Not allowed. Ask moderator or Admin to create account for you.</html>');
