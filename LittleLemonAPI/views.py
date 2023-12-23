from django.db.models import Sum
from django.contrib.auth.models import Group, User
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.decorators import action
from .permissions import IsInManagerGroup, NotInGroups, IsManagerOrReadOnly
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer, OrderStatusSerializer, UserSerializer

class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    ordering_fields = ['price','title']
    search_fields = ['title','category__title']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsInManagerGroup()]
        return [IsAuthenticated()]
    
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    http_method_names = ['get', 'post', 'delete']

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'DELETE']:
            return [IsAuthenticated(), NotInGroups()]
        
    def get_queryset(self):
        user = self.request.user
        return Cart.objects.filter(user=user)
    
    @action(detail=False, methods=['delete'])
    def delete(self, request, *args, **kwargs):
        user = self.request.user
        Cart.objects.filter(user=user).delete() # delete all the user's cart items
        return Response(status=204) # return a 204 response
    
class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    ordering_fields = ['date','total']

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)
    
    
    def create(self, request, *args, **kwargs):
        user = self.request.user
        order = Order.objects.create(user=user)
        cart_items = Cart.objects.filter(user=user)
        for cart_item in cart_items:
            menuitem = cart_item.menuitem
            quantity = cart_item.quantity
            unit_price = menuitem.price
            price = unit_price * quantity
            order_item = OrderItem.objects.create(order=order, menuitem=menuitem, quantity=quantity, unit_price=unit_price, price=price)
        Cart.objects.filter(user=user).delete()
        total = OrderItem.objects.filter(order=order).aggregate(total=Sum('price'))['total']
        order.total = total
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=201)
    
    @action(detail=True, methods=['put', 'patch'], permission_classes=[IsAuthenticated, IsInManagerGroup])
    def update_order(self, request, pk=None):
        order = self.get_object()
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)
        
    def partial_update(self, request, pk=None):
        order = self.get_object()
        user = self.request.user
        if user.groups.filter(name='Delivery crew').exists():
            serializer = OrderStatusSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=400)
        else:
            return super().partial_update(request, pk)
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsManagerOrReadOnly()]
        elif self.request.method == 'DELETE':
            return [IsAuthenticated(), IsInManagerGroup()]
        else:
            return [IsAuthenticated()]
        
# class GroupsViewSet(viewsets.GenericViewSet):
#     queryset = Group.objects.all()
#     permission_classes = [IsAuthenticated, IsInManagerGroup]

#     @action(detail=True, methods=['get'], url_path='manager/users')
#     def get_managers(self, request, pk=None):
#         group = self.get_object()
#         users = group.user_set.all()
#         serializer = UserSerializer(users, many=True)
#         return Response(serializer.data)

#     @action(detail=True, methods=['get'], url_path='delivery-crew/users')
#     def get_delivery_crew(self, request, pk=None):
#         group = self.get_object()
#         users = group.user_set.all()
#         serializer = UserSerializer(users, many=True)
#         return Response(serializer.data)

#     @action(detail=True, methods=['post'], url_path='manager/users')
#     def assign_manager(self, request, pk=None):
#         group = self.get_object()
#         user_id = request.data.get('user_id')
#         if user_id:
#             try:
#                 user = User.objects.get(id=user_id)
#                 group.user_set.add(user)
#                 return Response({'message': 'User assigned to manager group'})
#             except User.DoesNotExist:
#                 return Response({'error': 'User not found'}, status=404)
#         else:
#             return Response({'error': 'User id required'}, status=400)

#     @action(detail=True, methods=['post'], url_path='delivery-crew/users')
#     def assign_delivery_crew(self, request, pk=None):
#         group = self.get_object()
#         user_id = request.data.get('user_id')
#         if user_id:
#             try:
#                 user = User.objects.get(id=user_id)
#                 group.user_set.add(user)
#                 return Response({'message': 'User assigned to delivery crew group'})
#             except User.DoesNotExist:
#                 return Response({'error': 'User not found'}, status=404)
#         else:
#             return Response({'error': 'User id required'}, status=400)

#     @action(detail=True, methods=['delete'], url_path='manager/users/(?P<user_id>\d+)')
#     def remove_manager(self, request, pk=None, user_id=None):
#         group = self.get_object()
#         if user_id:
#             try:
#                 user = User.objects.get(id=user_id)
#                 group.user_set.remove(user)
#                 return Response({'message': 'User removed from manager group'})
#             except User.DoesNotExist:
#                 return Response({'error': 'User not found'}, status=404)
#         else:
#             return Response({'error': 'User id required'}, status=400)

#     @action(detail=True, methods=['delete'], url_path='delivery-crew/users/(?P<user_id>\d+)')
#     def remove_delivery_crew(self, request, pk=None, user_id=None):
#         group = self.get_object()
#         if user_id:
#             try:
#                 user = User.objects.get(id=user_id)
#                 group.user_set.remove(user)
#                 return Response({'message': 'User removed from delivery crew group'})
#             except User.DoesNotExist:
#                 return Response({'error': 'User not found'}, status=404)
#         else:
#             return Response({'error': 'User id required'}, status=400)

# class GroupsViewSet(viewsets.GenericViewSet):
#     queryset = Group.objects.all()
#     permission_classes = [IsAuthenticated, IsInManagerGroup]

#     @action(detail=True, methods=['get', 'post'], url_path='manager/users')
#     def manage_managers(self, request, pk=None):
#         group = self.get_object()
#         if request.method == 'GET':
#             users = group.user_set.all()
#             serializer = UserSerializer(users, many=True)
#             return Response(serializer.data)
#         elif request.method == 'POST':
#             user_id = request.data.get('user_id')
#             if user_id:
#                 try:
#                     user = User.objects.get(id=user_id)
#                     group.user_set.add(user)
#                     return Response({'message': 'User assigned to manager group'})
#                 except User.DoesNotExist:
#                     return Response({'error': 'User not found'}, status=404)
#             else:
#                 return Response({'error': 'User id required'}, status=400)

#     @action(detail=True, methods=['get', 'post'], url_path='delivery-crew/users')
#     def manage_delivery_crew(self, request, pk=None):
#         group = self.get_object()
#         if request.method == 'GET':
#             users = group.user_set.all()
#             serializer = UserSerializer(users, many=True)
#             return Response(serializer.data)
#         elif request.method == 'POST':
#             user_id = request.data.get('user_id')
#             if user_id:
#                 try:
#                     user = User.objects.get(id=user_id)
#                     group.user_set.add(user)
#                     return Response({'message': 'User assigned to delivery crew group'})
#                 except User.DoesNotExist:
#                     return Response({'error': 'User not found'}, status=404)
#             else:
#                 return Response({'error': 'User id required'}, status=400)

class GroupsViewSet(viewsets.GenericViewSet):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated, IsInManagerGroup]

    @action(detail=False, methods=['get', 'post'], url_path='manager/users')
    def manage_managers(self, request):
        if request.method == 'GET':
            users = User.objects.filter(groups__name='Manager')
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            user_id = request.data.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    group = Group.objects.get(name='Manager')
                    group.user_set.add(user)
                    return Response({'message': 'User assigned to manager group'})
                except (User.DoesNotExist, Group.DoesNotExist):
                    return Response({'error': 'User or group not found'}, status=404)
            else:
                return Response({'error': 'User id required'}, status=400)

    @action(detail=True, methods=['delete'], url_path='manager/users/(?P<user_id>\d+)')
    def remove_manager(self, request, pk=1, user_id=None):
        group = self.get_object()
        try:
            user = User.objects.get(id=user_id)
            group.user_set.remove(user)
            return Response({'message': 'User removed from manager group'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

    @action(detail=False, methods=['get', 'post'], url_path='delivery-crew/users')
    def manage_delivery_crew(self, request):
        if request.method == 'GET':
            users = User.objects.filter(groups__name='Delivery crew')
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            user_id = request.data.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    group = Group.objects.get(name='Delivery crew')
                    group.user_set.add(user)
                    return Response({'message': 'User assigned to delivery crew group'})
                except (User.DoesNotExist, Group.DoesNotExist):
                    return Response({'error': 'User or group not found'}, status=404)
            else:
                return Response({'error': 'User id required'}, status=400)
            
    @action(detail=True, methods=['delete'], url_path='delivery-crew/users/(?P<user_id>\d+)')
    def remove_delivery_crew(self, request, pk=2, user_id=None):
        group = self.get_object()
        try:
            user = User.objects.get(id=user_id)
            group.user_set.remove(user)
            return Response({'message': 'User removed from delivery crew group'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)