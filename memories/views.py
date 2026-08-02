import uuid

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import  authenticate
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from .models import AlbumShare, Image,UserProfile,Album,GuestAccess
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.db.models import Q



def album_detail(request, album_id):
    album = get_object_or_404(Album, id=album_id)

    is_owner = False
    is_guest = False
    guest_name = None
    profile = None

    if request.user.is_authenticated:
        profile = request.user.userprofile
        is_owner = album.owner == profile
        has_access = is_owner or AlbumShare.objects.filter(
            album=album, shared_with=profile, status='approved'
        ).exists()
    else:
        guest_tokens = request.session.get('guest_tokens', {})
        token = guest_tokens.get(str(album.id))
        guest_request = GuestAccess.objects.filter(token=token, album=album).first() if token else None
        is_guest = bool(guest_request and guest_request.status == 'approved')
        guest_name = guest_request.name if is_guest else None
        has_access = is_guest

    if not has_access:
        messages.error(request, "You don't have access to this album. Ask the owner for the invite link.")
        return redirect('landing')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Create an account to add photos to this album.')
            return redirect('album_detail', album_id=album.id)

        category = request.POST.get('category')
        note = request.POST.get('note')
        photo = request.FILES.get('photo')
        filter_style = request.POST.get('filter_style', 'none')
        date_taken = request.POST.get('date_taken')

        if photo:
            img = Image.objects.create(
                album=album, user=profile, image=photo,
                category=category, note=note, filter_style=filter_style,
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
        'album': album, 'is_owner': is_owner, 'is_guest': is_guest, 'guest_name': guest_name,
        'images': images, 'categories': Image.CATEGORY_CHOICES, 'filters': Image.FILTER_CHOICES,
        'current_category': category_filter, 'search_query': search_query,
        'total_memories': album.images.count(), 'category_counts': category_counts,
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
    next_url = request.POST.get('next') or request.GET.get('next') or 'my_albums'

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect(f"{reverse('signup')}?next={next_url}")

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect(f"{reverse('signup')}?next={next_url}")

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect(f"{reverse('signup')}?next={next_url}")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name,
        )

        UserProfile.objects.create(
            user=user,
            full_name=full_name,
        )

        auth_login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect(next_url)

    return render(request, 'signup.html', {'next': request.GET.get('next', '')})


@login_required
def my_albums(request):
    profile = request.user.userprofile
    albums = Album.objects.filter(
        Q(owner=profile) | Q(shares__shared_with=profile, shares__status='approved')
    ).distinct().order_by('-created_at')

    return render(request, 'dashboard.html', {
        'albums': albums,
        'total_memories': Image.objects.filter(album__in=albums).count(),
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


@login_required
def delete_album(request, pk):
    album = get_object_or_404(
        Album,
        pk=pk,
        owner=request.user.userprofile,
    )

    if request.method == "POST":
        album.delete()
        messages.success(request, "Album deleted successfully.")
        return redirect("my_albums")

    return render(request, 'delete_album.html', {
        "album": album
    })


@login_required
def share_album(request, album_id):
    album = get_object_or_404(Album, id=album_id, owner=request.user.userprofile)

    if request.method == 'POST':
        friend_username = request.POST.get('username')
        try:
            friend = UserProfile.objects.get(user__username=friend_username)
        except UserProfile.DoesNotExist:
            messages.error(request, 'No user with that username.')
            return redirect('share_album', album_id=album.id)

        if friend == album.owner:
            messages.error(request, "You can't share an album with yourself.")
            return redirect('share_album', album_id=album.id)

        share, created = AlbumShare.objects.get_or_create(
            album=album,
            shared_with=friend,
            defaults={'invited_by': request.user.userprofile}
        )
        if created:
            messages.success(request, f'Invite sent to {friend.user.username}.')
        else:
            messages.info(request, f'{friend.user.username} already has a pending or resolved invite.')
        return redirect('share_album', album_id=album.id)

    join_url = request.build_absolute_uri(reverse('join_via_link', kwargs={'token': album.share_token}))

    return render(request, 'share_album.html', {
        'album': album,
        'shares': album.shares.all(),
        'join_url': join_url,
        'pending_guest_requests': album.guest_requests.filter(status='pending'),
    })

@login_required
def pending_invites(request):
    invites = AlbumShare.objects.filter(
        shared_with=request.user.userprofile, status='pending'
    ).select_related('album', 'invited_by')
    return render(request, 'pending_invites.html', {'invites': invites})


@login_required
def respond_to_invite(request, share_id, action):
    if action not in ('approve', 'decline'):
        messages.error(request, 'Invalid action.')
        return redirect('pending_invites')

    share = get_object_or_404(AlbumShare, id=share_id, shared_with=request.user.userprofile)

    if action == 'approve':
        share.status = 'approved'
        messages.success(request, f'Joined "{share.album.title}"')
    else:
        share.status = 'declined'
        messages.info(request, 'Invite declined.')

    share.responded_at = timezone.now()
    share.save()
    return redirect('pending_invites')



from django.utils import timezone

def join_via_link(request, token):
    album = get_object_or_404(Album, share_token=token)

    # Authenticated users: unchanged, instant join
    if request.user.is_authenticated:
        profile = request.user.userprofile

        if album.owner == profile:
            messages.info(request, "This is your own album.")
            return redirect('album_detail', album_id=album.id)

        existing_share = AlbumShare.objects.filter(album=album, shared_with=profile).first()
        if existing_share and existing_share.status == 'approved':
            return redirect('album_detail', album_id=album.id)

        if request.method == 'POST':
            share, created = AlbumShare.objects.get_or_create(
                album=album,
                shared_with=profile,
                defaults={
                    'invited_by': album.owner,
                    'status': 'approved',
                    'responded_at': timezone.now(),
                }
            )
            if not created:
                share.status = 'approved'
                share.responded_at = timezone.now()
                share.save()
            messages.success(request, f'You joined "{album.title}"!')
            return redirect('album_detail', album_id=album.id)

        member_count = album.shares.filter(status='approved').count() + 1
        return render(request, 'join_album.html', {
            'album': album,
            'member_count': member_count,
        })

    # Anonymous users: request-based guest access
    guest_tokens = request.session.get('guest_tokens', {})
    existing_token = guest_tokens.get(str(album.id))
    existing_request = None
    if existing_token:
        existing_request = GuestAccess.objects.filter(token=existing_token, album=album).first()

    if existing_request:
        if existing_request.status == 'approved':
            request.session.setdefault('guest_access', {})[str(album.id)] = existing_request.name
            request.session.modified = True
            return redirect('album_detail', album_id=album.id)
        elif existing_request.status == 'pending':
            member_count = album.shares.filter(status='approved').count() + 1
            return render(request, 'join_album.html', {
                'album': album,
                'member_count': member_count,
                'request_pending': True,
                'guest_request_name': existing_request.name,
            })
        # declined: fall through to let them request again

    if request.method == 'POST':
        guest_name = request.POST.get('guest_name', '').strip()
        if guest_name:
            access = GuestAccess.objects.create(album=album, name=guest_name)
            guest_tokens[str(album.id)] = str(access.token)
            request.session['guest_tokens'] = guest_tokens
            request.session.modified = True
            messages.success(request, "Request sent! We'll let you know once it's approved.")
            member_count = album.shares.filter(status='approved').count() + 1
            return render(request, 'join_album.html', {
                'album': album,
                'member_count': member_count,
                'request_pending': True,
                'guest_request_name': guest_name,
            })
        else:
            messages.error(request, 'Please enter your name to continue.')

    member_count = album.shares.filter(status='approved').count() + 1
    return render(request, 'join_album.html', {
        'album': album,
        'member_count': member_count,
    })

@login_required
def regenerate_share_link(request, album_id):
    album = get_object_or_404(Album, id=album_id, owner=request.user.userprofile)
    album.share_token = uuid.uuid4()
    album.save()
    messages.success(request, 'Share link regenerated — the old link no longer works.')
    return redirect('share_album', album_id=album.id)

@login_required
def respond_guest_request(request, album_id, request_id, action):
    guest_request = get_object_or_404(
        GuestAccess, id=request_id, album_id=album_id, album__owner=request.user.userprofile
    )

    if action not in ('approve', 'decline'):
        messages.error(request, 'Invalid action.')
        return redirect('share_album', album_id=guest_request.album.id)

    guest_request.status = 'approved' if action == 'approve' else 'declined'
    guest_request.responded_at = timezone.now()
    guest_request.save()

    messages.success(request, f'Request from {guest_request.name} {"approved" if action == "approve" else "declined"}.')
    return redirect('share_album', album_id=guest_request.album.id)