from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipesSerializer,
    FavoriteRecipesCreateSerializer,
    ListToBuyRecipesCreateSerializer,
    RecipesCreateSerializer
)
from .permissions import (
    AuthorOrReadOnly
)
from recipes.models import (
    Tag, Ingredient, Recipes,
    Favorite, ListToBuy, IngredientRecipe
)
from . mixins import ListRetrieveViewSet
from .pagination import CustomPagination
from .filters import RecipesFilter


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all().order_by('slug')
    serializer_class = TagSerializer


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all().order_by('pk')
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all().order_by('-pub_date')
    serializer_class = RecipesSerializer
    pagination_class = CustomPagination
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipesSerializer
        return RecipesCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def favorite_listtobuy_create(
        self, request, pk, model, getserializer
    ):
        data = {}
        data['recipe'] = get_object_or_404(Recipes, pk=pk).pk
        data['user'] = self.request.user.pk
        serializer = getserializer(
            context={'request': request}, data=data
        )
        serializer.is_valid(raise_exception=True)
        if request.method == "POST":
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        model.objects.filter(**data).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        return self.favorite_listtobuy_create(
            request, pk, Favorite, FavoriteRecipesCreateSerializer
        )

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk):
        return self.favorite_listtobuy_create(
            request, pk, ListToBuy, ListToBuyRecipesCreateSerializer
        )

    @action(detail=False)
    def download_shopping_cart(self, request):
        ingredient_list = Ingredient.objects.filter(
            id__in=IngredientRecipe.objects.filter(
                recipe_id__in=self.request.user.listtobuy.values_list(
                    'recipe', flat=True
                )
            ).values_list('ingredient_id', flat=True)
        ).annotate(amount=Sum('ingredientrecipe__amount')).order_by('pk')
        to_buy = [
            f'{ing.name} ({ing.measurement_unit}) - {ing.amount} \n'
            for ing in ingredient_list
        ]
        response = HttpResponse(content_type='text/plain')
        response["Content-Disposition"] = "attachment; filename=shop-list.txt"
        response.writelines(to_buy)
        return response
