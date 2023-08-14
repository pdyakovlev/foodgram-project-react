from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count
from django.db.models.expressions import Value
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from djoser.views import UserViewSet
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated)
from rest_framework.response import Response
from .utils import get_pdf_shopping_cart
from .mixins import GetObjectMixin, PermissionAndPaginationMixin
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrAuthorOrReadOnly
from recipes.models import (Ingredient, Recipe, Subscribe, Tag, ShoppingCart)
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer,
                          SubscribeSerializer, TagSerializer)
from users.serializers import (TokenSerializer, ListUserSerializer,
                               CreateUserSerializer, PasswordUserSerializer)
from rest_framework.pagination import PageNumberPagination

User = get_user_model()


class AddAndDeleteSubscribe(
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True),)

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST)
        if request.user.follower.filter(author=instance).exists():
            return Response(
                {'errors': 'Вы уже подписаны.'},
                status=status.HTTP_400_BAD_REQUEST)
        subs = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.follower.filter(author=instance).delete()


class AddDeleteFavoriteRecipe(
        GetObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.favorite_recipe.recipe.remove(instance)


class AddDeleteShoppingCart(
        GetObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            request.user.shopping_cart.recipe.add(instance)
        except ShoppingCart.DoesNotExist:
            ShoppingCart.objects.create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.shopping_cart.recipe.remove(instance)


class AuthToken(ObtainAuthToken):
    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {'auth_token': token.key},
            status=status.HTTP_201_CREATED)


class UsersViewSet(UserViewSet):
    serializer_class = ListUserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method.lower() == 'post':
            return CreateUserSerializer
        return ListUserSerializer

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        return Recipe.objects.annotate(
        ).select_related('author').prefetch_related(
            'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe', 'tags'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        page = get_pdf_shopping_cart(self, request)
        return FileResponse(page,
                            as_attachment=True,
                            filename='shoppinglist.pdf')


class IngredientsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class TagsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


@api_view(['post'])
def set_password(request):
    serializer = PasswordUserSerializer(
        data=request.data,
        context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Пароль был изменен.'},
            status=status.HTTP_201_CREATED)
    return Response(
        {'error': 'Введены неверные данные.'},
        status=status.HTTP_400_BAD_REQUEST)
