from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.author = User.objects.create_user(username='testauthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client.force_login(self.author)
        cache.clear()

    def test_urls_available_to_all_user(self):
        """Страницы по адресу /, group/<slug>/,
        profile/<username>/, posts/<post_id>/
        доступны любому пользователю.
        """
        guest_url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.group.slug,)),
            reverse('posts:profile', args=(self.user,)),
            reverse('posts:post_detail', args=(self.post.pk,))]
        for url in guest_url_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_available_to_autorized_users(self):
        """Страницы по адресам /posts/post_id/comment/, /create/
        доступны авторизованным пользователям.
        """
        urls_status_names = {
            reverse('posts:add_comment',
                    args=(self.post.pk,)): self.authorized_client,
            reverse('posts:post_create'): self.authorized_client
        }
        for url, client in urls_status_names.items():
            with self.subTest(url=url, client=client):
                response = client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_not_available_to_not_autorized_users(self):
        """Страницы по адресам /posts/post_id/edit/,
        /posts/post_id/comment/, /create/
        недоступны неавторизованным пользователям.
        """
        urls_redirects_names = {
            reverse('posts:post_update', args=(self.post.pk,)):
            f'/auth/login/?next=/posts/{self.post.pk}/edit/',
            reverse('posts:add_comment', args=(self.post.pk,)):
            f'/auth/login/?next=/posts/{self.post.pk}/comment/',
            reverse('posts:post_create'): '/auth/login/?next=/create/'
        }
        for url, url_redirect in urls_redirects_names.items():
            with self.subTest(url=url, url_redirect=url_redirect):
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, url_redirect)

    def test_post_edit_url_available_to_author(self):
        """Страница по адресу /posts/post_id/edit/
        доступна автору.
        """
        response = self.author_client.get(
            reverse('posts:post_update', args=(self.post.pk,)))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_not_available_to_not_author(self):
        """Страница по адресу /posts/post_id/edit/
        перенаправит пользователя на являющегося автором.
        на /posts/post_id/
        """
        response = self.authorized_client.get(
            reverse('posts:post_update', args=(self.post.pk,)),
            follow=True)
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_unexisting_page_return_404(self):
        """Страница по несуществующему адресу возвращает 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)
