from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, IncomeViewSet, ExpenseViewSet,
    BudgetViewSet, SavingsGoalViewSet, SubscriptionViewSet, NotificationViewSet
)

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('income', IncomeViewSet, basename='income')
router.register('expenses', ExpenseViewSet, basename='expense')
router.register('budgets', BudgetViewSet, basename='budget')
router.register('savings-goals', SavingsGoalViewSet, basename='savings-goal')
router.register('subscriptions', SubscriptionViewSet, basename='subscription')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
