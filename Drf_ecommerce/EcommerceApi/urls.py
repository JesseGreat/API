from django.urls import path
from .views import (MenuitemView, SingleMenuitemView, CategoryView, ManagersGroupView, 
                    DeliveryCrewView, CartMenuItemsView, OrderView, OrderItemView)

urlpatterns = [
    path('menu-items', MenuitemView.as_view(), name='menu-item-list'),
    path('menu-items/{menuItem}', SingleMenuitemView.as_view, name='single-menu-view' ),
    path('category', CategoryView.as_view(), name='category-list'),
    path('groups/manager/users', ManagersGroupView.as_view(), name='creating-manager'),
    path('groups/manager/users/<userId>', ManagersGroupView.as_view(), name='deleting-manager'),
    path('groups/delivery-crew/users', DeliveryCrewView.as_view(), name='creating-delivery-crew'),
    path('groups/delivery-crew/users/<userId>', DeliveryCrewView.as_view(), name='creating-delivery-crew'),
    path('cart/menu-items', CartMenuItemsView.as_view()),
    path('cart/menu-items/<int:pk>', CartMenuItemsView.as_view()),
    path('orders', OrderView.as_view()),
    path('api/orders/<id>', OrderItemView.as_view())
]