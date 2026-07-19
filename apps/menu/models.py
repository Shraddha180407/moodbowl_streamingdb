from django.db import models

class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    rating = models.FloatField(default=4.0)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        app_label = 'menu'

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    CATEGORIES = ['main_course','starter','dessert','beverage','snack',
                  'breakfast','comfort_food','healthy','street_food']
    CUISINES = ['Indian','Italian','Chinese','Mexican','Continental','Thai','Japanese']

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.URLField(blank=True)
    category = models.CharField(max_length=50)
    cuisine = models.CharField(max_length=50)
    rating = models.FloatField(default=4.0)
    reviews_count = models.IntegerField(default=0)
    is_vegetarian = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    preparation_time = models.IntegerField(default=20)
    calories = models.IntegerField(default=400)
    protein = models.CharField(max_length=10, default='15g')
    carbs = models.CharField(max_length=10, default='40g')
    fat = models.CharField(max_length=10, default='10g')
    ingredients = models.JSONField(default=list)
    customizations = models.JSONField(default=list)
    mood_tags = models.JSONField(default=list)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    order_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'menu'

    def __str__(self):
        return self.name

class MoodCategory(models.Model):
    mood_id = models.CharField(max_length=30, unique=True)
    label = models.CharField(max_length=50)
    emoji = models.CharField(max_length=10)
    color = models.CharField(max_length=10)
    description = models.CharField(max_length=200)

    class Meta:
        app_label = 'menu'
        verbose_name_plural = 'Mood Categories'

    def __str__(self):
        return self.label
