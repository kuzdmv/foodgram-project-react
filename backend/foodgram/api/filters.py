import django_filters

from recipes.models import Recipes, Tag

STATUS_CHOICES = (
    (1, '1'),
    (0, '0'),
)


class RecipesFilter(django_filters.FilterSet):
    is_favorited = django_filters.ChoiceFilter(
        method='filter_is_favorited',
        choices=STATUS_CHOICES
    )
    is_in_shopping_cart = django_filters.ChoiceFilter(
        method='filter_is_in_shopping_cart',
        choices=STATUS_CHOICES
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    def filter_is_favorited(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        fav_list = self.request.user.favorite.all()
        recipe_list = [i.recipe.pk for i in fav_list]
        if value == '1':
            return queryset.filter(id__in=recipe_list)
        return queryset.exclude(id__in=recipe_list)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        listtobuy_list = self.request.user.listtobuy.all()
        recipe_list = [i.recipe.pk for i in listtobuy_list]
        if value == '1':
            return queryset.filter(id__in=recipe_list)
        return queryset.exclude(id__in=recipe_list)

    class Meta:
        model = Recipes
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')
