import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User
from ..utils import POSTS_COUNT

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testauthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост',
                                       group=cls.group)

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_page_uses_correct_template(self):
        """URL-адрес использует соответсвующий шаблон."""
        pages_template_names = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_create'):
            'posts/create_post.html',
            reverse('posts:post_update', kwargs={'post_id': self.post.pk}):
            'posts/create_post.html'
        }
        for reverse_name, template in pages_template_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostContextTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testauthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        temp_image = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                      b'\x01\x00\x80\x00\x00\x00\x00\x00'
                      b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                      b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                      b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                      b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(name='temp_image.gif',
                                      content=temp_image,
                                      content_type='image/gif')
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост',
                                       group=cls.group,
                                       image=uploaded)
        cls.comment = Comment.objects.create(post=cls.post,
                                             author=cls.author,
                                             text='Тестовый коммент'
                                             )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_show_correct_context(self):
        """Страница index, group_list,
        profile, post_detail сформирована с правильным контекстом.
        """
        page_context_names = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', args=(self.group.slug, )): 'page_obj',
            reverse('posts:profile', args=(self.author, )): 'page_obj',
            reverse('posts:post_detail', args=(self.post.pk, )): 'post'
        }

        for url, keyword in page_context_names.items():
            with self.subTest(url=url, keyword=keyword):
                response = self.author_client.get(url)
                if keyword == 'page_obj':
                    obj = response.context[keyword][0]
                else:
                    obj = response.context[keyword]
                post_context_names = {
                    obj.text: self.post.text,
                    obj.group: self.post.group,
                    obj.author: self.post.author,
                    obj.image: self.post.image,
                    obj.comments.get(): self.comment
                }
                for post_context, test_context in post_context_names.items():
                    self.assertEqual(post_context, test_context)


class PostCreateUpdateTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testauthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post_page_show_correct_context(self):
        """Страница create_post, post_update
        сформирована с правильным контекстом."""
        page_names = [
            reverse('posts:post_create'),
            reverse('posts:post_update', kwargs={'post_id': self.post.pk})
        ]
        for url in page_names:
            response = self.author_client.get(url)
            for value, expected in self.form_fields.items():
                with self.subTest(value=value, expected=expected):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
            if response.context['is_edit']:
                self.assertEqual(response.context['post'].text, self.post.text)
                self.assertEqual(response.context['post'].group,
                                 self.post.group)


class PostPaginatorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testauthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.POSTS_DELTA = 3
        for post_number in range(POSTS_COUNT + cls.POSTS_DELTA):
            cls.post = Post.objects.create(
                author=cls.author,
                text=f'Тестовый пост {post_number}',
                group=cls.group,
            )

    def setUp(self):
        cache.clear()

    def test_paginator(self):
        """Страница index, group_list, profile
        выводит количество постов равное POSTS_COUNT."""
        posts_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author})
        ]
        for url in posts_pages:
            for page_number in (1, 2):
                with self.subTest(url=url, page_number=page_number):
                    response = self.client.get(url, {'page': page_number})
                    self.assertEqual(
                        len(response.context['page_obj']),
                        POSTS_COUNT if page_number == 1 else self.POSTS_DELTA)


class PostGroupProfileTests(TestCase):

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
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост',
                                       group=cls.group)
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )

    def setUp(self):
        cache.clear()

    def test_index_group_list_profile_page_contains_one_record(self):
        """Страницы index, group_list, profile содержат добавленный пост."""
        page_names_with_post = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.group.slug, )),
            reverse('posts:profile', args=(self.author, ))
        ]

        for url in page_names_with_post:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(len(response.context['page_obj']), 1)
                self.assertEqual(response.context['page_obj'][0].pk,
                                 self.post.pk)

    def test_index_group_list_profile_page_no_contains_record(self):
        """Страницы group_list, profile не содержат не добавленный пост."""
        page_names_without_post = [
            reverse('posts:group_list', args=(self.group_2.slug, )),
            reverse('posts:profile', args=(self.user, ))
        ]

        for url in page_names_without_post:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(len(response.context['page_obj']), 0)


class FollowTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='testuser1')
        cls.user2 = User.objects.create_user(username='testuser2')
        cls.author = User.objects.create_user(username='testauthor')
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост')

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.user1)
        self.unfollower_client = Client()
        self.unfollower_client.force_login(self.user2)
        cache.clear()

    def test_profile_follow(self):
        """Авторизованный пользователь может
        подписываться/отписываться на других пользователей."""
        self.follower_client.get(
            reverse('posts:profile_follow', args=(self.author,)))
        self.assertTrue(Follow.objects.filter(
            user=self.user1, author=self.author).exists())
        self.follower_client.get(
            reverse('posts:profile_unfollow', args=(self.author,)))
        self.assertFalse(Follow.objects.filter(
            user=self.user1, author=self.author).exists())

    def test_follow_index_contains_records(self):
        """Новая запись пользователя
        появляется в ленте тех, кто на него подписан и
        не появляется в ленте тех, кто не подписан."""
        self.follower_client.get(
            reverse('posts:profile_follow', args=(self.author,)))
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0].pk,
                         self.post.pk)
        response = self.unfollower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)


class CacheTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testauthor')
        cls.post = Post.objects.create(author=cls.author,
                                       text='Тестовый пост')

    def test_posts_cache(self):
        """Cписок записей на странице index хранится
        в кеше и обновляется раз в 20 секунд ."""
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, self.post.text)
        Post.objects.get(pk=self.post.pk).delete()
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, self.post.text)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotContains(response, self.post.text)
