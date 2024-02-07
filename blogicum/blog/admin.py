from django.contrib import admin

from .models import Category, Location, Post, Comment


@admin.register(Post)
class BlogAdmin(admin.ModelAdmin):
    list_display = (
        'is_published',
        'title',
        'text',
        'location',
        'author',
        'category',
        'created_at'
    )
    list_editable = (
        'is_published',
        'location',
        'category'
    )
    search_fields = ('title',)
    list_filter = ('category',)
    list_display_links = ('title',)


admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment)

