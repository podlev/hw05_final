from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверка, что у моделей корректно работает __str__."""
        objects_name = {
            self.post: self.post.text[:15],
            self.group: self.group.title
        }
        for object, str_value in objects_name.items():
            with self.subTest(object=object):
                self.assertEqual(object.__str__(), str_value)
