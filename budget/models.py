from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


# stores every income or expense the user records
class Transaction(models.Model):

    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('income',  'Income'),
    ]

    PAYMENT_CHOICES = [
        ('cash',   'Cash'),
        ('card',   'Card'),
        ('online', 'Online'),
    ]

    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    category         = models.CharField(max_length=100)
    date             = models.DateField()
    payment_method   = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} EGP ({self.category})"

    class Meta:
        ordering = ['-date']


# spending limit the user sets for a category
class Budget(models.Model):

    user            = models.ForeignKey(User, on_delete=models.CASCADE)
    category        = models.CharField(max_length=100)
    limit_amount    = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alert_threshold = models.IntegerField(default=90)  # warn at this % of the limit
    start_date      = models.DateField()
    end_date        = models.DateField()

    def get_remaining(self):
        return self.limit_amount - self.spent_amount

    def get_percentage(self):
        if self.limit_amount == 0:
            return 0
        return round((self.spent_amount / self.limit_amount) * 100, 1)

    def check_limit(self):
        if self.limit_amount == 0:
            return 'ok'
        pct = (self.spent_amount / self.limit_amount) * 100
        if pct >= 100:
            return 'exceeded'
        elif pct >= self.alert_threshold:
            return 'warning'
        return 'ok'

    def __str__(self):
        return f"{self.category} budget ({self.start_date} to {self.end_date})"

    class Meta:
        ordering = ['category']


# a savings target the user wants to reach by a deadline
class SavingsGoal(models.Model):

    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('paused',    'Paused'),
    ]

    user           = models.ForeignKey(User, on_delete=models.CASCADE)
    name           = models.CharField(max_length=200)
    target_amount  = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline       = models.DateField()
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at     = models.DateTimeField(auto_now_add=True)

    def update_saved_amount(self, amount):
        self.current_amount += Decimal(str(amount))
        if self.current_amount >= self.target_amount:
            self.status = 'completed'
        self.save()

    def get_completion_percentage(self):
        if self.target_amount == 0:
            return 0
        pct = (self.current_amount / self.target_amount) * 100
        return round(min(pct, 100), 1)

    def __str__(self):
        return f"{self.name} - {self.get_completion_percentage()}% done"

    class Meta:
        ordering = ['deadline']


# notifications sent to the user (budget warnings, etc.)
class Notification(models.Model):

    TYPE_CHOICES = [
        ('BUDGET_ALERT',    'Budget Alert'),
        ('BUDGET_EXCEEDED', 'Budget Exceeded'),
        ('GOAL_COMPLETED',  'Goal Completed'),
        ('INFO',            'Info'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    message    = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='INFO')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.notif_type}] {self.message[:50]}"

    class Meta:
        ordering = ['-created_at']
