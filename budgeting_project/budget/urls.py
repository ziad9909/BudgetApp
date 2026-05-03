"""
URL patterns for the budget app.
Each URL is linked to a view function.
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── Authentication ──────────────────────────────────────────────────────
    path('signup/',  views.signup_view,  name='signup'),
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),

    # ── US7 – Dashboard (home page) ─────────────────────────────────────────
    path('', views.dashboard_view, name='dashboard'),

    # ── US2 – Transactions ──────────────────────────────────────────────────
    path('transactions/',     views.transaction_list_view, name='transaction_list'),
    path('transactions/add/', views.add_transaction_view,  name='add_transaction'),

    # ── US3 – Budgets ───────────────────────────────────────────────────────
    path('budgets/',              views.budget_list_view,   name='budget_list'),
    path('budgets/create/',       views.create_budget_view, name='create_budget'),
    path('budgets/edit/<int:budget_id>/',        views.edit_budget_view,        name='edit_budget'),
    path('budgets/recalculate/<int:budget_id>/', views.recalculate_budget_view, name='recalculate_budget'),

    # ── US4 – Alerts ────────────────────────────────────────────────────────
    path('alerts/', views.alerts_view, name='alerts'),

    # ── US5 – Savings Goals ─────────────────────────────────────────────────
    path('goals/',                          views.goals_view,            name='goals'),
    path('goals/contribute/<int:goal_id>/', views.contribute_to_goal_view, name='contribute'),

    # ── US6 – Reports ───────────────────────────────────────────────────────
    path('reports/', views.reports_view, name='reports'),
]
