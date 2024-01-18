# serializers.py

from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from .models import MenuItem, CustomUser, Cart, Category, Order, OrderItem

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = ['username', 'email']
        
class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']
        
    def create(self, validated_data):
        validated_data['price'] = validated_data['unit_price'] * validated_data['quantity']
        return super().create(validated_data)
    
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date']

class OrderItemSerializer(serializers.ModelSerializer):
    # quantity = CustomSmallIntegerField()
    price = serializers.SerializerMethodField(method_name='total_price')
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'quantity', 'unit_price', 'price']
        
    def total_price(self, product:OrderItem):
        return product.unit_price * product.quantity


