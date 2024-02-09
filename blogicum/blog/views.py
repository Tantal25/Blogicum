from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView)
from django.urls import reverse
from django.utils import timezone

from .forms import PostForm, CommentForm
from blog.models import Post, Category, Comment


POST_ON_PAGE = 10

User = get_user_model()


def get_posts_and_filatrate(filtration=False, annotation_and_order=False):
    """
    Функция отвечающая за фильтрацию постов по заданным критериям,
    создающая подсчет коментариев и сортирующая по дате публикации.
    """
    posts = Post.objects.select_related('author', 'category', 'location')
    if filtration is True:
        posts = posts.filter(is_published=True, category__is_published=True,
                             pub_date__lte=timezone.now())
    if annotation_and_order is True:
        posts = posts.annotate(
            comment_count=Count('comments')).order_by('-pub_date')
    return posts


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин переопределяющий встроенную test_func,
    который не дает редактировать, удалять посты никому кроме автора.
    """

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostMixin:
    """Миксин задающий атрибуты для CBV связанных с постом."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    """СBV отвечающая за создание постов."""

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostUpdateView(OnlyAuthorMixin, PostMixin, UpdateView):
    """СBV отвечающая за редактирование постов."""

    def handle_no_permission(self):
        return redirect('blog:post_detail', self.kwargs['post_id'])

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(OnlyAuthorMixin, PostMixin, DeleteView):
    """СBV отвечающая за удаление постов."""

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostListView(ListView):
    """СBV отвечающая за вывод опубликованных постов на главную страницу."""

    queryset = get_posts_and_filatrate(
        filtration=True, annotation_and_order=True)
    template_name = 'blog/index.html'
    paginate_by = POST_ON_PAGE


class PostDetailView(DetailView):
    """
    СBV отвечающая за просмотр конкретного поста,
    если он соответствует критериям.
    """

    queryset = get_posts_and_filatrate()
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        object = super().get_object()
        if object.author != self.request.user and (
            object.category.is_published is False
            or object.is_published is False
            or object.pub_date >= timezone.now()
        ):
            raise Http404
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author'))
        return context


class PostCategoryView(ListView):
    """СBV отвечающая за вывод постов на по категориям."""

    queryset = get_posts_and_filatrate(
        filtration=True, annotation_and_order=True)
    template_name = 'blog/category.html'
    paginate_by = POST_ON_PAGE

    def get_queryset(self):
        return self.queryset.filter(category=self.get_category())

    def get_context_data(self, **kwargs):
        return dict(super().get_context_data(**kwargs),
                    category=self.get_category())

    def get_category(self):
        return get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True)


class CommentMixin:
    """Миксин задающий атрибуты для CBV связанных с комментариями к посту."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.object.post_id}
        )


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    """СBV отвечающая за создание комментариев."""

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return super().form_valid(form)


class EditCommentView(OnlyAuthorMixin, CommentMixin, UpdateView):
    """СBV отвечающая за редактирование комментариев."""

    pk_url_kwarg = 'comment_id'


class DeleteCommentView(OnlyAuthorMixin, CommentMixin, DeleteView):
    """СBV отвечающая за удаление комментариев."""

    pk_url_kwarg = 'comment_id'


class ProfileView(ListView):
    """
    СBV отвечающая за отображение профилей пользователей
    и постов с ними связанных.
    """

    model = User
    template_name = 'blog/profile.html'
    paginate_by = POST_ON_PAGE
    slug_url_kwargs = 'username'
    slug_field = 'username'

    def get_queryset(self):
        profile = self.get_profile()
        return get_posts_and_filatrate(
            filtration=self.request.user != profile,
            annotation_and_order=True).filter(author=profile)

    def get_context_data(self, **kwargs):
        return dict(super().get_context_data(**kwargs),
                    profile=self.get_profile())

    def get_profile(self):
        return get_object_or_404(User, username=self.kwargs['username'])


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """СBV отвечающая за редактирование данных профиля пользователя."""

    model = User
    fields = 'username', 'first_name', 'last_name', 'email'
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])
