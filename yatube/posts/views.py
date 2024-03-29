from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from .models import Group, Post, User, Follow
from posts.models import Post
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core.cache import cache
from django.urls import reverse


def paginator(request, post_list):
    paginator_obj = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    return paginator_obj.get_page(page_number)


@require_GET
def index(request):
    ''' Главная страница'''
    # Одна строка вместо тысячи слов на SQL:
    # в переменную posts будет сохранена выборка из 10 объектов модели Post,
    # отсортированных по полю pub_date по убыванию
    posts = cache.get('posts:index')
    if posts is None:
        posts = Post.objects.all()
        cache.set('posts:index', posts, timeout=20)
    page_obj = paginator(request, posts)
    # В словаре context отправляем информацию в шаблон
    context = {
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    ''' Страница cо списком страниц сообщества'''
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    template = 'posts/group_list.html'
    title = 'Здесь будет информация о группах проекта Yatube'
    page_obj = paginator(request, posts)
    # В словаре context отправляем информацию в шаблон
    context = {
        'title': title,
        'posts': posts,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    counter = posts.count()
    page_obj = paginator(request, posts)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'username': username,
        'posts': posts,
        'page_obj': page_obj,
        'counter': counter,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    all_posts = author.posts.all()
    counter = all_posts.count()
    form = CommentForm()
    context = {
        'post': post,
        'counter': counter,
        'author': author,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()

    return redirect('posts:profile', username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    form = PostForm(request.POST, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.pk)
    return render(request, 'posts/post_create.html',
                  {'form': form, 'post': post, 'author': author,
                   'is_edit': True}
                  )


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    return render(
        request,
        'core/404.html',
        {'path': request.path}, status=404)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/comment.html', {'form': form,
                  'post': post})


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')


def server_error(request):
    context = {}
    response = render(request, 'core/500.html', context=context)
    response.status_code = 500
    return response


@login_required
def follow_index(request):
    list_of_posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(list_of_posts, 20)
    page_namber = request.GET.get('page_obj')
    page = paginator.get_page(page_namber)
    context = {'page_obj': page}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            author=author,
            user=request.user
        )
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    is_follower.delete()
    return redirect('posts:profile', username=author)
