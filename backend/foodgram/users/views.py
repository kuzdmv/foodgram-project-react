from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from recipes.models import User, Subscript
from api.serializers import (
    CustomUserSerializer,
    SetPasswordSerializer,
    SubscriptSerializer,
    SubscriptCreateSerializer,
)
from api.mixins import ListRetrieveCreateViewSet
from api.pagination import CustomPagination


class CustomUserViewSet(ListRetrieveCreateViewSet):
    queryset = User.objects.all().order_by('pk')
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = CustomUserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=["post"],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(
            context={'request': request}, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = User.objects.filter(
            id__in=request.user.follower.values_list('author', flat=True)
        ).order_by('pk')
        recipes_limit = self.request.query_params.get('recipes_limit')
        page = self.paginate_queryset(queryset)
        serializer = SubscriptSerializer(
            page,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk):
        data = {}
        data['author'] = get_object_or_404(User, pk=pk).pk
        data['user'] = self.request.user.pk
        serializer = SubscriptCreateSerializer(
            context={'request': request}, data=data
        )
        serializer.is_valid(raise_exception=True)
        if request.method == "POST":
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        Subscript.objects.filter(**data).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
