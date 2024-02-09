from django.urls import path, include

from . import views

app_name = 'blog'

post_and_comments_urls = [
    path('<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('create/', views.PostCreateView.as_view(), name='create_post'),
    path('<int:post_id>/edit/',
         views.PostUpdateView.as_view(),
         name='edit_post'),
    path('<int:post_id>/delete/',
         views.PostDeleteView.as_view(),
         name='delete_post'),
    path('<int:post_id>/comment/',
         views.CommentCreateView.as_view(),
         name='add_comment'),
    path('<int:post_id>/edit_comment/<int:comment_id>',
         views.EditCommentView.as_view(),
         name='edit_comment'),
    path('<int:post_id>/delete_comment/<int:comment_id>',
         views.DeleteCommentView.as_view(),
         name='delete_comment'),
]

urlpatterns = [
    path('',
         views.PostListView.as_view(),
         name='index'),
    path('posts/', include(post_and_comments_urls)),
    path('category/<slug:category_slug>/',
         views.PostCategoryView.as_view(),
         name='category_posts'),
    path('profile_edit/',
         views.ProfileEditView.as_view(),
         name='edit_profile'),
    path('profile/<slug:username>/',
         views.ProfileView.as_view(),
         name='profile'),
]
