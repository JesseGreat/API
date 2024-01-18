from rest_framework import permissions, generics
from django.contrib.auth.models import  Group
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
import datetime
from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import (MenuItemSerializer, CategorySerializer, CustomUserCreateSerializer, 
                          CartSerializer, OrderSerializer, OrderItemSerializer)
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class ManagerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        elif request.user.groups.filter(name="Manager").exists():
            return True
        else:
            raise PermissionDenied("403 - Unauthorized")


# MENU ITEMS ENDPOINTS
class MenuitemView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, ManagerPermission]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_field = ['title', 'price', 'featured']
    
class SingleMenuitemView(generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, ManagerPermission]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer 
    
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    
    
# USER GROUPS MANAGEMENT ENDPOINTS
class ManagersGroupView(generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.filter(name='Manager')
    serializer_class = CustomUserCreateSerializer
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        users = self.get_object().user_set.all()
        serializer = CustomUserCreateSerializer(users, many=True)
        return Response(serializer.data)


class DeliveryCrewView(generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.filter(name='Delivery crew')
    serializer_class = CustomUserCreateSerializer
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        users = self.get_object().user_set.all()
        serializer = CustomUserCreateSerializer(users, many=True)
        return Response(serializer.data)


# CART MANAGEMENT ENDPOINTS
class CartMenuItemsView(generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Cart.objects.all()  # Assuming you want to list all cart items for all users
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter the queryset to show only the items for the authenticated user
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Set the authenticated user as the user id for the cart item
        serializer.save(user=self.request.user)


class OrderView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    ordering_field = ['status', 'date']
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # retreive relevant cart item for the users
        cart_items = Cart.objects.filter(user=user)
        
        # calculate total for the order
        total = sum(cart_item.price for cart_item in cart_items)
        
        with transaction.atomic(): # helps to ensure integrity of data
            
            # create a new order instance
            order = Order.objects.create(
                user=user,
                total=total,
                status=False,
                date=datetime.date.today()
            )
            
            # create order items based on cart items
            order_items = []
            for cart_item in cart_items:
                order_item = OrderItem(
                    order = order,
                    menuitem=cart_item.menuitem,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    price=cart_item.price
                )
                order_items.append(order_item)
                
            # bulk create order items
            OrderItem.objects.bulk_create(order_items)
            
            # delete cart items
            cart_items.delete()
            
        return Response("Order create and cart items deleted")
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # retrieve all order items for the manager
        if user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
            
        # retrieve all order items for the delivery crew
        elif user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew=user)
            
        #retrieve all orders
        else:
            orders = Order.objects.filter(user=user)
        
        serializer_data = []
        
        # get order items
        for order in orders:
            order_data = self.get_serializer(order).data
            order_items = OrderItem.objects.filter(order=order)
            order_item_data = OrderItemSerializer(order_items, many=True).data
            order_data['order_items'] = order_item_data
            serializer_data.append(order_data)
            
        
        return Response(serializer_data)
    

class OrderItemView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'id'
    
    def get(self, request, *args, **kwargs):
        user = request.user
        orderId = kwargs['id']
        order = get_object_or_404(Order, id=orderId)
        if order.user != user:
            raise PermissionDenied("Incorrect user for order ID")
        
        orders = Order.objects.filter(id=orderId)
        serializer_data = []
        
        # get order items
        for order in orders:
            order_data = self.get_serializer(order).data
            order_items = OrderItem.objects.filter(order=order)
            order_item_data = OrderItemSerializer(order_items, many=True).data
            order_data['order_items'] = order_item_data
            serializer_data.append(order_data)
            
        
        return Response(serializer_data)
    
    
    def put(self, request, *args, **kwargs):
        user = request.user
        
        if user.groups.filter(name='Manager').exists():
            return super().put(request, *args, **kwargs)
        raise PermissionDenied("You are not authourized to perform this action")
    
    
    def patch(self, request, *args, **kwargs):
        user = request.user
        
        manager = user.groups.filter(name='Manager').exists()
        delivery_crew = user.groups.filter(name='Delivery crew').exists()
        
        if manager or delivery_crew:
            return super().partial_update(request, *args, **kwargs)
        raise PermissionDenied("You are not authourized to perform this action")
    
    
    def destroy(self, request, *args, **kwargs):
        user = request.user
        
        if user.groups.filter(name='Manager').exists():
            return super().destroy(request, *args, **kwargs)
        raise PermissionDenied("You are not authourized to perform this action")