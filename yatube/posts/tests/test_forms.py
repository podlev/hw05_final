import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.author = User.objects.create_user(username='testauthor')
        cls.post = Post.objects.create(author=cls.author, text='Простой пост')

    def setUp(self):
        self.author_client = Client()
        self.authorized_client = Client()
        self.author_client.force_login(self.author)
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает Post."""
        posts_count = Post.objects.count()
        temp_image = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                      b'\x01\x00\x80\x00\x00\x00\x00\x00'
                      b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                      b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                      b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                      b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(name='temp_image.gif',
                                      content=temp_image,
                                      content_type='image/gif')
        form_data = {
            'author': self.author,
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.author_client.post(reverse('posts:post_create'),
                                           data=form_data,
                                           follow=True)
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.author}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter().exists())
        self.assertTrue(
            Post.objects.filter(text=form_data['text'],
                                author=self.author,
                                image='posts/temp_image.gif').exists())

    def test_update_post(self):
        """Валидная форма изменяет Post."""
        posts_count = Post.objects.count()
        temp_image = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                      b'\x01\x00\x80\x00\x00\x00\x00\x00'
                      b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                      b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                      b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                      b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(name='temp_image.gif',
                                      content=temp_image,
                                      content_type='image/gif')
        form_data = {
            'author': self.author,
            'text': 'ИЗМЕНЕННЫЙ пост',
            'image': uploaded,
        }
        response = self.author_client.post(reverse(
            'posts:post_update', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())
        self.assertTrue(
            Post.objects.filter(text=form_data['text'],
                                author=self.author,
                                image='posts/temp_image.gif').exists())

    def test_add_comment(self):
        """Валидная форма создает комментарий."""
        form_data = {
            'post': self.post.pk,
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.pk}))
        self.assertTrue(self.post.comments.filter(
            text=form_data['text']).exists())
