from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:course_id>/', views.checkout, name='checkout'),
    path('create-checkout-session/<int:course_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.payment_success, name='success'),
    path('cancel/<int:course_id>/', views.payment_cancel, name='cancel'),
    path('history/', views.payment_history, name='history'),
    path('invoice/<int:payment_id>/', views.invoice, name='invoice'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('apply-coupon/<int:course_id>/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
] 