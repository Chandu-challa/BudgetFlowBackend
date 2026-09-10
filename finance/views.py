from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime

from .models import Category, Income, Expense, Budget, SavingsGoal, Subscription, Notification
from .serializers import (
    CategorySerializer, IncomeSerializer, ExpenseSerializer,
    BudgetSerializer, SavingsGoalSerializer, SubscriptionSerializer, NotificationSerializer
)

def check_budget_limit(user, category, amount, date):
    # Check category budget
    month = date.month
    year = date.year
    
    # Get category budget
    cat_budget = Budget.objects.filter(user=user, category=category, month=month, year=year, budget_type=Budget.CATEGORY).first()
    if cat_budget:
        total_spent = Expense.objects.filter(
            user=user, category=category, date__month=month, date__year=year
        ).aggregate(total=Sum('amount'))['total'] or 0
        # If this is called in perform_create, the new expense is not in database yet, so we add it.
        # If in perform_update, we should be careful, but we just check the current sum.
        # To be safe, we calculate sum and notify if it crosses limit.
        if total_spent > cat_budget.budget_amount:
            Notification.objects.create(
                user=user,
                type=Notification.BUDGET_ALERT,
                message=f"Budget Alert: Spending of {total_spent} in '{category.name}' has exceeded your category budget of {cat_budget.budget_amount} for {month}/{year}."
            )
            
    # Check fixed overall budget
    fixed_budget = Budget.objects.filter(user=user, month=month, year=year, budget_type=Budget.FIXED).first()
    if fixed_budget:
        total_spent_all = Expense.objects.filter(
            user=user, date__month=month, date__year=year
        ).aggregate(total=Sum('amount'))['total'] or 0
        if total_spent_all > fixed_budget.budget_amount:
            Notification.objects.create(
                user=user,
                type=Notification.BUDGET_ALERT,
                message=f"Budget Alert: Total monthly spending of {total_spent_all} has exceeded your fixed monthly budget of {fixed_budget.budget_amount} for {month}/{year}."
            )


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # Admins see all categories. Normal users see default categories + their own.
        if user.role == 'ADMIN':
            return Category.objects.all().order_by('name')
        return Category.objects.filter(Q(is_default=True) | Q(user=user)).order_by('name')

    def perform_create(self, serializer):
        # Admin can create default categories, normal users create personal ones.
        is_default = self.request.user.role == 'ADMIN'
        serializer.save(user=self.request.user, is_default=is_default)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default and request.user.role != 'ADMIN':
            return Response(
                {"error": "You cannot delete a default category."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class IncomeViewSet(viewsets.ModelViewSet):
    serializer_class = IncomeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # Admins see all income, normal users see only their own.
        queryset = Income.objects.all() if user.role == 'ADMIN' else Income.objects.filter(user=user)

        # Filters
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(description__icontains=search)

        ordering = self.request.query_params.get('ordering', '-date')
        return queryset.order_by(ordering)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        queryset = Income.objects.filter(id__in=ids)
        if user.role != 'ADMIN':
            queryset = queryset.filter(user=user)
        
        count = queryset.count()
        queryset.delete()
        return Response({"message": f"Successfully deleted {count} records."}, status=status.HTTP_200_OK)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Expense.objects.all() if user.role == 'ADMIN' else Expense.objects.filter(user=user)

        # Filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(notes__icontains=search))

        ordering = self.request.query_params.get('ordering', '-date')
        return queryset.order_by(ordering)

    def perform_create(self, serializer):
        expense = serializer.save(user=self.request.user)
        # Check budget alert
        check_budget_limit(expense.user, expense.category, expense.amount, expense.date)

    def perform_update(self, serializer):
        expense = serializer.save()
        check_budget_limit(expense.user, expense.category, 0, expense.date)

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        queryset = Expense.objects.filter(id__in=ids)
        if user.role != 'ADMIN':
            queryset = queryset.filter(user=user)
        
        count = queryset.count()
        queryset.delete()
        return Response({"message": f"Successfully deleted {count} records."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        # We use the same filter logic as get_queryset to ensure stats match the active view
        queryset = Expense.objects.filter(user=request.user)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(notes__icontains=search))

        total_spent = queryset.aggregate(total=Sum('amount'))['total'] or 0

        # Highest category
        top_category = queryset.values('category__name').annotate(total=Sum('amount')).order_by('-total').first()
        top_category_name = top_category['category__name'] if top_category else "N/A"

        # Avg daily spend
        # Find unique days
        unique_days = queryset.values('date').distinct().count()
        avg_daily = float(total_spent) / unique_days if unique_days > 0 else 0

        return Response({
            "total_spent": total_spent,
            "top_category": top_category_name,
            "avg_daily_spend": avg_daily
        }, status=status.HTTP_200_OK)


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Budget.objects.all() if user.role == 'ADMIN' else Budget.objects.filter(user=user)
        
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month:
            queryset = queryset.filter(month=month)
        if year:
            queryset = queryset.filter(year=year)
            
        return queryset.order_by('-year', '-month')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='compare')
    def compare_budgets(self, request):
        user = request.user
        # Allow passing a target date, default to today
        target_date_str = request.query_params.get('target_date')
        if target_date_str:
            try:
                from datetime import datetime
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()

        month = target_date.month
        year = target_date.year

        # Get all budgets for the user. We will filter out specific ones that don't match the target date.
        budgets = Budget.objects.filter(user=user)
        
        comparison = []
        for b in budgets:
            # If the budget is strictly tied to a month/year, skip if it doesn't match
            if b.month and b.month != month:
                continue
            if b.year and b.year != year:
                continue

            # Calculate actual spent based on period
            expense_query = Expense.objects.filter(user=user)
            if b.budget_type == Budget.CATEGORY and b.category:
                expense_query = expense_query.filter(category=b.category)

            if b.period == Budget.DAILY:
                actual = expense_query.filter(date=target_date).aggregate(total=Sum('amount'))['total'] or 0
            elif b.period == Budget.YEARLY:
                actual = expense_query.filter(date__year=year).aggregate(total=Sum('amount'))['total'] or 0
            else: # MONTHLY default
                actual = expense_query.filter(date__month=month, date__year=year).aggregate(total=Sum('amount'))['total'] or 0

            cat_name = b.category.name if b.category else f"Fixed {b.period} Limit"

            comparison.append({
                "id": b.id,
                "category": cat_name,
                "budget_type": b.budget_type,
                "period": b.period,
                "budget_amount": b.budget_amount,
                "actual_amount": actual,
                "remaining": b.budget_amount - actual,
                "utilization_pct": round(float((actual / b.budget_amount) * 100), 2) if b.budget_amount > 0 else 0
            })

        return Response(comparison, status=status.HTTP_200_OK)


class SavingsGoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = SavingsGoal.objects.all() if user.role == 'ADMIN' else SavingsGoal.objects.filter(user=user)
        return queryset.order_by('deadline')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='contribute')
    def contribute(self, request, pk=None):
        goal = self.get_object()
        amount = request.data.get('amount')
        
        if not amount:
            return Response({"error": "Contribution amount is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = float(amount)
        except ValueError:
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        goal.current_amount += timezone.decimal.Decimal(amount)
        goal.save()

        # Check if completed
        if goal.current_amount >= goal.target_amount:
            Notification.objects.create(
                user=goal.user,
                type=Notification.GOAL_COMPLETED,
                message=f"Congratulations! You've achieved your savings goal '{goal.name}' of {goal.target_amount}!"
            )

        return Response(SavingsGoalSerializer(goal).data, status=status.HTTP_200_OK)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Subscription.objects.all() if user.role == 'ADMIN' else Subscription.objects.filter(user=user)
        return queryset.order_by('renewal_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "notification marked as read"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "all notifications marked as read"}, status=status.HTTP_200_OK)
