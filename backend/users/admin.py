from django.contrib import admin
from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email',
                    'first_name', 'last_name', 'avatar')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email', 'first_name', 'last_name')
    filter_horizontal = ('groups', 'user_permissions')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личные данные', {
         'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('username',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'user__email',
                     'author__username', 'author__email')
    list_filter = ('user', 'author')
