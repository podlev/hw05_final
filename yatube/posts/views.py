from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Group, Follow, Post, User
from .utils import get_page_obj


@cache_page(200, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('group', 'author').all()
    page_obj = get_page_obj(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_post(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = page_obj = get_page_obj(request, post_list)
    context = {'page_obj': page_obj, 'group': group}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    page_obj = page_obj = get_page_obj(request, post_list)

    if (request.user.is_authenticated
        and Follow.objects.filter(user=request.user,
                                  author=author).exists()):
        following = True
    else:
        following = False
    context = {'author': author,
               'page_obj': page_obj,
               'following': following}
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related(), pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {'title': post.text,
               'post': post,
               'form': form,
               'comments': comments}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        context = {'form': form, 'is_edit': False}
        return render(request, 'posts/create_post.html', context)
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if not form.is_valid():
        context = {'form': form, 'post': post, 'is_edit': True}
        return render(request, 'posts/create_post.html', context)
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_obj(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (request.user != author
            and not Follow.objects.filter(user=request.user,
                                          author=author).exists()):
        Follow.objects.create(user=request.user,
                              author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user,
                                   author=author)
    if follow:
        follow.delete()
    return redirect('posts:profile', author)
