from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=False)

router.register('menu-items', views.MenuItemsViewSet, basename='menu')
router.register('cart/menu-items', views.CartViewSet, basename='cart')
router.register('orders', views.OrdersViewSet, basename='order')
router.register('groups', views.GroupsViewSet, basename='groups')

urlpatterns = router.urls