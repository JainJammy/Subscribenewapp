from rest_framework import serializers
from .models import CustomUser,Subscription
from django.contrib.auth import authenticate
from datetime import date,timedelta

import pdb
class CustomUserSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True,required=True)
    class Meta:
        model=CustomUser
        fields=['email','name','password','phone_number']
    def create(self,validated_data):
        user=CustomUser.objects.create(
            email=validated_data["email"],
            name=validated_data["name"],
            phone_number=validated_data["phone_number"]

        )
        user.set_password(validated_data["password"])
        user.save()
        return user
    
    def validate_email(self,value):
        if CustomUser.objects.filter(email=value).exists():
            return serializers.ValidationError("This email is already in use")
        return value
    
    def validate_password(self,value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be 8 characters long")
        return value
class LoginSerializer(serializers.ModelSerializer):
    #pdb.set_trace()
    email = serializers.EmailField(max_length=255)
    class Meta:
        model=CustomUser
        fields=["email","password"]

class UserSerilaizer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=["email","is_admin"]   

class UserSubscription(serializers.ModelSerializer):
    class Meta:
        model=Subscription
        fields=["subscription_name","subscription_price"]
    
    def create(self, validated_data):
        print(validated_data)
        subscription_name=validated_data.get('subscription_name')
        subscription_price=validated_data.get('subscription_price')
        subscription=Subscription.objects.create(
            subscription_name=subscription_name,
            subscription_price=subscription_price
        )
        return subscription
    


class SubscriptionSerializer(serializers.ModelSerializer):
    #trial_days_left = serializers.SerializerMethodField()
    class Meta:
        model=Subscription
        fields=["id","subscription_name","subscription_price","is_active","next_billing_date"]
    """def get_trial_days_left(self, obj):
        if obj.is_trial:
            current_date = date.today()
            trial_end_date = obj.created_at.date() + timedelta(days=obj.trial_days)
            return (trial_end_date - current_date).days if current_date < trial_end_date else 0
        return 0"""
class AvailableSubscriptionSerializer(serializers.ModelSerializer):
    trial_days_left=serializers.SerializerMethodField()
    class Meta:
        model=Subscription
        fields=["id","subscription_name","subscription_price","is_trial","trial_days_left"]
    def get_trial_days_left(self, obj):
        if obj.is_trial:
            current_date = date.today()
            trial_end_date = obj.created_at.date() + timedelta(days=obj.trial_days)
            return (trial_end_date - current_date).days if current_date < trial_end_date else 0
        return 0
class UpdateBillingDetails(serializers.ModelSerializer):
    class Meta:
        model=Subscription
        fields=["id","next_billing_date"]
    def update(self,instance,validated_data):
        instance.next_billing_date=validated_data.get("next_billing_date",instance.next_billing_date)
        instance.save()
        return instance
    