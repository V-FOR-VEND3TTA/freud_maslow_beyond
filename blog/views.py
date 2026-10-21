import json
import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ContactForm, NewsletterForm
from .models import NewsletterSubscriber, Post

logger = logging.getLogger(__name__)

HOME_POST_COUNT = 5
POSTS_PER_PAGE = 10

DEFAULT_META_DESCRIPTION = (
    'An independent educational publishing project about psychology, '
    'motivation and human behaviour — explained clearly, sourced honestly, '
    'with limitations included.'
)


def index(request):
    published = Post.objects.filter(status='published').order_by('-created_at')
    posts = list(published[:HOME_POST_COUNT])
    return render(
        request,
        'blog/index.html',
        {
            'posts': posts,
            'total_published': published.count(),
            'meta_description': DEFAULT_META_DESCRIPTION,
        },
    )


def about(request):
    return render(
        request,
        'blog/about.html',
        {
            'meta_description': (
                'About Freud, Maslow, & Beyond — an independent educational '
                'publishing project, its mission, audience and editorial principles.'
            )
        },
    )


def blog(request):
    queryset = Post.objects.filter(status='published').order_by('-created_at')
    page_obj = Paginator(queryset, POSTS_PER_PAGE).get_page(request.GET.get('page'))
    return render(
        request,
        'blog/blog.html',
        {
            'page_obj': page_obj,
            'posts': page_obj.object_list,
            'meta_description': (
                'All published articles on psychology, motivation and human '
                'behaviour — the thinkers, the ideas, the evidence and the questions.'
            ),
        },
    )


def post_detail(request, year, month, day, slug):
    post = get_object_or_404(
        Post,
        status='published',
        slug=slug,
        created_at__year=year,
        created_at__month=month,
        created_at__day=day,
    )

    description = (post.excerpt or '').strip()
    if not description:
        description = (post.content.strip()[:157] + '…') if len(post.content.strip()) > 160 else post.content.strip()

    structured_data = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': post.title,
        'description': description,
        'inLanguage': 'en',
        'isAccessibleForFree': True,
        'datePublished': post.created_at.isoformat(),
        'dateModified': post.updated_at.isoformat(),
        'author': {
            '@type': 'Person',
            'name': post.author.get_full_name() or post.author.username,
        },
        'publisher': {
            '@type': 'Organization',
            'name': 'Freud, Maslow, & Beyond',
        },
        'mainEntityOfPage': request.build_absolute_uri(post.get_absolute_url()),
    }
    if post.featured_image:
        structured_data['image'] = request.build_absolute_uri(post.featured_image.url)

    # Escape '<' so content can never terminate the script element.
    json_ld = json.dumps(structured_data, indent=2).replace('<', '\\u003c')

    return render(
        request,
        'blog/post.html',
        {
            'post': post,
            'post_description': description,
            'json_ld': json_ld,
        },
    )


def post_detail_legacy(request, post_id):
    """Old /post/<id>/ links: redirect permanently to the canonical article URL."""
    post = get_object_or_404(Post, pk=post_id, status='published')
    return redirect(post.get_absolute_url(), permanent=True)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                send_mail(
                    subject=f"Freud, Maslow & Beyond — {data['subject']}",
                    message=(
                        f"From: {data['name']} <{data['email']}>\n\n"
                        f"{data['message']}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                )
            except SMTPException:
                logger.exception('Contact form email failed to send')
                messages.error(
                    request,
                    'Sorry — your message could not be sent. '
                    'Please try again a little later.',
                )
            else:
                messages.success(
                    request,
                    "Thanks — your message has been sent. "
                    "You'll get a reply as soon as possible.",
                )
            return redirect('contact')
    else:
        form = ContactForm()
    return render(
        request,
        'blog/contact.html',
        {
            'form': form,
            'meta_description': (
                'Get in touch with Freud, Maslow, & Beyond — questions, '
                'feedback, corrections and collaboration enquiries.'
            ),
        },
    )


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        NewsletterSubscriber.objects.get_or_create(
            email=form.cleaned_data['email'].lower()
        )
        messages.success(
            request,
            "You're subscribed. You'll get new articles by email — nothing else.",
        )
    else:
        messages.error(request, "That email address doesn't look valid.")
    return redirect(request.META.get('HTTP_REFERER') or 'index')


def robots(request):
    """robots.txt — allows crawling, points at the sitemap."""
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        f'Sitemap: {request.build_absolute_uri("/sitemap.xml")}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')