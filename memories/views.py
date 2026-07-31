from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import  authenticate
from django.contrib import messages
from django.db.models import Count
from .models import Image
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import authenticate, login as auth_login


@login_required
@ratelimit(key='user', rate='10/m', method='GET', block=True)
def osei(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        note = request.POST.get('note')
        photo = request.FILES.get('photo')
        filter_style = request.POST.get('filter_style', 'none')
        date_taken = request.POST.get('date_taken')

        if photo:
            img = Image.objects.create(
                user=request.user,
                category=category,
                note=note,
                image=photo,
                filter_style=filter_style
            )
            if date_taken:
                img.date_taken = date_taken
                img.save()
            messages.success(request, 'Memory preserved successfully!')
            return redirect('osei')
        else:
            messages.error(request, 'Please select a photo to upload.')

    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    images = Image.objects.all()[:6]
    if category_filter:
        images = images.filter(category=category_filter)
    if search_query:
        images = images.filter(note__icontains=search_query)

    total_memories = Image.objects.count()
    category_counts = Image.objects.values('category').annotate(count=Count('id')).order_by('-count')

    context = {
        'images': images,
        'categories': Image.CATEGORY_CHOICES,
        'filters': Image.FILTER_CHOICES,
        'current_category': category_filter,
        'search_query': search_query,
        'total_memories': total_memories,
        'category_counts': category_counts,
    }
    return render(request, 'oseiantwi.html', context)



@ratelimit(key='ip', rate='10/m', method='POST', block=True)  # limit POST attempts
def oslogin(request):  
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next') or '/'
        
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)  
            messages.success(request, 'Logged in successfully')
            return redirect(next_url)
        else:
            messages.error(request, 'Incorrect login credentials, try again')
            return redirect('oslogin')
    
    return render(request, 'login.html')