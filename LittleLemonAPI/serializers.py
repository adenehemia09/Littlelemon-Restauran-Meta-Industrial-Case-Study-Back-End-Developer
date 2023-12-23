from django.contrib.auth.models import User
from rest_framework import serializers
from .models import MenuItem, Cart, Order, OrderItem


class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'category', 'featured', 'category_id']

class CartSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    unit_price = serializers.SerializerMethodField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']

    def get_unit_price(self, cart):
        return cart.menuitem.price
    
    def create(self, validated_data):
        unit_price = validated_data['menuitem'].price
        quantity = validated_data['quantity']
        validated_data['price'] = int(unit_price) * int(quantity)
        request = self.context['request']
        validated_data['user'] = request.user
        validated_data['unit_price'] = int(unit_price) # add this line
        return super().create(validated_data)

    def get_context(self):
        context = super().get_context()
        context['request'] = self.request
        return context

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, source='orderitem_set')
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items']

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
        read_only_fields = []

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'groups']
        read_only_fields = ['id', 'groups']