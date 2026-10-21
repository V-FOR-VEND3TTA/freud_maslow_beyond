from datetime import datetime

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import NewsletterSubscriber, Post

# Deterministic publication date used by the fixtures below.
FIXED_DATE = datetime(2025, 5, 4, 12, 0, 0)


def make_post(slug, title=None, status='published'):
    """Create a post with a deterministic created_at/updated_at (auto_now_add would override)."""
    author, _ = User.objects.get_or_create(username='author')
    post = Post.objects.create(
        title=title or slug.replace('-', ' ').title(),
        slug=slug,
        content=f'Body of {slug}.\n\nSecond paragraph of {slug}.',
        excerpt=f'Excerpt for {slug}.',
        author=author,
        status=status,
    )
    Post.objects.filter(pk=post.pk).update(created_at=FIXED_DATE, updated_at=FIXED_DATE)
    post.refresh_from_db()
    return post


class PageTests(TestCase):
    def test_home_page_renders_published_only(self):
        published = make_post('published-post', title='Published Post')
        make_post('draft-post', title='Draft Post', status='draft')
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/index.html')
        self.assertContains(response, published.title)
        self.assertNotContains(response, 'Draft Post')

    def test_home_page_limits_posts_and_counts_total(self):
        for i in range(6):
            make_post(f'post-{i}', title=f'Post {i}')
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context['posts']), 5)
        self.assertEqual(response.context['total_published'], 6)

    def test_home_page_empty_state(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['posts'], [])

    def test_about_page_renders(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/about.html')

    def test_contact_page_renders_form(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/contact.html')
        self.assertContains(response, 'name="email"')

    def test_blog_page_lists_publishes_and_paginates(self):
        for i in range(11):
            make_post(f'article-{i}', title=f'Article {i}')
        make_post('hidden-draft', title='Hidden Draft', status='draft')

        response = self.client.get(reverse('blog'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 10)
        self.assertNotContains(response, 'Hidden Draft')

        response = self.client.get(reverse('blog') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 1)

        # Invalid page numbers must not crash (Paginator.get_page falls back).
        response = self.client.get(reverse('blog') + '?page=notanumber')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('blog') + '?page=999')
        self.assertEqual(response.status_code, 200)

    def test_blog_empty_state(self):
        response = self.client.get(reverse('blog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No articles published yet')

    def test_unknown_url_uses_404_template(self):
        response = self.client.get('/definitely-not-a-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')


class PostDetailTests(TestCase):
    def test_published_post_detail_renders(self):
        post = make_post('my-article', title='My Article')
        response = self.client.get(post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post.html')
        self.assertEqual(response.context['post'], post)
        self.assertContains(response, 'My Article')
        # Paragraphs are preserved from plain-text content.
        self.assertContains(response, '<p>Body of my-article.</p>', html=True)
        # Structured data present and valid-looking.
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, '"@type": "Article"')

    def test_draft_post_detail_is_404(self):
        post = make_post('secret-draft', status='draft')
        response = self.client.get(post.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_wrong_slug_is_404(self):
        post = make_post('right-slug')
        url = post.get_absolute_url().replace('right-slug', 'wrong-slug')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_wrong_date_is_404(self):
        post = make_post('dated-post')
        url = post.get_absolute_url().replace('/2025/5/4/', '/2025/5/5/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_legacy_post_id_url_redirects_to_canonical(self):
        post = make_post('old-link-target')
        response = self.client.get(f'/post/{post.pk}/')
        self.assertRedirects(
            response,
            post.get_absolute_url(),
            status_code=301,
            target_status_code=200,
        )

    def test_legacy_url_for_draft_is_404(self):
        post = make_post('draft-target', status='draft')
        response = self.client.get(f'/post/{post.pk}/')
        self.assertEqual(response.status_code, 404)


class ContactTests(TestCase):
    def test_valid_contact_form_sends_email(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Jane Reader',
                'email': 'jane@example.com',
                'subject': 'Question about an article',
                'message': 'Thanks for the clear explanation.',
            },
            follow=True,
        )
        self.assertEqual(response.redirect_chain, [(reverse('contact'), 302)])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Question about an article', mail.outbox[0].subject)
        self.assertIn('jane@example.com', mail.outbox[0].body)
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level_tag, 'success')

    def test_invalid_contact_form_sends_nothing(self):
        response = self.client.post(
            reverse('contact'),
            {'name': 'X', 'email': 'not-an-email', 'subject': '', 'message': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFormError(
            response.context['form'], 'email', 'Enter a valid email address.'
        )


class NewsletterTests(TestCase):
    def test_subscribe_requires_post(self):
        response = self.client.get(reverse('newsletter_subscribe'))
        self.assertEqual(response.status_code, 405)

    def test_valid_subscribe_creates_subscriber(self):
        response = self.client.post(
            reverse('newsletter_subscribe'),
            {'email': 'Reader@Example.com'},
            HTTP_REFERER=reverse('index'),
            follow=True,
        )
        self.assertEqual(response.redirect_chain, [(reverse('index'), 302)])
        self.assertTrue(
            NewsletterSubscriber.objects.filter(email='reader@example.com').exists()
        )
        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level_tag, 'success')

    def test_duplicate_subscribe_is_idempotent(self):
        for _ in range(2):
            self.client.post(
                reverse('newsletter_subscribe'),
                {'email': 'reader@example.com'},
                HTTP_REFERER=reverse('index'),
            )
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_invalid_email_is_rejected(self):
        self.client.post(
            reverse('newsletter_subscribe'),
            {'email': 'nope'},
            HTTP_REFERER=reverse('index'),
        )
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)


class DiscoverabilityTests(TestCase):
    def test_sitemap_lists_only_published_posts(self):
        published = make_post('listed-post')
        make_post('unlisted-draft', status='draft')
        response = self.client.get(reverse('sitemap'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, published.get_absolute_url())
        self.assertNotContains(response, 'unlisted-draft')

    def test_robots_txt_points_at_sitemap(self):
        response = self.client.get(reverse('robots'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, 'Disallow: /admin/')
        self.assertContains(response, f'Sitemap: {response.wsgi_request.build_absolute_uri("/sitemap.xml")}')

    def test_article_pages_carry_meta_description(self):
        post = make_post('described-post', title='Described Post')
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'rel="canonical"')