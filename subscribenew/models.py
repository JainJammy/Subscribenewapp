from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import BaseUserManager,AbstractBaseUser

# Create your models here.

class CommonFields(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        abstract=True

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email,password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user




class CustomUser(AbstractBaseUser,CommonFields):
    email = models.EmailField(
        verbose_name="Email",
        max_length=255,
        unique=True,
    )
    name=models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    subscription=models.ManyToManyField("Subscription",related_name="subscribed_users",blank=True)
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    


    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return self.is_admin

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

class Subscription(models.Model):
    subscription_name=models.CharField(max_length=255)
    subscription_price=models.DecimalField(max_digits=10,decimal_places=2)
    next_billing_date=models.DateField(null=True,blank=True)
    trial_days=models.IntegerField(default=4)
    is_active=models.BooleanField(default=False)
    is_trial=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    card_token = models.CharField(max_length=255, blank=True, null=True)  # New field to store the card token

    def __str__(self):
        return self.subscription_name
    
class Payment(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.SET_NULL,related_name="payments",null=True)
    subscription=models.ForeignKey(Subscription,on_delete=models.SET_NULL,related_name="subscriptions",null=True)
    transcation_id=models.CharField(max_length=100,unique=True)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=20,choices=[('pending','Pending'),('completed','Completed'),('failed','Failed')])
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.transcation_id
    