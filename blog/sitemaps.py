from django.contrib.sitemaps import Sitemap

from .models import Post


class PostSitemap(Sitemap):
    changfreq = 'monthly'
    priority = 0.7

    def items(self):
        return Post.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at