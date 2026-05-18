from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.CharField(max_length=280, blank=True)
    preferred_currency = models.CharField(max_length=10, default='EGP')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def get_display_name(self):
        return self.display_name.strip() or self.user.get_full_name() or self.user.username

    def __str__(self):
        return f"Profile: {self.get_display_name()}"

    class Meta:
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


                                                 
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


                                             
class Budget(models.Model):

    user            = models.ForeignKey(User, on_delete=models.CASCADE)
    category        = models.CharField(max_length=100)
    limit_amount    = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alert_threshold = models.IntegerField(default=90)                               
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


                                                         
class Subscription(models.Model):

    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    name        = models.CharField(max_length=200)
    service_key = models.CharField(max_length=50, blank=True, default='')
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    billing_day = models.IntegerField(default=1)                               
    category    = models.CharField(max_length=100, default='Subscription')
    is_active   = models.BooleanField(default=True)
    last_paid   = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def get_brand(self):
        from .data.subscription_services import resolve_subscription_brand
        return resolve_subscription_brand(self.service_key, self.name)

    def is_due(self):
        """True if never paid this month or last paid in a previous month."""
        from django.utils import timezone
        today = timezone.localdate()
        if self.last_paid is None:
            return True
        return self.last_paid.year < today.year or self.last_paid.month < today.month

    def __str__(self):
        return f"{self.name} – {self.amount} EGP/month"

    class Meta:
        ordering = ['name']


                                                        
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
