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
from recipes.models import Tag, Ingredient, Recipes, Favorite, ListToBuy
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

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        data = {}
        data['recipe'] = get_object_or_404(Recipes, pk=pk)
        data['user'] = self.request.user
        serializer = FavoriteRecipesCreateSerializer(data=data)
        if serializer.is_valid():
            if request.method == "POST":
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            if not Favorite.objects.filter(**data).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.filter(**data).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk):
        data = {}
        data['recipe'] = get_object_or_404(Recipes, pk=pk)
        data['user'] = self.request.user
        serializer = ListToBuyRecipesCreateSerializer(data=data)
        if serializer.is_valid():
            if request.method == "POST":
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            if not ListToBuy.objects.filter(**data).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            ListToBuy.objects.filter(**data).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False)
    def download_shopping_cart(self, request):
        recipes_caraft = self.request.user.listtobuy.all()
        recipe_list = [i.recipe for i in recipes_caraft]
        ingredient_list = [i.ingredientrecipe.all() for i in recipe_list]
        craft = {}
        for i in ingredient_list:
            for b in i:
                if b.ingredient in craft:
                    craft[b.ingredient] += b.amount
                else:
                    craft[b.ingredient] = b.amount
        to_buy = [
            f'{i.name} ({i.measurement_unit}) - {craft[i]} \n' for i in craft
        ]
        response = HttpResponse(content_type='text/plain')
        response["Content-Disposition"] = "attachment; filename=shop-list.txt"
        response.writelines(to_buy)
        return response
