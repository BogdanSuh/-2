from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm, LoginForm, ProfileForm, PostForm
from .models import Post, Like, Comment


def home(request):
    posts = Post.objects.select_related('author') \
                        .prefetch_related('likes', 'comments') \
                        .order_by('-created_at')
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    return render(request, 'home.html', {'posts': posts})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Вы успешно зарегистрированы!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, "Вы вышли из аккаунта.")
    return redirect('home')


@login_required
def profile(request):
    user_posts = Post.objects.filter(author=request.user).order_by('-created_at')
    paginator = Paginator(user_posts, 10)
    page = request.GET.get('page')
    user_posts = paginator.get_page(page)
    return render(request, 'profile.html', {'user_posts': user_posts})


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён!")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})


@login_required
def delete_profile(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, "Ваш профиль и все данные удалены.")
        return redirect('home')
    return render(request, 'delete_profile.html')


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Пост опубликован!")
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.select_related('author').order_by('created_at')
    is_liked = False
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(user=request.user, post=post).exists()
    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
    })


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Пост обновлён!")
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Пост удалён.")
        return redirect('profile')
    return render(request, 'delete_post.html', {'post': post})


@login_required
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like_qs = Like.objects.filter(user=request.user, post=post)
    if like_qs.exists():
        like_qs.delete()
    else:
        Like.objects.create(user=request.user, post=post)
    return redirect('post_detail', pk=pk)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(post=post, author=request.user, content=content)
    return redirect('post_detail', pk=pk)


@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == 'POST':
        comment.content = request.POST.get('content', comment.content).strip()
        comment.save()
        return redirect('post_detail', pk=comment.post.pk)
    return render(request, 'edit_comment.html', {'comment': comment})


@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == 'POST':
        post_pk = comment.post.pk
        comment.delete()
        return redirect('post_detail', pk=post_pk)
    return render(request, 'delete_comment.html', {'comment': comment})
