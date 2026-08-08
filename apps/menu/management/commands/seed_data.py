"""Seed MoodBite with synthetic data and pre-train the recommender."""
from django.core.management.base import BaseCommand
from apps.menu.models import MenuItem, Restaurant, MoodCategory
from apps.users.models import User, UserPreference
from apps.orders.models import Order, OrderItem, OrderStatusHistory, OrderRating
from apps.cart.models import Cart
from apps.recommendations.engine import engine
import random, uuid
from datetime import timedelta
from django.utils import timezone

RESTAURANTS = [
    ("Italian Kitchen", 4.5), ("Spice Garden", 4.3), ("Comfort Corner", 4.6),
    ("Healthy Bites", 4.4), ("Street Food Hub", 4.2), ("The Sweet Spot", 4.7),
    ("Zen Kitchen", 4.5), ("Fiesta Mexican", 4.3), ("Soothe & Brew", 4.6), ("FitFood", 4.4),
]

MOODS = [
    {"mood_id": "happy",       "label": "Happy",       "emoji": "😊", "color": "#FFD700", "description": "Feeling joyful and upbeat"},
    {"mood_id": "sad",         "label": "Sad",         "emoji": "😢", "color": "#4169E1", "description": "Need some comfort"},
    {"mood_id": "stressed",    "label": "Stressed",    "emoji": "😰", "color": "#FF6347", "description": "Need to de-stress"},
    {"mood_id": "tired",       "label": "Tired",       "emoji": "😴", "color": "#9370DB", "description": "Low energy, need fuel"},
    {"mood_id": "excited",     "label": "Excited",     "emoji": "🤩", "color": "#FF69B4", "description": "Full of energy"},
    {"mood_id": "romantic",    "label": "Romantic",    "emoji": "❤️", "color": "#DC143C", "description": "Special moments"},
    {"mood_id": "celebratory", "label": "Celebratory", "emoji": "🎉", "color": "#FFA500", "description": "Time to celebrate!"},
    {"mood_id": "bored",       "label": "Bored",       "emoji": "😑", "color": "#808080", "description": "Need something interesting"},
    {"mood_id": "energetic",   "label": "Energetic",   "emoji": "💪", "color": "#32CD32", "description": "Feeling active & strong"},
    {"mood_id": "anxious",     "label": "Anxious",     "emoji": "😟", "color": "#20B2AA", "description": "Need calm food"},
    {"mood_id": "soothing",    "label": "Soothing",    "emoji": "🧘", "color": "#87CEEB", "description": "Seeking peace & calm"},
    {"mood_id": "healthy",     "label": "Healthy",     "emoji": "🥗", "color": "#90EE90", "description": "Clean eating mode"},
    {"mood_id": "indulgent",   "label": "Indulgent",   "emoji": "🍫", "color": "#D2691E", "description": "Treating yourself"},
    {"mood_id": "focused",     "label": "Focused",     "emoji": "🎯", "color": "#9F79EE", "description": "Sharp mind, sharp food"},
]

IMAGES = {
    "comfort_food": "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=500",
    "main_course":  "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=500",
    "healthy":      "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
    "dessert":      "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=500",
    "starter":      "https://images.unsplash.com/photo-1541014741259-de529411b96a?w=500",
    "beverage":     "https://images.unsplash.com/photo-1544145945-f90425340c7e?w=500",
    "street_food":  "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d6?w=500",
    "breakfast":    "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=500",
    "snack":        "https://images.unsplash.com/photo-1582169296194-e4d644c48063?w=500",
}

ITEM_IMAGES = {
    "Mac & Cheese Bowl": "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=500",
    "Dal Makhani": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500",
    "Butter Chicken": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=500",
    "Chicken Biryani": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    "Paneer Tikka Masala": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500",
    "Margherita Pizza": "https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?w=500",
    "Pasta Arrabiata": "https://images.unsplash.com/photo-1563379971899-660589a01ec3?w=500",
    "Pad Thai": "https://images.unsplash.com/photo-1559314809-0d155014e29e?w=500",
    "Sushi Platter (8pcs)": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500",
    "Chole Bhature": "https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=500",
    "Veg Fried Rice": "https://images.unsplash.com/photo-1603133872878-685f5888a39a?w=500",
    "Quinoa Buddha Bowl": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
    "Greek Salad": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500",
    "Grilled Salmon": "https://images.unsplash.com/photo-1485921325814-a50431496cc9?w=500",
    "Avocado Toast": "https://images.unsplash.com/photo-1541532713592-79a0317b6b77?w=500",
    "Green Smoothie Bowl": "https://images.unsplash.com/photo-1511690656952-34342bb7c2f2?w=500",
    "Detox Salad": "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=500",
    "Protein Power Bowl": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
    "Chocolate Lava Cake": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500",
    "Gulab Jamun": "https://images.unsplash.com/photo-1589135304675-8f0dc0cc398d?w=500",
    "Cheesecake Slice": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=500",
    "Tiramisu": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500",
    "Mango Kulfi": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=500",
    "Samosa (2 pcs)": "https://images.unsplash.com/photo-1601050690597-df056fb4ce78?w=500",
    "Spring Rolls": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    "Bruschetta": "https://images.unsplash.com/photo-1572656631137-7935297eff55?w=500",
    "Chicken Wings": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=500",
    "Hummus & Pita": "https://images.unsplash.com/photo-1577906096429-f73cf1831d26?w=500",
    "Mango Lassi": "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=500",
    "Masala Chai": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500",
    "Cold Coffee": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=500",
    "Green Tea": "https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=500",
    "Fresh Lime Soda": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500",
    "Chamomile Honey Tea": "https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?w=500",
    "Protein Shake": "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=500",
    "Pav Bhaji": "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=500",
    "Vada Pav": "https://images.unsplash.com/photo-1601050690597-df056fb4ce78?w=500",
    "Tacos (3 pcs)": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=500",
    "Pani Puri": "https://images.unsplash.com/photo-1601050690597-df056fb4ce78?w=500",
    "Burrito Bowl": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
    "Masala Dosa": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=500",
    "Idli Sambar (4pcs)": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500",
    "Pancakes Stack": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=500",
    "Eggs Benedict": "https://images.unsplash.com/photo-1608039829572-78524f79c4c7?w=500",
}

# (name, description, price, category, cuisine, is_veg, mood_tags, calories, prep_time)
MENU_ITEMS = [
    # Comfort
    ("Mac & Cheese Bowl",     "Creamy macaroni with golden cheese crust",        299, "comfort_food", "Italian",     True,  ["tired","sad","stressed","indulgent"],         450, 25),
    ("Dal Makhani",           "Slow cooked black lentils in rich cream",          249, "comfort_food", "Indian",      True,  ["sad","tired","stressed","soothing"],          380, 35),
    # Main Course
    ("Butter Chicken",        "Classic North Indian butter chicken curry",        349, "main_course",  "Indian",      False, ["happy","tired","celebratory"],                520, 30),
    ("Chicken Biryani",       "Fragrant basmati rice with spiced chicken",        399, "main_course",  "Indian",      False, ["happy","celebratory","excited"],              650, 40),
    ("Paneer Tikka Masala",   "Cottage cheese in spiced tomato gravy",            329, "main_course",  "Indian",      True,  ["romantic","happy","indulgent"],               430, 30),
    ("Margherita Pizza",      "Classic tomato and mozzarella pizza",              399, "main_course",  "Italian",     True,  ["happy","celebratory","excited","indulgent"],   750, 25),
    ("Pasta Arrabiata",       "Penne in spicy tomato sauce",                      279, "main_course",  "Italian",     True,  ["stressed","bored","energetic"],               420, 25),
    ("Pad Thai",              "Thai stir-fried rice noodles",                     349, "main_course",  "Thai",        False, ["bored","excited","energetic","soothing"],      480, 20),
    ("Sushi Platter (8pcs)",  "Assorted Japanese sushi rolls",                   549, "main_course",  "Japanese",    False, ["romantic","stressed","anxious","soothing"],    320, 0),
    ("Chole Bhature",         "Spiced chickpeas with fried bread",                179, "main_course",  "Indian",      True,  ["happy","bored","tired","indulgent"],           580, 25),
    ("Veg Fried Rice",        "Wok tossed rice with vegetables",                  199, "main_course",  "Chinese",     True,  ["tired","bored","happy"],                      380, 15),
    # Healthy
    ("Quinoa Buddha Bowl",    "Nutritious bowl with roasted veggies",             349, "healthy",      "Continental", True,  ["energetic","stressed","anxious","healthy"],    320, 15),
    ("Greek Salad",           "Fresh vegetables with feta and olives",            249, "healthy",      "Continental", True,  ["stressed","anxious","energetic","healthy"],    180, 10),
    ("Grilled Salmon",        "Atlantic salmon with herbs and lemon",             549, "healthy",      "Continental", False, ["romantic","stressed","energetic","healthy"],   350, 25),
    ("Avocado Toast",         "Multigrain toast with fresh avocado",              249, "breakfast",    "Continental", True,  ["energetic","happy","healthy"],                280, 10),
    ("Green Smoothie Bowl",   "Spinach mango smoothie with granola",              299, "healthy",      "Continental", True,  ["energetic","anxious","healthy","soothing"],    250, 5),
    ("Detox Salad",           "Kale, beetroot, carrot with lemon dressing",       279, "healthy",      "Continental", True,  ["healthy","energetic","stressed"],             160, 10),
    ("Protein Power Bowl",    "Chickpeas, quinoa, grilled tofu, tahini",          369, "healthy",      "Continental", True,  ["energetic","healthy","focused"],              380, 15),
    # Dessert
    ("Chocolate Lava Cake",   "Warm chocolate cake with molten center",           199, "dessert",      "Italian",     True,  ["happy","sad","romantic","indulgent"],          450, 20),
    ("Gulab Jamun",           "Soft milk dumplings in rose syrup",                149, "dessert",      "Indian",      True,  ["happy","celebratory","sad","indulgent"],        380, 15),
    ("Cheesecake Slice",      "New York style creamy cheesecake",                 229, "dessert",      "Continental", True,  ["romantic","happy","celebratory","indulgent"],  420, 0),
    ("Tiramisu",              "Classic Italian coffee dessert",                   279, "dessert",      "Italian",     True,  ["romantic","tired","indulgent","soothing"],      380, 0),
    ("Mango Kulfi",           "Traditional Indian ice cream",                     129, "dessert",      "Indian",      True,  ["happy","excited","celebratory"],               280, 0),
    # Starters
    ("Samosa (2 pcs)",        "Crispy pastry with spiced potato filling",          99, "starter",      "Indian",      True,  ["bored","excited","happy"],                    220, 15),
    ("Spring Rolls",          "Crispy rolls with vegetable filling",              149, "starter",      "Chinese",     True,  ["bored","excited"],                            200, 15),
    ("Bruschetta",            "Toasted bread with tomato and basil",              199, "starter",      "Italian",     True,  ["romantic","happy"],                           180, 10),
    ("Chicken Wings",         "Spicy buffalo chicken wings",                      299, "starter",      "Continental", False, ["excited","bored","celebratory","indulgent"],   420, 20),
    ("Hummus & Pita",         "Creamy chickpea dip with warm pita bread",         199, "starter",      "Continental", True,  ["stressed","anxious","soothing"],              280, 0),
    # Beverages
    ("Mango Lassi",           "Sweet yogurt drink with fresh mango",              129, "beverage",     "Indian",      True,  ["happy","tired","excited","soothing"],          180, 0),
    ("Masala Chai",           "Spiced Indian tea with milk",                       79, "beverage",     "Indian",      True,  ["tired","stressed","sad","soothing"],            80, 0),
    ("Cold Coffee",           "Chilled coffee with ice cream",                    149, "beverage",     "Continental", True,  ["tired","bored","energetic","focused"],          180, 0),
    ("Green Tea",             "Calming Japanese green tea",                        99, "beverage",     "Japanese",    True,  ["stressed","anxious","tired","soothing","healthy"],5, 0),
    ("Fresh Lime Soda",       "Refreshing lemon soda with mint",                   79, "beverage",     "Continental", True,  ["energetic","happy","excited","healthy"],        30, 0),
    ("Chamomile Honey Tea",   "Calming chamomile with honey and lemon",            99, "beverage",     "Continental", True,  ["soothing","anxious","stressed","tired"],        10, 0),
    ("Protein Shake",         "Banana, peanut butter, oat milk protein shake",    169, "beverage",     "Continental", True,  ["energetic","healthy","focused","excited"],     220, 0),
    # Street Food
    ("Pav Bhaji",             "Mumbai style spiced vegetable with soft buns",     149, "street_food",  "Indian",      True,  ["bored","happy","tired","indulgent"],           380, 20),
    ("Vada Pav",              "Mumbai burger with spiced potato patty",            79, "street_food",  "Indian",      True,  ["bored","tired","indulgent"],                   280, 15),
    ("Tacos (3 pcs)",         "Mexican soft tacos with choice of filling",        299, "street_food",  "Mexican",     False, ["excited","bored","celebratory"],               380, 15),
    ("Pani Puri",             "Crispy shells with tangy spiced water",             89, "street_food",  "Indian",      True,  ["bored","excited","happy"],                    150, 10),
    ("Burrito Bowl",          "Mexican rice bowl with beans and salsa",           349, "street_food",  "Mexican",     True,  ["energetic","excited","healthy"],               480, 25),
    # Breakfast
    ("Masala Dosa",           "Crispy rice crepe with potato filling",             149, "breakfast",    "Indian",      True,  ["happy","energetic","tired"],                  320, 20),
    ("Idli Sambar (4pcs)",    "Steamed rice cakes with lentil soup",               99, "breakfast",    "Indian",      True,  ["stressed","tired","soothing","healthy"],        240, 15),
    ("Pancakes Stack",        "Fluffy pancakes with maple syrup",                 199, "breakfast",    "Continental", True,  ["happy","celebratory","sad","indulgent"],        450, 15),
    ("Eggs Benedict",         "Poached eggs on muffin with hollandaise",          299, "breakfast",    "Continental", False, ["romantic","happy","indulgent"],                420, 20),
    ("Overnight Oats",        "Rolled oats with chia, berries, almond milk",      199, "breakfast",    "Continental", True,  ["healthy","energetic","focused","soothing"],     280, 0),
    # Snacks
    ("Energy Bites",          "Dates, nuts, dark chocolate rolled balls",          149, "snack",        "Continental", True,  ["energetic","focused","healthy"],               180, 0),
    ("Nachos & Salsa",        "Crispy tortilla chips with salsa and guac",         229, "snack",        "Mexican",     True,  ["excited","bored","celebratory","indulgent"],   320, 10),
]


class Command(BaseCommand):
    help = 'Seed MoodBite with synthetic data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🌱 Seeding MoodBite..."))

        MoodCategory.objects.all().delete()
        for m in MOODS:
            MoodCategory.objects.create(**m)
        self.stdout.write("  ✅ Moods (14 moods incl. soothing, healthy, energetic, celebratory)")

        Restaurant.objects.all().delete()
        restaurants = [Restaurant.objects.create(name=n, rating=r) for n, r in RESTAURANTS]
        self.stdout.write("  ✅ Restaurants")

        MenuItem.objects.all().delete()
        menu_items = []
        for name, desc, price, cat, cuisine, veg, moods, cal, prep in MENU_ITEMS:
            mi = MenuItem.objects.create(
                name=name, description=desc, price=price, category=cat, cuisine=cuisine,
                is_vegetarian=veg, mood_tags=moods, calories=cal, preparation_time=prep,
                rating=round(random.uniform(3.8, 4.9), 1),
                reviews_count=random.randint(50, 2000),
                order_count=random.randint(100, 5000),
                image=ITEM_IMAGES.get(name, IMAGES.get(cat, IMAGES['main_course'])),
                protein=f"{random.randint(5, 35)}g",
                carbs=f"{random.randint(20, 80)}g",
                fat=f"{random.randint(5, 25)}g",
                ingredients=["Fresh ingredients", "Quality spices", "Locally sourced"],
                restaurant=random.choice(restaurants),
            )
            menu_items.append(mi)
        self.stdout.write(f"  ✅ {len(menu_items)} menu items")

        # Synthetic users
        names = [
            "Priya Sharma", "Rahul Verma", "Anita Singh", "Karan Mehta", "Sneha Patel",
            "Arjun Nair", "Pooja Gupta", "Vikram Joshi", "Deepa Reddy", "Rohan Das",
            "Isha Kapoor", "Amit Tiwari", "Neha Saxena", "Siddharth Roy", "Divya Kumar",
            "Manish Yadav", "Riya Agarwal", "Suresh Pillai", "Kavya Menon", "Aditya Shah",
        ]
        users = []
        for i, name in enumerate(names):
            email = f"user{i+1}@moodbite.demo"
            user, created = User.objects.get_or_create(email=email, defaults={'name': name})
            if created:
                user.set_password('demo1234')
                user.save()
                UserPreference.objects.create(user=user)
                Cart.objects.get_or_create(user=user)
            users.append(user)
        self.stdout.write(f"  ✅ {len(users)} demo users")

        # Synthetic orders spread over last 60 days
        MOOD_IDS = [m['mood_id'] for m in MOODS]
        Order.objects.all().delete()
        order_count, rating_count = 0, 0

        for _ in range(300):
            user = random.choice(users)
            # pick the mood the user ordered under
            ordered_under_mood = random.choice(MOOD_IDS)
            mood_items = [mi for mi in menu_items if ordered_under_mood in mi.mood_tags] or menu_items[:5]
            selected = random.sample(mood_items, min(random.randint(1, 3), len(mood_items)))
            subtotal = sum(float(mi.price) for mi in selected)

            # recommendation mood (could differ from order mood slightly)
            recommended_mood = ordered_under_mood if random.random() > 0.3 else random.choice(MOOD_IDS)

            days_ago = random.randint(0, 60)
            created_at = timezone.now() - timedelta(
                days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            status = random.choices(
                ['placed', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled'],
                weights=[2, 3, 5, 5, 75, 10])[0]

            order = Order(
                user=user,
                order_number=f"MB{str(uuid.uuid4().int)[:7]}",
                status=status,
                delivery_address={
                    "city": random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune"]),
                    "pincode": f"4{random.randint(10000, 99999)}",
                },
                payment_method=random.choice(['cod', 'upi', 'card', 'online']),
                subtotal=subtotal,
                taxes=round(subtotal * 0.1, 2),
                delivery_fee=50,
                discount=0,
                total=round(subtotal * 1.1 + 50, 2),
                # Store BOTH: mood under which order was placed AND mood filter recommended
                mood_context={
                    "detected_mood": ordered_under_mood,
                    "recommended_mood": recommended_mood,
                },
                estimated_delivery_time=created_at + timedelta(hours=1),
            )
            order.save()
            Order.objects.filter(pk=order.pk).update(created_at=created_at)

            for mi in selected:
                OrderItem.objects.create(
                    order=order, item=mi, item_name=mi.name,
                    quantity=1, price=mi.price, image=mi.image)

            OrderStatusHistory.objects.create(order=order, status='placed')

            if status == 'delivered':
                rating_val = random.choices([3, 4, 4, 5, 5, 5], k=1)[0]
                OrderRating.objects.create(
                    order=order, user=user, rating=rating_val,
                    food_rating=rating_val, delivery_rating=random.randint(3, 5))
                for mi in selected:
                    engine.update(ordered_under_mood, mi.id, float(rating_val))
                rating_count += 1

            order_count += 1

        self.stdout.write(f"  ✅ {order_count} synthetic orders, {rating_count} ratings → model trained")
        self.stdout.write(f"  ✅ Streaming model: {engine.total_updates} training samples")
        self.stdout.write(self.style.SUCCESS("🚀 MoodBite seeded successfully!\n"))
        self.stdout.write("  Demo login: user1@moodbite.demo / demo1234")
        self.stdout.write("  Admin: python manage.py createsuperuser")
