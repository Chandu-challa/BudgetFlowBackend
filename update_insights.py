import re

content = open('D:/BudgetFlowBackend/reports/views.py', encoding='utf-8').read()

old_code = """    def get(self, request):
        user = request.user
        now = timezone.now()
        current_month = now.month
        current_year = now.year"""

new_code = """    def get(self, request):
        user = request.user
        
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year')
        start_date_param = request.query_params.get('start_date')
        end_date_param = request.query_params.get('end_date')

        now = timezone.now()
        current_month = int(month_param) if month_param else now.month
        current_year = int(year_param) if year_param else now.year
        
        if start_date_param and end_date_param:
            try:
                start_date_filter = datetime.strptime(start_date_param, '%Y-%m-%d').date()
                end_date_filter = datetime.strptime(end_date_param, '%Y-%m-%d').date()
            except ValueError:
                start_date_filter = now.replace(day=1).date()
                end_date_filter = now.date()
        else:
            import calendar
            start_date_filter = datetime(current_year, current_month, 1).date()
            last_day = calendar.monthrange(current_year, current_month)[1]
            end_date_filter = datetime(current_year, current_month, last_day).date()"""

content = content.replace(old_code, new_code)

content = content.replace(
"""        this_month_spent = Expense.objects.filter(
            user=user, date__month=current_month, date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""",
"""        this_month_spent = Expense.objects.filter(
            user=user, date__gte=start_date_filter, date__lte=end_date_filter
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""")

content = content.replace(
"""            cat_spent = Expense.objects.filter(
                user=user, category=cat, date__month=current_month, date__year=current_year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""",
"""            cat_spent = Expense.objects.filter(
                user=user, category=cat, date__gte=start_date_filter, date__lte=end_date_filter
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""")

content = content.replace(
"""        this_month_income = Income.objects.filter(
            user=user, date__month=current_month, date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""",
"""        this_month_income = Income.objects.filter(
            user=user, date__gte=start_date_filter, date__lte=end_date_filter
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""")

content = content.replace(
"""        budgets = Budget.objects.filter(user=user, month=current_month, year=current_year, budget_type=Budget.CATEGORY)""",
"""        budgets = Budget.objects.filter(user=user, month=current_month, year=current_year, budget_type=Budget.CATEGORY) # budgets are monthly so this stays""")

content = content.replace(
"""            actual = Expense.objects.filter(
                user=user, category=b.category, date__month=current_month, date__year=current_year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""",
"""            actual = Expense.objects.filter(
                user=user, category=b.category, date__gte=start_date_filter, date__lte=end_date_filter
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')""")

open('D:/BudgetFlowBackend/reports/views.py', 'w', encoding='utf-8').write(content)
print("Updated SmartInsightsView")
