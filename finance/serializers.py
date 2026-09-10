from rest_framework import serializers
from .models import Category, Income, Expense, Budget, SavingsGoal, Subscription, Notification

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'is_default', 'user')
        read_only_fields = ('id', 'is_default', 'user')


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ('id', 'user', 'source', 'amount', 'date', 'description', 'proof')
        read_only_fields = ('id', 'user')


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Expense
        fields = ('id', 'user', 'name', 'amount', 'category', 'category_name', 'payment_method', 'date', 'notes', 'proof')
        read_only_fields = ('id', 'user')


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Budget
        fields = ('id', 'user', 'category', 'category_name', 'budget_amount', 'period', 'month', 'year', 'budget_type')
        read_only_fields = ('id', 'user')


class SavingsGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = ('id', 'user', 'name', 'target_amount', 'current_amount', 'deadline', 'progress_percentage')
        read_only_fields = ('id', 'user')

    def get_progress_percentage(self, obj):
        if obj.target_amount <= 0:
            return 0.0
        pct = (obj.current_amount / obj.target_amount) * 100
        return min(round(float(pct), 2), 100.0)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'user', 'name', 'amount', 'renewal_date', 'frequency')
        read_only_fields = ('id', 'user')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'user', 'message', 'is_read', 'created_at', 'type')
        read_only_fields = ('id', 'user', 'created_at')
