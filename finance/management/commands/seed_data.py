from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from finance.models import Category, Income, Expense, Budget, SavingsGoal, Subscription
from datetime import date, timedelta
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds categories, admin user, and sample transaction data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1. Create Default Categories
        default_categories = [
            "Food", "Groceries", "Rent", "Utilities", "Travel", "Fuel", 
            "Shopping", "Healthcare", "Education", "Entertainment", 
            "Insurance", "Investments", "Miscellaneous"
        ]
        
        cats = []
        for cat_name in default_categories:
            cat, created = Category.objects.get_or_create(name=cat_name, is_default=True)
            if created:
                self.stdout.write(f"Created category: {cat_name}")
            cats.append(cat)

        # 2. Create Admin Superuser Challa Chandu
        admin_user, created = User.objects.get_or_create(
            username="Challa Chandu",
            defaults={
                "email": "chandu@budgetflow.com",
                "name": "Challa Chandu",
                "role": User.ADMIN,
                "is_superuser": True,
                "is_staff": True,
                "currency": "INR"
            }
        )
        if created or not admin_user.check_password("Chandu692003"):
            admin_user.set_password("Chandu692003")
            admin_user.save()
            self.stdout.write("Admin user 'Challa Chandu' seeded.")

        # 3. Create a Demo Normal User
        demo_user, created = User.objects.get_or_create(
            username="Demo User",
            defaults={
                "email": "demo@budgetflow.com",
                "name": "Demo User",
                "role": User.USER,
                "currency": "USD",
                "monthly_income": Decimal("5000.00")
            }
        )
        if created or not demo_user.check_password("demo123"):
            demo_user.set_password("demo123")
            demo_user.save()
            self.stdout.write("Demo normal user 'Demo User' seeded (password: demo123).")

        # 4. Create some Mock Data for Demo User (last 90 days of transactions)
        # To avoid duplicate mock entries on multiple seed commands
        if Expense.objects.filter(user=demo_user).count() == 0:
            self.stdout.write("Seeding mock transactions for Demo User...")
            today = date.today()
            
            # Seed monthly income
            for month_offset in range(3):
                m_date = today - timedelta(days=30 * month_offset)
                first_of_month = m_date.replace(day=1)
                
                Income.objects.create(
                    user=demo_user,
                    source=Income.SALARY,
                    amount=Decimal("5000.00"),
                    date=first_of_month,
                    description="Monthly corporate salary"
                )
                
                # Small freelancing income
                Income.objects.create(
                    user=demo_user,
                    source=Income.FREELANCING,
                    amount=Decimal("850.00"),
                    date=first_of_month + timedelta(days=12),
                    description="Web development consulting contract"
                )

            # Seed Budgets for Demo User for current month and last month
            current_month = today.month
            current_year = today.year
            last_month = current_month - 1 if current_month > 1 else 12
            last_year = current_year if current_month > 1 else current_year - 1

            for y, m in [(current_year, current_month), (last_year, last_month)]:
                # Category budget: Food (500)
                food_cat = Category.objects.filter(name="Food", is_default=True).first()
                if food_cat:
                    Budget.objects.get_or_create(
                        user=demo_user, category=food_cat, month=m, year=y,
                        defaults={"budget_amount": Decimal("500.00"), "budget_type": Budget.CATEGORY}
                    )
                # Category budget: Groceries (400)
                groc_cat = Category.objects.filter(name="Groceries", is_default=True).first()
                if groc_cat:
                    Budget.objects.get_or_create(
                        user=demo_user, category=groc_cat, month=m, year=y,
                        defaults={"budget_amount": Decimal("400.00"), "budget_type": Budget.CATEGORY}
                    )
                # Fixed overall budget (3500)
                Budget.objects.get_or_create(
                    user=demo_user, category=None, month=m, year=y, budget_type=Budget.FIXED,
                    defaults={"budget_amount": Decimal("3500.00")}
                )

            # Seed Expenses over past 60 days
            payment_methods = [Expense.CASH, Expense.CARD, Expense.UPI, Expense.NET_BANKING]
            expense_samples = [
                {"name": "Whole Foods Groceries", "cat": "Groceries", "min_amt": 80, "max_amt": 150},
                {"name": "Olive Garden Dinner", "cat": "Food", "min_amt": 40, "max_amt": 90},
                {"name": "Monthly App Rent", "cat": "Rent", "min_amt": 1200, "max_amt": 1200, "once_a_month": True},
                {"name": "Electricity Bill", "cat": "Utilities", "min_amt": 80, "max_amt": 130, "once_a_month": True},
                {"name": "Uber ride to office", "cat": "Travel", "min_amt": 15, "max_amt": 35},
                {"name": "Shell Gas Refill", "cat": "Fuel", "min_amt": 40, "max_amt": 60},
                {"name": "Zara Clothes Shopping", "cat": "Shopping", "min_amt": 60, "max_amt": 180},
                {"name": "CVS Pharmacy Prescription", "cat": "Healthcare", "min_amt": 10, "max_amt": 45},
                {"name": "Netflix Monthly Subscription", "cat": "Entertainment", "min_amt": 15.99, "max_amt": 15.99, "once_a_month": True},
                {"name": "Udemy React Course", "cat": "Education", "min_amt": 12.99, "max_amt": 19.99},
            ]

            # Generate random expenses
            for offset in range(60):
                d = today - timedelta(days=offset)
                
                # Check each expense type
                for ex in expense_samples:
                    if ex.get("once_a_month") and d.day != 5:
                        # only charge on the 5th of the month
                        continue
                    
                    # Random chance to spend on non-monthly items
                    if not ex.get("once_a_month") and random.random() > 0.25:
                        continue
                        
                    cat_obj = Category.objects.filter(name=ex["cat"], is_default=True).first()
                    if not cat_obj:
                        continue
                        
                    amt = Decimal(str(round(random.uniform(float(ex["min_amt"]), float(ex["max_amt"])), 2)))
                    Expense.objects.create(
                        user=demo_user,
                        name=ex["name"],
                        amount=amt,
                        category=cat_obj,
                        payment_method=random.choice(payment_methods),
                        date=d,
                        notes="Simulated transaction for dashboard visualization"
                    )

            # 5. Seed Savings Goals
            SavingsGoal.objects.create(
                user=demo_user,
                name="Emergency Fund",
                target_amount=Decimal("10000.00"),
                current_amount=Decimal("4500.00"),
                deadline=today + timedelta(days=180)
            )
            SavingsGoal.objects.create(
                user=demo_user,
                name="MacBook Pro Purchase",
                target_amount=Decimal("2500.00"),
                current_amount=Decimal("1200.00"),
                deadline=today + timedelta(days=60)
            )

            # 6. Seed Subscriptions
            Subscription.objects.create(
                user=demo_user,
                name="Adobe Creative Cloud",
                amount=Decimal("54.99"),
                renewal_date=today + timedelta(days=12),
                frequency=Subscription.MONTHLY
            )
            Subscription.objects.create(
                user=demo_user,
                name="Gym Membership",
                amount=Decimal("30.00"),
                renewal_date=today + timedelta(days=3),
                frequency=Subscription.MONTHLY
            )
            Subscription.objects.create(
                user=demo_user,
                name="Github Copilot",
                amount=Decimal("10.00"),
                renewal_date=today + timedelta(days=8),
                frequency=Subscription.MONTHLY
            )

            self.stdout.write("Mock transaction data seeded successfully.")

        self.stdout.write("Database seeding complete!")
