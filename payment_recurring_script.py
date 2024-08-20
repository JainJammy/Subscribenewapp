import os
import sys
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'usersubscribenextpart.settings')
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from subscribenew.serializers import CustomUserSerializer,LoginSerializer,UserSerilaizer,UserSubscription,SubscriptionSerializer,AvailableSubscriptionSerializer,UpdateBillingDetails
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from subscribenew.permission import IsAuthenticatedCustom
from subscribenew.models import CustomUser,Subscription,Payment
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect
from paywix.payu import Payu
from datetime import date,timedelta
import uuid
import calendar
#import os
#import django

#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'usersubscribenextpart.settings')
#django.setup()

def calculate_next_billing_date(subscription):
    """Calculate the next billing date based on the subscription's billing cycle."""
    print("hitted the part")
    current_date = date.today()
    
    if subscription.is_trial:
        print("httomg0",subscription.is_trial)
        # Assuming the trial period is 'trial_days' from the start date
        trial_end_date = subscription.created_at.date() + timedelta(days=subscription.trial_days)
        print("trial end date",trial_end_date)
        return trial_end_date
    
    month = current_date.month
    print("month",month)
    year = current_date.year
    print("year",year)

    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

    last_day_of_month = calendar.monthrange(year, month)[1]
    print("last_day_of_month",last_day_of_month)
    next_billing_day = min(current_date.day, last_day_of_month)
    print("next_billing_date",next_billing_day)
    next_billing_date = date(year, month, next_billing_day)
    print("Next Billing Date:",next_billing_date)
    return next_billing_date


def process_recurring_payments():
    today = date.today()
    subscriptions = Subscription.objects.filter(next_billing_date=today, is_active=True)
    #users = subscriptions.subscribed_users.all()  # Fetch all users for this subscription
    for subscription in subscriptions:
        print("Subscription details:", subscription)
        users = subscription.subscribed_users.all()  # Fetch all users for this subscription
        
        for user in users:
            # Verify if this user is correctly associated with this subscription
            if subscription in user.subscription.all():
                print(f"Processing payment for User: {user.name}, Email: {user.email}")
                card_token = subscription.card_token
                
                if not card_token:
                    continue  # Skip if no card token is stored
                
                # Prepare payment data
                data = {
                    'key': settings.PAYU_MERCHANT_KEY,
                    'txnid': str(uuid.uuid4()),
                    'amount': str(subscription.subscription_price),
                    'productinfo': subscription.subscription_name,
                    'firstname': user.name,
                    'email': user.email,
                    'phone': user.phone_number,
                    'furl':'http://127.0.0.0:8000/handle_auto_payment_success/',
                    'surl':'http://127.0.0.0:8000/handle_auto_payment_failure/',
                    'store_card_token': card_token,  # Use the stored card token
                }
                
                # Initiate the payment
                payu = Payu(
                    settings.PAYU_MERCHANT_KEY,
                    settings.PAYU_MERCHANT_SALT,
                    "test" if settings.PAYU_MODE == "test" else "live"
                )
                response = payu.transaction(**data)
                print("response",response)
                
                if 'success' in response:
                    # Update the subscription's next billing date
                    subscription.next_billing_date = calculate_next_billing_date(subscription)
                    subscription.save()
                    
                    # Record the payment in the database
                    Payment.objects.create(
                        user=user,
                        subscription=subscription,
                        transcation_id=response.get('txnid'),
                        amount=subscription.subscription_price,
                        status='completed'
                    )
                else:
                    # Handle payment failure
                    Payment.objects.create(
                        user=user,
                        subscription=subscription,
                        transcation_id=response.get('txnid'),
                        amount=subscription.subscription_price,
                        status='failed'
                    )


@csrf_exempt
@api_view(['POST'])
def handle_auto_payment_success(request):
    print("payment accepted")
    data = request.POST
    txnid = data.get('txnid')
    status = data.get('status')

    try:
        payment = Payment.objects.get(transcation_id=txnid)
        if status == 'success':
            payment.status = 'SUCCESS'
            subscription = payment.subscription
            subscription.next_billing_date = calculate_next_billing_date(subscription)
            subscription.save()
        else:
            payment.status = 'FAILED'
        payment.save()
    except Payment.DoesNotExist:
        print("Payment not found for txnid:", txnid)

    return JsonResponse({'status': 'received'}, status=200)

@csrf_exempt
@api_view(["POST"])
def handle_failure_payment(request):
    print("request")
if __name__ == "__main__":
    process_recurring_payments()

