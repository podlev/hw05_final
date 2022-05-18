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
        self.guest_client = Client()
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
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_post_edit_url_not_available_to_not_authorized_user(self):
        """Страница по адресу /posts/post_id/edit/
        перенаправит неавторизованного пользователя
        на auth/login/?next=/posts/post_id/edit/.
        """
        response = self.guest_client.get(
            reverse('posts:post_update', args=(self.post.pk,)),
            follow=True)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_comment_url_not_available_to_not_authorized_user(self):
        """Переход по адресу /posts/post_id/comment/
        перенаправит неавторизованного пользователя
        на auth/login/?next=/posts/post_id/comment/.
        """
        response = self.guest_client.get(
            reverse('posts:add_comment', args=(self.post.pk,)),
            follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )

    def test_comment_url_available_to_authorized_user(self):
        """Страница по адресу /posts/post_id/comment/
        доступна авторизованному пользователю.
        """
        response = self.client.get(
            reverse('posts:add_comment', args=(self.post.pk,)),
            follow=True)
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_not_available_to_not_author(self):
        """Страница по адресу /posts/post_id/edit/
        перенаправит пользователя на являющегося автором.
        на /posts/post_id/
        """
        response = self.authorized_client.get(
            reverse('posts:post_update', args=(self.post.pk,)),
            follow=True)
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_post_edit_url_available_to_author(self):
        """Страница по адресу /posts/post_id/edit/
        доступна автору.
        """
        response = self.author_client.get(
            reverse('posts:post_update', args=(self.post.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_post_create_url_not_available_to_not_authorized_user(self):
        """Страница по адресу /posts/post_id/
        перенаправит неавторизованного пользователя
        на /auth/login/?next=/create/.
        """
        response = self.guest_client.get(
            reverse('posts:post_create'), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_create_url_available_to_authorized_user(self):
        """Страница по адресу /posts/post_id/
        доступна авторизованному пользователю.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, 200)

    def test_unexisting_page_return_404(self):
        """Страница по несуществующему адресу возвращает 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

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
