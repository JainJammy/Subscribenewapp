from django.contrib import admin
from django.urls import path
from subscribenew import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("signup/",views.signup_request),
    path("login/",views.login_view),
    path("profile/",views.get_user_email),
    path("api/token/refresh/",TokenRefreshView.as_view(),name="token_refresh"),
    path("add_subscription/",views.subscription_post_request),
    path("subscriptions/",views.subscription_get_request),
    path("avaiablesub/",views.avaiable_subscriptions_request),
    path("update_billing_details/",views.update_billing_user),
    path("initiate_payment/",views.initiate_payment),
    path("payment_success/",views.payment_success),
    path("autopayment_success/",views.auto_payment_success),
    path("handle_auto_payment_success/",views.handle_auto_payment_success),
    path("payment_failure/",views.payment_failure),
    path("cancel_subscription/",views.cancel_subscription),
    path("")
    #path("handle_auto_payment_success/",views.handle_auto_payment_success)
]
