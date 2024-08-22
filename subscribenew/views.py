from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from .serializers import CustomUserSerializer,LoginSerializer,UserSerilaizer,UserSubscription,SubscriptionSerializer,AvailableSubscriptionSerializer,UpdateBillingDetails
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .permission import IsAuthenticatedCustom
from .models import CustomUser,Subscription,Payment
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect
from paywix.payu import Payu
import datetime
import pdb
import hashlib
import uuid
import requests
# Create your views here.
from datetime import date, timedelta
import calendar
import json
import hashlib
def initate_monthly_recurring_payment(user,amount,id,authpayuid):
    txn_id = str(uuid.uuid4())
    #subscription = Subscription.objects.get(id=id)
    #authpayuid = subscription.authpayuid  # Retrieve the authpayuid

    var1_dict= {
        "authpayuid":authpayuid,
        "invoiceDisplayNumber": txn_id,
        "amount": str(amount),
        "txnid": txn_id,
        "phone": user.phone_number,
        "email": user.email,
        "udf2": "",
        "udf3": "",
        "udf4": "",
        "udf5": ""
    }
    var1=json.dumps(var1_dict)

    txn_id=str(uuid.uuid4())
    
    data = {
        'key': settings.PAYU_MERCHANT_KEY,
        'command': 'si_transaction',
        'var1': var1,
    }
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }



    # Generate hash for secure transaction
    #hash_string = '|'.join([str(data[key]) for key in sorted(data.keys())]) + '|' + settings.PAYU_MERCHANT_SALT
        # Generate hash for secure transaction
    hash_string = f"{data['key']}|{data['command']}|{var1}|{settings.PAYU_MERCHANT_SALT}"
    data['hash'] = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()

    #data['hash'] = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()

    # Send request to PayU
    response = requests.post(settings.PAYU_RECURRING_URL,headers=headers, data=data)
    print('Response of Json format',response)
    try:
       return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Non Json response received........",response.text)


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

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(["POST"])

def signup_request(request):
    #import pdb
    #pdb.set_trace()
    print("hello")
   # pdb.set_trace()
    if request.method == "POST":
        print(request.data)
        serializer=CustomUserSerializer(data=request.data)
        if not serializer.is_valid():
            errors={}
            for field,error in serializer.errors.items():
                if field == "email":
                    errors[field]="Invalid email or email or already in use"
                
                elif field == "password":
                     errors[field]="Password must be 8 characters long"

                else:
                    errors[field]=error[0]
            return Response({
                "status":"error",
                "message":"User creation failed due to invalid data",
                "errors":errors
            },status=status.HTTP_400_BAD_REQUEST)       
        user = serializer.save()
        print("user is",user)
        token=get_tokens_for_user(user)
        return Response({
        'status': 'success',
        'message': 'User created successfully.',
        'data': {
        'email': user.email,
        'name': user.name,
        },
        "token":token
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login_view(request):
    #pdb.set_trace()
    if request.method == "POST":
        print(request.data)
        serializer = LoginSerializer(data=request.data)
        print("serializer",serializer)
        if not serializer.is_valid():
            errors = {}
            
            # Custom error handling
            for field, error in serializer.errors.items():
                if field == 'email':
                    errors[field] = "Invalid email or password."
                elif field == 'password':
                    errors[field] = "Invalid email or password."
                else:
                    errors[field] = error[0]  

            return Response({
                'status': 'error',
                'message': 'Login failed',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.data.get("email")
        password=serializer.data.get("password")
        user=authenticate(email=email,password=password)
        #print("user is",user.name)
        if user is not None:
            token= get_tokens_for_user(user=user)
            
            return Response({
                'status': 'success',
                'message': 'Login successful.',
                'token': token,
                'data': {
                    'email': user.email,
                    'name': user.name
                },
                "token":token
            }, status=status.HTTP_200_OK)
        else:
            return Response({
            'status': 'error',
            'message': 'Login failed due to invalid credentials.',
            'errors': {
            'email': 'Invalid email or password.',
            'password': 'Invalid email or password.'
            }
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAuthenticatedCustom])
def get_user_email(request):
    try:
        user = CustomUser.objects.get(email__iexact=request.user.email)
        serializer = UserSerilaizer(user)
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticatedCustom])

def subscription_post_request(request):
    if request.method =="POST":
        subscription_name = request.data.get('subscription_name')
        if Subscription.objects.filter(subscription_name=subscription_name).exists():
            return Response(
                {"error": "Subscription name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer=UserSubscription(data=request.data)
        if serializer.is_valid():
            subscription=serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["GET"])
@permission_classes([IsAuthenticatedCustom])
def subscription_get_request(request):
    if request.method == "GET":
       user=request.user

       user_subscription=user.subscription.all()
       print(user_subscription)
       data={
           "subscribed":SubscriptionSerializer(user_subscription,many=True).data,
       }
       return Response(data,status=status.HTTP_200_OK)
@api_view(["POST"])
@permission_classes([IsAuthenticatedCustom])
def update_billing_user(request):
    if request.method == "POST":
        user=request.user
        if not user.is_admin:
            return Response({"error":"Only admin users can update the billing details"},status=status.HTTP_403_FORBIDDEN)
        try:
            print("request data",request.data)
            subscription = Subscription.objects.get(id=request.data.get('subscription_id'))
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UpdateBillingDetails(instance=subscription, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save() 
            return Response({"message": "Billing date updated successfully"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticatedCustom])
def avaiable_subscriptions_request(request):
    if request.method == "GET":
        user=request.user
        user_subscription=user.subscription.all()
        available_subscription=Subscription.objects.exclude(id__in=user_subscription.values_list('id',flat=True))
        data={
            "avaiable":AvailableSubscriptionSerializer(available_subscription,many=True).data
        }
        return Response(data,status=status.HTTP_200_OK)
    
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def cancel_subscription(request):
    try:
        user = request.user
        subscription_id = request.data.get('subscription_id')

        # Get the subscription object
        subscription = Subscription.objects.get(id=subscription_id)

        # Remove the association between user and subscription
        user.subscription.remove(subscription)

        # Set the subscription to inactive
        subscription.save()

        # Delete the associated payments
        Payment.objects.filter(user=user, subscription=subscription).delete()

        return Response({"message": "Subscription canceled successfully"}, status=status.HTTP_200_OK)
    except Subscription.DoesNotExist:
        return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticatedCustom])
def initiate_payment(request):
    subscription_id = request.data.get('subscription_id')
    user=request.user
    subscription = Subscription.objects.get(id=subscription_id)
    cu=CustomUser.objects.get(email=user)
    transaction_id = str(uuid.uuid4())

    payment = Payment.objects.create(
        user=cu,
        subscription=subscription,
        transcation_id=transaction_id,
        amount=subscription.subscription_price,
        status='pending',
    )
    today = datetime.date.today().strftime("%Y-%m-%d")
    si_details = {
        "billingAmount": str(payment.amount),
        "billingCurrency": "INR",
        "billingCycle": "DAILY",
        "billingInterval": 1,
        "paymentStartDate": today,  # Start today
        "paymentEndDate": (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),  # End tomorrow
    }


    key = settings.PAYU_MERCHANT_KEY
    txnid = transaction_id
    amount = str(payment.amount)
    productinfo = subscription.subscription_name
    firstname = request.user.name
    email = request.user.email
    #pg="CC"

    salt = settings.PAYU_MERCHANT_SALT
    si_details_str = json.dumps(si_details)  # Ensure si_details is converted to a JSON string
    api_version = "7"  # The API version you're using
    hash_string = f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{si_details_str}|{salt}|{api_version}"
    #hash_string = f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}||||||||||||{api_version}"
    hash_value = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()



    data = {
        'key': settings.PAYU_MERCHANT_KEY,
        'txnid': transaction_id,
        'amount': str(payment.amount),
        'productinfo': subscription.subscription_name,
        'firstname': request.user.name,
        'email': request.user.email,
        'phone': request.user.phone_number,
        #'pg':"CC",
        'si_details':json.dumps(si_details),
        'si':1,
        'surl': 'http://127.0.0.1:8000/usersubscription/payment_success/',  # Success URL
        'furl': 'http://127.0.0.1:8000/payment_failure/',  # Failure URL,
        #'store_card_token':'1',
        #'hash':hash_value
    }
    payu = Payu(
    settings.PAYU_MERCHANT_KEY,
    settings.PAYU_MERCHANT_SALT,
    "test" if settings.PAYU_MODE == "test" else "live"
    )
    response = payu.transaction(**data)
    print("Jammyresponse",response)
    # Check the response
   
    if 'action' in response:
        return Response({'message': 'Payment initiated successfully', 'data': response}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Payment initiation failed', 'data': response}, status=status.HTTP_400_BAD_REQUEST)




@csrf_exempt
def payment_success(request):
    response_data = request.POST
    print("response_data of authpayuid",response_data)
    txnid = response_data.get('txnid')
    payment = Payment.objects.get(transcation_id=txnid)
    print("payment",payment)
    print("response",response_data)
    #print("save card token is",response_data["cardToken"])
    #card_token=response_data["cardToken"]
    #print("card_token",card_token)
    if payment and payment.status!="completed":
        payment.status = 'completed'
        payment.save()
        #authpayuid = response_data.get('mihpayid')

        # Store the authpayuid in the user's subscription
        #if authpayuid:
            #print("MIPayuid",authpayuid)
            #payment.subscription.authpayuid = authpayuid  # If stored in the Subscription model
            #payment.subscription.save()


        # Update the subscription status
        #import pdb
        #pdb.set_trace()
        subscription = payment.subscription
        print("subscription success",subscription)
        subscription.is_active = True
        print("subscription is active",subscription.is_active)
        subscription.is_trial = False
        print("subscription is trial",subscription.is_trial)
        subscription.next_billing_date =calculate_next_billing_date(subscription)  # Implement your billing logic here
        print("subscription next",subscription.next_billing_date)
        #subscription.card_token=card_token
        #subscription.save()
        payment.user.subscription.add(subscription)
        payment.user.save()
        #authpayuid = response_data.get('authpayuid')
        #print("AUTHPAYUID",authpayuid)
        #response=initate_monthly_recurring_payment(payment.user,payment.amount,subscription.id,authpayuid)
        #print("response hitted url",response)
        #redirect_url=f"http://localhost:3000/subscriptions"
        #redirect_url=f"https://d3cq3vpq332mz9.cloudfront.net"
        redirect_url=f"https://d3rhp1eivkuqqo.cloudfront.net"
        return HttpResponseRedirect(redirect_url)

@csrf_exempt
@api_view(['POST'])
def auto_payment_success(request):
    print("request",request)
    # Extract the transaction details from the request
    txnid = request.data.get('txnid')
    subscription_name = request.data.get('productinfo')
    amount = request.data.get('amount')
    email = request.data.get('email')

    try:
        # Find the user and subscription based on the provided data
        user = CustomUser.objects.get(email=email)
        subscription = Subscription.objects.get(subscription_name=subscription_name)
        
        # Update the subscription's next billing date
        next_billing_date = subscription.next_billing_date + timedelta(days=30)  # Assuming a 30-day billing cycle
        subscription.next_billing_date = next_billing_date
        subscription.save()

        # Record the successful payment
        Payment.objects.create(
            user=user,
            subscription=subscription,
            transcation_id=txnid,
            amount=amount,
            status='completed'
        )
        redirect_url=f"https://d3rhp1eivkuqqo.cloudfront.net"
        #return Response({"message": "Payment successful and subscription updated."})
        return HttpResponseRedirect(redirect_url)

    except CustomUser.DoesNotExist:
        return Response({"error": "User not found."}, status=404)
    except Subscription.DoesNotExist:
        return Response({"error": "Subscription not found."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@csrf_exempt
def payment_failure(request):
    response_data = request.POST
    txnid = response_data.get('txnid')
    payment = Payment.objects.get(transcation_id=txnid)

    if payment:
        payment.status = 'failed'
        payment.save()

    return HttpResponse("Payment failed")

@csrf_exempt
def auto_payment_failure(request):
    response_data=request.POST
    print("response data",response_data)
    return HttpResponse("payment failed")