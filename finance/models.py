from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories"
    )

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ("name", "user", "is_default")

    def __str__(self):
        return f"{self.name} (Default)" if self.is_default else f"{self.name} ({self.user.username})"


class Income(models.Model):
    SALARY = 'Salary'
    FREELANCING = 'Freelancing'
    BUSINESS = 'Business'
    INVESTMENT = 'Investment'
    RENTAL = 'Rental Income'
    BONUS = 'Bonus'
    OTHER = 'Other'

    SOURCE_CHOICES = [
        (SALARY, 'Salary'),
        (FREELANCING, 'Freelancing'),
        (BUSINESS, 'Business'),
        (INVESTMENT, 'Investment'),
        (RENTAL, 'Rental Income'),
        (BONUS, 'Bonus'),
        (OTHER, 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incomes")
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default=OTHER)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    proof = models.FileField(upload_to="income_proofs/", null=True, blank=True)

    def __str__(self):
        return f"Income: {self.source} - {self.amount} by {self.user.username} on {self.date}"


class Expense(models.Model):
    CASH = 'Cash'
    CARD = 'Card'
    UPI = 'UPI'
    NET_BANKING = 'Net Banking'

    PAYMENT_CHOICES = [
        (CASH, 'Cash'),
        (CARD, 'Card'),
        (UPI, 'UPI'),
        (NET_BANKING, 'Net Banking'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expenses")
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="expenses")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default=CASH)
    date = models.DateField()
    notes = models.TextField(blank=True)
    proof = models.FileField(upload_to="expense_proofs/", null=True, blank=True)

    def __str__(self):
        return f"Expense: {self.name} ({self.category.name}) - {self.amount} on {self.date}"


class Budget(models.Model):
    FIXED = 'Fixed'
    CATEGORY = 'Category'

    TYPE_CHOICES = [
        (FIXED, 'Fixed Budget'),
        (CATEGORY, 'Category Budget'),
    ]

    DAILY = 'Daily'
    MONTHLY = 'Monthly'
    YEARLY = 'Yearly'

    PERIOD_CHOICES = [
        (DAILY, 'Daily'),
        (MONTHLY, 'Monthly'),
        (YEARLY, 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="budgets"
    )
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default=MONTHLY)
    # Month and Year can now be optional if the user wants a generic recurring budget
    month = models.PositiveIntegerField(null=True, blank=True) 
    year = models.PositiveIntegerField(null=True, blank=True)
    budget_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=CATEGORY)

    class Meta:
        # We remove unique_together because with nulls it gets complicated, and users might want generic + specific
        pass

    def __str__(self):
        cat_str = self.category.name if self.category else "Fixed Limit"
        return f"Budget ({self.period}) for {cat_str}: {self.budget_amount}"


class SavingsGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_goals")
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    deadline = models.DateField()

    def __str__(self):
        return f"Savings Goal: {self.name} - {self.current_amount}/{self.target_amount} by {self.deadline}"


class Subscription(models.Model):
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'
    YEARLY = 'Yearly'

    FREQUENCY_CHOICES = [
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (YEARLY, 'Yearly'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    renewal_date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default=MONTHLY)

    def __str__(self):
        return f"Subscription: {self.name} - {self.amount} ({self.frequency})"


class Notification(models.Model):
    BUDGET_ALERT = 'budget_alert'
    GOAL_COMPLETED = 'goal_completed'
    SUBSCRIPTION_DUE = 'subscription_due'
    REPORT_READY = 'report_ready'

    TYPE_CHOICES = [
        (BUDGET_ALERT, 'Budget Limit Reached'),
        (GOAL_COMPLETED, 'Goal Completed'),
        (SUBSCRIPTION_DUE, 'Subscription Due'),
        (REPORT_READY, 'Report Ready'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=BUDGET_ALERT)

    def __str__(self):
        return f"Notification ({self.type}) for {self.user.username}: {self.message[:30]}"
