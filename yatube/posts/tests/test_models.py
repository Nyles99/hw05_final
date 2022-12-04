from django.contrib.auth import get_user_model

from django.test import TestCase

from ..models import Group, Post, User

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Testik',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test post',
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        have_correct_object_names = post.text[:15]
        self.assertEquals(have_correct_object_names, str(post))

    def test_models_have_correct_object_title(self):
        '''__str__  group - строка с group.title.'''
        group = PostModelTest.group
        have_correct_object_title = group.title
        self.assertEquals(have_correct_object_title, str(group))
