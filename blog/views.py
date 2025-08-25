from django.shortcuts import render, get_object_or_404
from .models import Post

def index(request):
    posts = Post.objects.filter(status='published').order_by('-created_at')
    return render(request, 'blog/index.html', {'posts': posts})

def about(request):
    return render(request, 'blog/about.html')

def blog(request):
     return render(request, 'blog/blog.html')

def contact(request):
    return render(request, 'blog/contact.html')

# def post_detail(request, post_id):
#    post = get_object_or_404(Post, pk=post_id, status='published')
#    return render(request, 'blog/post.html', {'post': post})

def post_detail(request):
	return render(request, 'blog/post.html')