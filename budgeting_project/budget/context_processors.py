from .models import UserProfile


def user_profile(request):
    if not request.user.is_authenticated:
        return {}
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {
        'user_profile': profile,
        'user_display_name': profile.get_display_name(),
        'user_avatar_url': profile.avatar.url if profile.avatar else None,
    }
