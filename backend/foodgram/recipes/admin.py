from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Tag, Ingredient, Recipes, IngredientRecipe,
    Favorite, ListToBuy, User, Subscript
)


@admin.register(User)
class UserAdminConfig(UserAdmin):
    default_site = 'foodgram.users.admin.AdminAreaSite'
    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
        'bio',
        'role',
        'is_active',
        'date_joined'
    )
    search_fields = ('username', 'email')
    list_filter = ('is_superuser', 'is_staff')
    fieldsets = (
        ('Key fields', {
            'fields': ('username', 'email', 'password', 'role')
        }),
        ('Personal info', {
            'fields': (
                'first_name', 'last_name', 'bio'
            ), 'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff',),
        }),
        ('Date joined', {
            'fields': ('date_joined',)
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('extrapretty',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    def has_module_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        if obj:
            return request.user.is_staff and not obj.is_staff
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if obj:
            return request.user.is_staff and not obj.is_staff
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def save_model(self, request, obj, form, change):
        if isinstance(obj, User):
            super().save_model(request, obj, form, change)
            user_role = obj.role
            if user_role == User.ADMIN:
                obj.is_staff = True
            else:
                obj.is_staff = False
            obj.save()
        else:
            super().save_model(request, obj, form, change)


class PermissionsAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff


@admin.register(Tag)
class TagAdminConfig(PermissionsAdmin):
    list_display = (
        'pk',
        'name',
        'color',
        'slug'
    )
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdminConfig(PermissionsAdmin):
    list_display = (
        'pk',
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)


@admin.register(IngredientRecipe)
class IngredientRecipeAdminConfig(PermissionsAdmin):
    list_display = (
        'pk',
        'ingredient',
        'amount',
        'recipe',
        'recipe_id',
    )
    search_fields = ('ingredient', 'recipe')
    list_filter = ('ingredient', 'recipe')


class RecipesAdmin(PermissionsAdmin):
    list_display = ('pk', 'name', 'author')
    list_filter = ('tags', 'name', 'author')
    readonly_fields = ('fav_count', 'pub_date')
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'fav_count', 'name', 'author',
                'text', 'image', 'tags', 'pub_date', 'cooking_time'
            )
        }),

    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            kwargs["queryset"] = Tag.objects.filter(user=request.user)
        return super(RecipesAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    def fav_count(self, obj):
        return obj.favorite.all().count()
    fav_count.short_description = 'Кол-во добавлений в избранное'


admin.site.register(Recipes, RecipesAdmin)
admin.site.register(Favorite, PermissionsAdmin)
admin.site.register(ListToBuy, PermissionsAdmin)
admin.site.register(Subscript, PermissionsAdmin)
