"""
Register models with the Django admin panel so you can view/edit data from /admin/.
"""

from django.contrib import admin
from .models import Transaction, Budget, SavingsGoal, Notification

# Register all models so they appear in the admin interface
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(SavingsGoal)
admin.site.register(Notification)

# Customize the admin site title
admin.site.site_header  = "Personal Budgeting Admin"
admin.site.site_title   = "BudgetApp Admin"
admin.site.index_title  = "Welcome to BudgetApp Administration"
