from decimal import Decimal
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from .models import Transaction, Budget, SavingsGoal, Notification, Subscription

                                                                                                     
_EXPENSE_BREAKDOWN_PALETTE = [
    '#8b5cf6',
    '#a78bfa',
    '#c4b5fd',
    '#7c3aed',
    '#6366f1',
    '#a855f7',
    '#9333ea',
    '#6d28d9',
]


def _budget_period_overlaps(user, category, start_date, end_date, exclude_pk=None):
    """True if another budget exists for the same category with an overlapping date range (SRS US #4)."""
    qs = Budget.objects.filter(user=user, category=category)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.filter(start_date__lte=end_date, end_date__gte=start_date).exists()


               
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    errors = {}

    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username:
            errors['username'] = 'Username is required.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'This username is already taken.'

        if not email or '@' not in email:
            errors['email'] = 'Enter a valid email address.'

        if not password1:
            errors['password1'] = 'Password is required.'

        if password1 != password2:
            errors['password2'] = 'Passwords do not match.'

        if not errors:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, f'Welcome, {username}!')
            return redirect('dashboard')

    return render(request, 'budget/signup.html', {'errors': errors, 'old': request.POST})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Incorrect username or password.')

    return render(request, 'budget/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


                       
@login_required
def add_transaction_view(request):
    errors = {}

    if request.method == 'POST':
        ttype    = request.POST.get('transaction_type', '').strip()
        amt_str  = request.POST.get('amount', '').strip()
        category = request.POST.get('category', '').strip()
        date     = request.POST.get('date', '').strip()
        payment  = request.POST.get('payment_method', 'cash').strip()
        notes    = request.POST.get('notes', '').strip()

        if ttype not in ('expense', 'income'):
            errors['transaction_type'] = 'Please choose Expense or Income.'
        if not category:
            errors['category'] = 'Category is required.'
        if not date:
            errors['date'] = 'Date is required.'

        amount = None
        if not amt_str:
            errors['amount'] = 'Amount is required.'
        else:
            try:
                amount = Decimal(amt_str)
                if amount <= 0:
                    errors['amount'] = 'Amount must be greater than zero.'
            except Exception:
                errors['amount'] = 'Amount must be a number.'

        if not errors:
            t = Transaction.objects.create(
                user=request.user, transaction_type=ttype,
                amount=amount, category=category,
                date=date, payment_method=payment, notes=notes
            )
            if ttype == 'expense':
                _check_budget(request, t)
            messages.success(request, 'Transaction saved!')
            return redirect('transaction_list')

    return render(request, 'budget/add_transaction.html', {'errors': errors, 'old': request.POST})


@login_required
def transaction_list_view(request):
    transactions = Transaction.objects.filter(user=request.user)
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    if query:
        transactions = transactions.filter(
            models.Q(category__icontains=query)
            | models.Q(notes__icontains=query)
            | models.Q(payment_method__icontains=query)
            | models.Q(transaction_type__icontains=query)
        )

    if category:
        transactions = transactions.filter(category=category)

    categories = (
        Transaction.objects.filter(user=request.user)
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    return render(request, 'budget/transaction_list.html', {
        'transactions': transactions,
        'categories': categories,
        'query': query,
        'selected_category': category,
    })


def _check_budget(request, transaction):
                                                                                            
                                                                                         
    budget = (
        Budget.objects.filter(
            user=request.user,
            category=transaction.category,
            start_date__lte=transaction.date,
            end_date__gte=transaction.date,
        )
        .order_by('-start_date', '-id')
        .first()
    )
    if not budget:
        return

    budget.spent_amount += Decimal(str(transaction.amount))
    budget.save()

    status = budget.check_limit()
    if status == 'exceeded':
        Notification.objects.create(
            user=request.user,
            message=f'You exceeded your {transaction.category} budget!',
            notif_type='BUDGET_EXCEEDED',
        )
        messages.warning(request, f'You exceeded your {transaction.category} budget!')
    elif status == 'warning':
        Notification.objects.create(
            user=request.user,
            message=f'You are close to your {transaction.category} budget limit.',
            notif_type='BUDGET_ALERT',
        )
        messages.warning(request, f'You are close to your {transaction.category} budget limit.')


               
@login_required
def budget_list_view(request):
    budgets = Budget.objects.filter(user=request.user)
    return render(request, 'budget/budget_list.html', {'budgets': budgets})


@login_required
def create_budget_view(request):
    errors = {}

    if request.method == 'POST':
        category  = request.POST.get('category', '').strip()
        lmt_str   = request.POST.get('limit_amount', '').strip()
        start     = request.POST.get('start_date', '').strip()
        end       = request.POST.get('end_date', '').strip()
        threshold = int(request.POST.get('alert_threshold', 90) or 90)

        if not category:
            errors['category'] = 'Category is required.'
        if not start:
            errors['start_date'] = 'Start date is required.'
        if not end:
            errors['end_date'] = 'End date is required.'
        if start and end and start >= end:
            errors['end_date'] = 'End date must be after start date.'

        limit = None
        if not lmt_str:
            errors['limit_amount'] = 'Limit amount is required.'
        else:
            try:
                limit = Decimal(lmt_str)
                if limit <= 0:
                    errors['limit_amount'] = 'Limit must be greater than zero.'
            except Exception:
                errors['limit_amount'] = 'Limit must be a number.'

        sd, ed = parse_date(start), parse_date(end)
        if not errors and sd and ed and _budget_period_overlaps(request.user, category, sd, ed):
            errors['category'] = (
                'A budget for this category already exists for this month. '
                'Please edit the existing budget instead.'
            )

        if not errors:
            already_spent = Transaction.objects.filter(
                user=request.user,
                transaction_type='expense',
                category=category,
                date__gte=start,
                date__lte=end,
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

            Budget.objects.create(
                user=request.user, category=category,
                limit_amount=limit, start_date=start,
                end_date=end, alert_threshold=threshold,
                spent_amount=already_spent,
            )
            messages.success(request, f"Budget for '{category}' created!")
            return redirect('budget_list')

    return render(request, 'budget/create_budget.html', {'errors': errors, 'old': request.POST, 'action': 'Create'})


@login_required
def edit_budget_view(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    errors = {}

    if request.method == 'POST':
        category  = request.POST.get('category', '').strip()
        lmt_str   = request.POST.get('limit_amount', '').strip()
        start     = request.POST.get('start_date', '').strip()
        end       = request.POST.get('end_date', '').strip()
        threshold = int(request.POST.get('alert_threshold', 90) or 90)

        if not category:
            errors['category'] = 'Category is required.'
        if start and end and start >= end:
            errors['end_date'] = 'End date must be after start date.'

        limit = None
        if not lmt_str:
            errors['limit_amount'] = 'Limit amount is required.'
        else:
            try:
                limit = Decimal(lmt_str)
                if limit <= 0:
                    errors['limit_amount'] = 'Limit must be greater than zero.'
            except Exception:
                errors['limit_amount'] = 'Limit must be a number.'

        sd, ed = parse_date(start), parse_date(end)
        if (
            not errors
            and sd
            and ed
            and _budget_period_overlaps(request.user, category, sd, ed, exclude_pk=budget.id)
        ):
            errors['category'] = (
                'A budget for this category already exists for this month. '
                'Please edit the existing budget instead.'
            )

        if not errors:
            if limit < budget.spent_amount:
                messages.warning(request, f'New limit is lower than what you already spent ({budget.spent_amount} EGP).')
            budget.category = category
            budget.limit_amount = limit
            budget.start_date = start
            budget.end_date = end
            budget.alert_threshold = threshold
            budget.save()
            messages.success(request, 'Budget updated!')
            return redirect('budget_list')

    return render(request, 'budget/create_budget.html', {'errors': errors, 'budget': budget, 'action': 'Edit'})


@login_required
def recalculate_budget_view(request, budget_id):
    """Recalculate spent_amount for a budget from actual transactions."""
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    spent = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense',
        category=budget.category,
        date__gte=budget.start_date,
        date__lte=budget.end_date,
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    budget.spent_amount = spent
    budget.save()
    messages.success(request, f"Budget for '{budget.category}' recalculated: {spent} EGP spent.")
    return redirect('budget_list')


              
@login_required
def alerts_view(request):
    today = timezone.localdate()
    notifications = Notification.objects.filter(user=request.user)
    notifications.filter(is_read=False).update(is_read=True)

    budgets = Budget.objects.filter(user=request.user, start_date__lte=today, end_date__gte=today)
    budget_statuses = [{'budget': b, 'status': b.check_limit(), 'percentage': b.get_percentage()} for b in budgets]

    return render(request, 'budget/alerts.html', {
        'notifications': notifications,
        'budget_statuses': budget_statuses,
    })


             
@login_required
def goals_view(request):
    goals  = SavingsGoal.objects.filter(user=request.user)
    errors = {}

    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        tgt_str    = request.POST.get('target_amount', '').strip()
        deadline   = request.POST.get('deadline', '').strip()

        if not name:
            errors['name'] = 'Goal name is required.'
        if not deadline:
            errors['deadline'] = 'Deadline is required.'

        target = None
        if not tgt_str:
            errors['target_amount'] = 'Target amount is required.'
        else:
            try:
                target = Decimal(tgt_str)
                if target <= 0:
                    errors['target_amount'] = 'Target must be greater than zero.'
            except Exception:
                errors['target_amount'] = 'Target must be a number.'

        if not errors:
            SavingsGoal.objects.create(user=request.user, name=name, target_amount=target, deadline=deadline)
            messages.success(request, f"Goal '{name}' created!")
            return redirect('goals')

    return render(request, 'budget/goals.html', {'goals': goals, 'errors': errors, 'old': request.POST})


@login_required
def contribute_to_goal_view(request, goal_id):
    goal   = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
    errors = {}

    if request.method == 'POST':
        amt_str = request.POST.get('amount', '').strip()
        amount  = None
        if not amt_str:
            errors['amount'] = 'Amount is required.'
        else:
            try:
                amount = Decimal(amt_str)
                if amount <= 0:
                    errors['amount'] = 'Amount must be greater than zero.'
            except Exception:
                errors['amount'] = 'Amount must be a number.'

        if not errors:
            goal.update_saved_amount(amount)
            messages.success(request, f'Added {amount} EGP to "{goal.name}"!')
            if goal.status == 'completed':
                messages.success(request, f'You reached your goal "{goal.name}"!')
            return redirect('goals')

    return render(request, 'budget/contribute.html', {
        'goal': goal,
        'errors': errors,
        'remaining': goal.target_amount - goal.current_amount,
    })


               
@login_required
def reports_view(request):
    today = timezone.localdate()

    def _int_in_range(raw, default, lo, hi):
        try:
            n = int(raw)
            if lo <= n <= hi:
                return n
        except (TypeError, ValueError):
            pass
        return default

    month = _int_in_range(request.GET.get('month'), today.month, 1, 12)
    year = _int_in_range(request.GET.get('year'), today.year, 2000, 2100)

    transactions = Transaction.objects.filter(user=request.user, date__month=month, date__year=year)
    expenses     = transactions.filter(transaction_type='expense')
    incomes      = transactions.filter(transaction_type='income')

    total_expenses = sum(float(t.amount) for t in expenses)
    total_income   = sum(float(t.amount) for t in incomes)

    category_totals = {}
    for t in expenses:
        category_totals[t.category] = category_totals.get(t.category, 0) + float(t.amount)
    expense_analysis = []
    for cat, total in category_totals.items():
        percentage = (total / total_expenses * 100) if total_expenses else 0
        expense_analysis.append({
            'category': cat,
            'total': total,
            'percentage': round(percentage, 1),
        })
    expense_analysis.sort(key=lambda item: item['total'], reverse=True)
    for i, item in enumerate(expense_analysis):
        item['color'] = _EXPENSE_BREAKDOWN_PALETTE[i % len(_EXPENSE_BREAKDOWN_PALETTE)]
    report_pie_labels = [item['category'] for item in expense_analysis]
    report_pie_values = [item['total'] for item in expense_analysis]
    report_pie_colors = [item['color'] for item in expense_analysis]
    top_expense_category = expense_analysis[0] if expense_analysis else None

    if total_income > total_expenses:
        insight = f'You saved {total_income - total_expenses:.2f} EGP this month.'
    elif total_expenses > total_income:
        insight = f'You spent {total_expenses - total_income:.2f} EGP more than you earned.'
    else:
        insight = 'Income and expenses are balanced this month.'

    month_names = [
        (1,'January'),(2,'February'),(3,'March'),(4,'April'),
        (5,'May'),(6,'June'),(7,'July'),(8,'August'),
        (9,'September'),(10,'October'),(11,'November'),(12,'December'),
    ]

    return render(request, 'budget/reports.html', {
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'category_totals': category_totals,
        'expense_analysis': expense_analysis,
        'report_pie_labels': report_pie_labels,
        'report_pie_values': report_pie_values,
        'report_pie_colors': report_pie_colors,
        'top_expense_category': top_expense_category,
        'insight': insight,
        'month': month,
        'year': year,
        'month_names': month_names,
    })


                 
@login_required
def dashboard_view(request):
    today = timezone.localdate()
    all_transactions = list(Transaction.objects.filter(user=request.user))

    active_budgets = Budget.objects.filter(user=request.user, start_date__lte=today, end_date__gte=today)
    goals          = SavingsGoal.objects.filter(user=request.user, status='active')
    notifications  = Notification.objects.filter(user=request.user, is_read=False)

    total_income  = sum(float(t.amount) for t in all_transactions if t.transaction_type == 'income')
    total_expense = sum(float(t.amount) for t in all_transactions if t.transaction_type == 'expense')
    total_balance = total_income - total_expense

    monthly_income = sum(
        float(t.amount) for t in all_transactions
        if t.transaction_type == 'income' and t.date.month == today.month and t.date.year == today.year
    )
    monthly_expenses = sum(
        float(t.amount) for t in all_transactions
        if t.transaction_type == 'expense' and t.date.month == today.month and t.date.year == today.year
    )
    monthly_expense_totals = {}
    for t in all_transactions:
        if t.transaction_type == 'expense' and t.date.month == today.month and t.date.year == today.year:
            monthly_expense_totals[t.category] = monthly_expense_totals.get(t.category, 0) + float(t.amount)

    expense_breakdown = []
    for category, total in monthly_expense_totals.items():
        percentage = (total / monthly_expenses * 100) if monthly_expenses else 0
        expense_breakdown.append({
            'category': category,
            'total': total,
            'percentage': round(percentage, 1),
        })
    expense_breakdown.sort(key=lambda item: item['total'], reverse=True)
    for i, item in enumerate(expense_breakdown):
        item['color'] = _EXPENSE_BREAKDOWN_PALETTE[i % len(_EXPENSE_BREAKDOWN_PALETTE)]
    dashboard_pie_labels = [item['category'] for item in expense_breakdown]
    dashboard_pie_values = [item['total'] for item in expense_breakdown]
    dashboard_pie_colors = [item['color'] for item in expense_breakdown]

    budget_warnings = [
        {'budget': b, 'status': b.check_limit()}
        for b in active_budgets if b.check_limit() in ('warning', 'exceeded')
    ]

    return render(request, 'budget/dashboard.html', {
        'total_balance': total_balance,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'recent_transactions': all_transactions[:5],
        'active_budgets': active_budgets,
        'goals': goals,
        'notifications': notifications,
        'budget_warnings': budget_warnings,
        'expense_breakdown': expense_breakdown,
        'dashboard_pie_labels': dashboard_pie_labels,
        'dashboard_pie_values': dashboard_pie_values,
        'dashboard_pie_colors': dashboard_pie_colors,
    })


               
@login_required
def subscriptions_view(request):
    errors = {}

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        amt_str     = request.POST.get('amount', '').strip()
        billing_day = request.POST.get('billing_day', '1').strip()
        category    = request.POST.get('category', 'Subscription').strip()

        if not name:
            errors['name'] = 'Name is required.'
        amount = None
        if not amt_str:
            errors['amount'] = 'Amount is required.'
        else:
            try:
                amount = Decimal(amt_str)
                if amount <= 0:
                    errors['amount'] = 'Amount must be greater than zero.'
            except Exception:
                errors['amount'] = 'Amount must be a number.'
        try:
            billing_day = int(billing_day)
            if not (1 <= billing_day <= 28):
                errors['billing_day'] = 'Day must be between 1 and 28.'
        except ValueError:
            errors['billing_day'] = 'Day must be a number.'

        if not errors:
            Subscription.objects.create(
                user=request.user,
                name=name,
                amount=amount,
                billing_day=billing_day,
                category=category or 'Subscription',
            )
            messages.success(request, f"Subscription '{name}' added!")
            return redirect('subscriptions')

    subs = Subscription.objects.filter(user=request.user, is_active=True)
    return render(request, 'budget/subscriptions.html', {
        'subscriptions': subs,
        'errors': errors,
        'old': request.POST,
    })


@login_required
def pay_subscription_view(request, sub_id):
    sub = get_object_or_404(Subscription, id=sub_id, user=request.user)
    today = timezone.localdate()

    t = Transaction.objects.create(
        user=request.user,
        transaction_type='expense',
        amount=sub.amount,
        category=sub.category,
        date=today,
        payment_method='online',
        notes=f'Monthly subscription: {sub.name}',
    )
    _check_budget(request, t)

    sub.last_paid = today
    sub.save()

    messages.success(request, f"Paid {sub.amount} EGP for '{sub.name}'.")
    return redirect('subscriptions')


@login_required
def delete_subscription_view(request, sub_id):
    sub = get_object_or_404(Subscription, id=sub_id, user=request.user)
    name = sub.name
    sub.delete()
    messages.success(request, f"Subscription '{name}' removed.")
    return redirect('subscriptions')
