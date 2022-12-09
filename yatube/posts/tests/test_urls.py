from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from posts.models import Group, Post, User
from django.urls import reverse

User = get_user_model()
Index = reverse('posts:index')
Create = reverse('posts:post_create')
Profile = reverse('posts:profile', kwargs={'username': 'HasNoName'})
Edit_1 = reverse('posts:post_edit', kwargs={'post_id': '1'})
GRoup = reverse('posts:group_list', kwargs={'slug': 'test-slug'})
Post_1 = reverse('posts:post_detail', kwargs={'post_id': '1'})
Post_404 = reverse('posts:post_detail', kwargs={'post_id': '404'})
ABOUT_A = reverse('about:author')
ABOUT_T = reverse('about:author')


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

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_urls_status_code(self):
        urls_names = [
            [Index, self.guest_client, 200],
            [Create, self.guest_client, 302],
            [GRoup, self.guest_client, 200],
            [Post_1, self.guest_client, 200],
            [Profile, self.guest_client, 200],
            [ABOUT_A, self.guest_client, 200],
            [ABOUT_T, self.guest_client, 200],
            [Edit_1, self.guest_client, 302],
            [Edit_1, self.authorized_client, 200],
            [Create, self.authorized_client, 200],
            [Post_404, self.guest_client, 404],
            [Post_404, self.authorized_client, 404],
        ]
        for url, client, status in urls_names:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, status)

    def test_post_url_uses_correct_template(self):
        """Проверка шаблона для адреса ."""
        template_about_urls_name = {
            Index: 'posts/index.html',
            Create: 'posts/post_create.html',
            GRoup: 'posts/group_list.html',
            Profile: 'posts/profile.html',
            Post_1: 'posts/post_detail.html',
            Edit_1: 'posts/post_create.html',
        }
        for adress, template in template_about_urls_name.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
