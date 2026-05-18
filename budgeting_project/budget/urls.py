"""
URL patterns for the budget app.
Each URL is linked to a view function.
"""

from django.urls import path
from . import views

urlpatterns = [
                                                                              
    path('signup/',  views.signup_view,  name='signup'),
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),

    path('profile/', views.profile_view, name='profile'),

                                                                              
    path('', views.dashboard_view, name='dashboard'),

                                                                              
    path('transactions/',     views.transaction_list_view, name='transaction_list'),
    path('transactions/add/', views.add_transaction_view,  name='add_transaction'),

                                                                              
    path('budgets/',              views.budget_list_view,   name='budget_list'),
    path('budgets/create/',       views.create_budget_view, name='create_budget'),
    path('budgets/edit/<int:budget_id>/',        views.edit_budget_view,        name='edit_budget'),
    path('budgets/recalculate/<int:budget_id>/', views.recalculate_budget_view, name='recalculate_budget'),

                                                                              
    path('alerts/', views.alerts_view, name='alerts'),

                                                                              
    path('goals/',                          views.goals_view,            name='goals'),
    path('goals/contribute/<int:goal_id>/', views.contribute_to_goal_view, name='contribute'),

                                                                              
    path('reports/', views.reports_view, name='reports'),

                                                                              
    path('subscriptions/',                          views.subscriptions_view,       name='subscriptions'),
    path('subscriptions/pay/<int:sub_id>/',         views.pay_subscription_view,    name='pay_subscription'),
    path('subscriptions/delete/<int:sub_id>/',      views.delete_subscription_view, name='delete_subscription'),

    path('api/voice-transaction/',      views.voice_transaction_api,      name='voice_transaction_api'),
    path('api/voice-transaction/save/', views.voice_transaction_save_api, name='voice_transaction_save_api'),
]
