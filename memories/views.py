from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import  authenticate
from django.contrib import messages
from django.db.models import Count
from .models import AlbumShare, Image,UserProfile,Album
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.db.models import Q

@login_required
def album_detail(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    profile = request.user.userprofile
    is_owner = album.owner == profile

    has_access = is_owner or AlbumShare.objects.filter(
        album=album, shared_with=profile, status='approved'
    ).exists()

    if not has_access:
        messages.error(request, "You don't have access to this album.")
        return redirect('my_albums')

    if request.method == 'POST':
        category = request.POST.get('category')
        note = request.POST.get('note')
        photo = request.FILES.get('photo')
        filter_style = request.POST.get('filter_style', 'none')
        date_taken = request.POST.get('date_taken')

        if photo:
            profile = UserProfile.objects.get(user=request.user)

            img = Image.objects.create(
                album=album,
                user=request.user.userprofile,
                image=request.FILES['photo'],
                category=request.POST.get('category'),
                note=request.POST.get('note')
            )

            if date_taken:
                img.date_taken = date_taken
                img.save()
            messages.success(request, 'Memory preserved successfully!')
            return redirect('album_detail', album_id=album.id)
        else:
            messages.error(request, 'Please select a photo to upload.')

    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    images = album.images.all().order_by('-uploaded_at')
    if category_filter:
        images = images.filter(category=category_filter)
    if search_query:
        images = images.filter(note__icontains=search_query)

    category_counts = album.images.values('category').annotate(count=Count('id')).order_by('-count')

    return render(request, 'album_detail.html', {
        'album': album,
        'is_owner': is_owner,
        'images': images,
        'categories': Image.CATEGORY_CHOICES,
        'filters': Image.FILTER_CHOICES,
        'current_category': category_filter,
        'search_query': search_query,
        'total_memories': album.images.count(),
        'category_counts': category_counts,
    })



@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next') or 'my_albums'

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Logged in successfully')
            return redirect(next_url)
        else:
            messages.error(request, 'Incorrect login credentials, try again')
            return redirect('login')

    next_url = request.GET.get('next', '')
    return render(request, 'login.html', {'next': next_url})




def landing(request):
    return render(request, 'landing.html')


def works(request):
    return render(request, 'works.html')



@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name,   # optional
        )

        UserProfile.objects.create(
            user=user,
            full_name=full_name,
        )

        auth_login(request, user)

        messages.success(request, 'Account created successfully!')
        return redirect('my_albums')

    return render(request, 'signup.html')



@login_required
def my_albums(request):
    profile = request.user.userprofile
    albums = Album.objects.filter(
        Q(owner=profile) | Q(shares__shared_with=profile, shares__status='approved')
    ).distinct().order_by('-created_at')

    return render(request, 'dashboard.html', {
        'albums': albums,
        'total_memories': Image.objects.filter().count(),
        'pending_invite_count': AlbumShare.objects.filter(shared_with=profile, status='pending').count(),
    })
    
    
    
@login_required
def create_album(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')

        if not title:
            messages.error(request, 'Album needs a title.')
            return redirect('create_album')

        album = Album.objects.create(
            owner=request.user.userprofile,
            title=title,
            description=description
        )
        messages.success(request, f'"{album.title}" created!')
        return redirect('album_detail', album_id=album.id)

    return render(request, 'create_album.html')