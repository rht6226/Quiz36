from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib import auth, messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .forms import UserForm, ProfileForm
from quiz.models import Quiz,Score
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .models import Profile
import os
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

def destroy_prev_session(request):
    user = User.objects.get(username=request.POST['username'])
    user.profile.flag = False
    user.profile.save()
   #The below line disables the user in order to login properly this must be set back again to true
    user.is_active = False
    user.save()

    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        #USER wants to sign up
        if request.POST['password1'] == request.POST['password2']:
            #Entered passwords are identical
            try:
                # #check if user already exists in database if yes raise error

                user = User.objects.get(username = request.POST['username'])
                return render(request, 'signup.html', {'error': 'Username is already taken!'})


            except:
               try:
                usermail = User.objects.get(email = request.POST['email'])
                return render(request, 'signup.html', {'error': 'Email is already taken!'})
               except User.DoesNotExist:
                   # username is available
                   user = User.objects.create_user(username=request.POST['username'],
                                                   password=request.POST['password1'], email=request.POST['email'], )
                   auth.login(request, user)
                   return redirect('edit_profile')
        else:
            return render(request, 'signup.html', {'error2': 'Passwords do not match!'})

    else:
        #If request is get
        if request.user.is_authenticated:
            return render(request,'dashboard.html')
        else:
            return render(request, 'signup.html')

@login_required(login_url = '/accounts/login')
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required(login_url = '/accounts/login')
def profile(request):
    data = Score.objects.filter(applicant=request.user)
    return render(request, 'userprofile.html', {'scores': data})

def login(request):
    if request.method == 'POST':
        #This is to handle the case when the user is disabled for having multiple session
        try:
            user = User.objects.get(username = request.POST['username'])

            if user.is_active == False:
                user.is_active = True
                user.save()
            user = auth.authenticate(username = request.POST['username'], password= request.POST['password'])


            if user is not None:
                if user.profile.flag==True:
                    return render(request,'session_prevent.html',{'userroot':user.username})
                else:

                    user.profile.flag=True
                    user.profile.save()
                    auth.login(request, user)

                    item=Quiz.objects.all().order_by('-duration')
                    paginator = Paginator(item, 7)  # Show 1o quizzes per page
                    page = request.GET.get('page', 1)
                    try:
                        item = paginator.get_page(page)
                    except PageNotAnInteger:
                        item = paginator.get_page(1)
                    except EmptyPage:
                        item = paginator.get_page(paginator.num_pages)

                    return render(request,'dashboard.html',{'quiz_object':item})
            else:
                return render(request, 'home.html', {'error': 'Invalid Credentials! Please enter correct username and password.'})
        except User.DoesNotExist:
             return render(request, 'home.html', {'error': 'Invalid Credentials! Please enter correct username and password.'})
    else:
        return redirect('dashboard')

def logout(request):
    if request.method == 'POST':
        user = request.user
        user.profile.flag = False
        user.profile.save()
        auth.logout(request)
        return render(request,'home.html')

@login_required(login_url = '/accounts/login')
def dash(request):
    item = Quiz.objects.all().order_by('-duration')
    paginator = Paginator(item, 7)  # Show 1o quizzes per page
    page = request.GET.get('page', 1)
    try:
        item = paginator.get_page(page)
    except PageNotAnInteger:
        item = paginator.get_page(1)
    except EmptyPage:
        item = paginator.get_page(paginator.num_pages)

    return render(request, 'dashboard.html', {'quiz_object': item})

def public_profile(request, username):
    user = get_object_or_404(User, username = username)
    data = Score.objects.filter(applicant=user)
    return render(request, 'publicprofile.html', {'person': user, 'scores': data})

@login_required(login_url = '/accounts/login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Updates all active sessions
            messages.success(request, 'Your password was successfully updated!')
            return redirect('logout')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {
        'form': form
    })
    
    