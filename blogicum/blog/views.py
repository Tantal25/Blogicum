from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView)
from django.urls import reverse
from django.utils import timezone

from .forms import PostForm, CommentForm
from blog.models import Post, Category, Comment


POST_ON_PAGE = 10

User = get_user_model()


def posts_filtration(posts, need_add_filtration=True):
    """
    Функция отвечающая за фильрацию постов по заданным критериям,
    создающая подсчет коментариев и сортирующая по дате публикации.
    """
    posts_with_comment_count = posts.annotate(
        comment_count=Count('comments')).order_by('-pub_date')
    if need_add_filtration:
        return posts_with_comment_count.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now())
    else:
        return posts_with_comment_count


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
        return HttpResponseRedirect(
            reverse('blog:post_detail',
                    kwargs={'post_id': self.kwargs['post_id']}))

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(OnlyAuthorMixin, PostMixin, DeleteView):
    """СBV отвечающая за удаление постов."""

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostListView(ListView):
    """СBV отвечающая за вывод опубликованных постов на главную страницу."""

    queryset = posts_filtration(Post.objects.all(), need_add_filtration=True)
    template_name = 'blog/index.html'
    paginate_by = POST_ON_PAGE


class PostDetailView(DetailView):
    """
    СBV отвечающая за просмотр конкретного поста,
    если он соответствует критериям.
    """

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if (self.object.category.is_published is False
                and self.object.author != self.request.user):
            raise Http404
        elif (self.object.is_published is False
                and self.object.author != self.request.user):
            raise Http404
        elif (self.object.pub_date >= timezone.now()
                and self.object.author != self.request.user):
            raise Http404
        else:
            context['form'] = CommentForm()
            context['comments'] = (
                self.object.comments.select_related('author'))
            return context


class PostCategoryView(ListView):
    """СBV отвечающая за вывод постов на по категориям."""

    model = Post
    form_class = PostForm
    template_name = 'blog/category.html'
    paginate_by = POST_ON_PAGE

    def get_context_data(self, **kwargs):
        category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True)
        self.object_list = posts_filtration(
            Post.objects.all(), need_add_filtration=True).filter(
                category=category)
        return dict(super().get_context_data(**kwargs), category=category)


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
        form.instance.post = get_object_or_404(Post, id=self.kwargs["post_id"])
        return super().form_valid(form)


class EditCommentView(OnlyAuthorMixin, CommentMixin, UpdateView):
    """СBV отвечающая за редактирование комментариев."""

    pass


class DeleteCommentView(OnlyAuthorMixin, CommentMixin, DeleteView):
    """СBV отвечающая за удаление комментариев."""

    pass


class ProfileView(ListView):
    """
    СBV отвечающая за отображение профилей пользователей
    и постов с ними связанных.
    """

    model = User
    template_name = 'blog/profile.html'
    slug_url_kwarg = 'username'
    slug_field = 'username'
    paginate_by = POST_ON_PAGE

    def get_context_data(self, **kwargs):
        profile = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user == profile:
            self.object_list = posts_filtration(
                profile.posts.all(), need_add_filtration=False)
        else:
            self.object_list = posts_filtration(profile.posts.all())
        return dict(super().get_context_data(**kwargs), profile=profile)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """СBV отвечающая за редактирование данных профиля пользователя."""

    model = User
    fields = 'username', 'first_name', 'last_name', 'email'
    template_name = 'blog/user.html'
    slug_url_kwarg = 'username'
    slug_field = 'username'

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])
