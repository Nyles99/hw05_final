import shutil
import tempfile

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django import forms
from posts.models import Group, Post, User, Follow
from django.core.cache import cache
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Testik',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test post',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса ."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
            'users/signup.html': reverse('users:signup'),
            'users/login.html': reverse('users:login'),
            'posts/post_create.html': reverse('posts:post_create'),
            'users/logged_out.html': reverse('users:logout'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': 'HasNoName'}),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы (в нём передаётся форма)
    def test_posts_create_page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected, f'поле {value} '
                                      + 'не того типа')
    # Проверяем, что словарь context страницы /task
    # в первом элементе списка object_list содержит ожидаемые значения

    def test_post_list_page_show_correct_context(self):
        """Шаблон task_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}
        )
        )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group.title
        post_text_0 = first_object.text
        post_image_0 = first_object.image
        self.assertEqual(post_group_0, 'Test group')
        self.assertEqual(post_text_0, 'Test post')
        self.assertEqual(post_image_0, 'posts/small.gif')

    # Проверяем, что словарь context страницы post/post_id
    # содержит ожидаемые значения

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group.title
        post_text_0 = first_object.text
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_group_0, 'Test group')
        self.assertEqual(post_text_0, 'Test post')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{self.post.id}'})))
        get_post = response.context.get('post')
        self.assertEqual(get_post.group.title, f'{self.group}')
        self.assertEqual(get_post.text, 'Test post')
        self.assertEqual(get_post.author.username, 'auth')
        self.assertEqual(get_post.id, self.post.id)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_image_0, 'posts/small.gif')
        self.assertEqual(response.context['author'].username, 'auth')
        self.assertEqual(post_text_0, 'Test post')

    def test_post_in_url(self):
        urls_names = [
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for value in urls_names:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(Post.objects.count(), 1)
                self.assertIn(
                    self.post,
                    response.context.get('page_obj')
                )

    def test_authorised_user_subscribe(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user,
                                  author=self.author).exists()
        )

    def test_authorised_user_subscribe(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'auth'})
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user,
                                  author=self.author).exists()
        )

    def test_new_post_appears_on_subscriber_page(self):
        self.subscribed_user = User.objects.create_user(username='new_user')
        self.subscribed_client = Client()
        self.subscribed_client.force_login(self.subscribed_user)
        self.subscribed_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        post = Post.objects.create(
            text='Test post',
            author=self.user,
            group=self.test_group
        )
        response = self.subscribed_client.get(reverse('posts:follow_index'))
        object_list = response.context.get('page_obj')
        self.assertIn(post, object_list)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        object_list = response.context.get('page_obj')
        self.assertNotIn(post, object_list)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Testik',
        )
        cls.posts = []
        for number in range(13):
            cls.posts.append(Post(
                author=cls.user,
                text=('Test post' + str(number)),
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}
        ))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{self.user.username}'}
        ))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{self.user.username}'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
