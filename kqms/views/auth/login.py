from django.shortcuts import render
from django.contrib.auth import authenticate, login,logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # This is the email
        password = request.POST.get('password')
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        print(f"[DEBUG] Email from POST: {username}")
        # print(f"[DEBUG] Password from POST: {password}")

        if user is None:
            print("Authentication failed")  # Check if authentication fails
            messages.error(request, 'Email atau password salah!')
            return render(request, 'auth/login.html')
        login(request, user)
        return redirect('redirect_by_role') 
    
    return render(request, 'auth/login.html')

def custom_logout(request):
    logout(request)
    
    # Redirect sesuai role atau asal halaman
    if request.user.is_staff:
        return redirect('/admin/login/')  # redirect ke admin login
    return redirect('login')  # redirect ke login biasa

@login_required
def redirect_by_role(request):
    user = request.user
    if user.groups.filter(name='AdminGelology').exists():
        return redirect('gelogy_dashboard')
    elif user.groups.filter(name='AdminMining').exists():
        return redirect('mining_dashboard')
    else:
        return redirect('home-geology')  # default