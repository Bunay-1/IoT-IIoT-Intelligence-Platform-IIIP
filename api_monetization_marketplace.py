import uuid
import random
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum

class BillingModel(Enum):
    PAY_AS_YOU_GO = "pay_as_you_go"
    TIERED = "tiered"
    FIXED_RATE = "fixed_rate"

# --- Data Models ---

class APIProduct:
    def __init__(self, name: str, developer_id: str, billing_model: BillingModel, pricing: Dict[str, Any]):
        self.product_id = f"api_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.developer_id = developer_id
        self.billing_model = billing_model
        self.pricing = pricing
        self.total_calls = 0
        self.total_revenue = 0.0

class Developer:
    def __init__(self, name: str):
        self.developer_id = f"dev_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.balance = 0.0
        self.api_products: List[str] = []

class Consumer:
    def __init__(self, name: str):
        self.consumer_id = f"con_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.subscriptions: List[str] = []

class Subscription:
    def __init__(self, consumer_id: str, product_id: str):
        self.subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
        self.consumer_id = consumer_id
        self.product_id = product_id
        self.usage_this_month = 0
        self.is_active = True

# --- Core Marketplace Logic ---

class Marketplace:
    def __init__(self, platform_fee_percent: float = 10.0):
        self.platform_fee_percent = platform_fee_percent
        self.platform_revenue = 0.0

        self.api_products: Dict[str, APIProduct] = {}
        self.developers: Dict[str, Developer] = {}
        self.consumers: Dict[str, Consumer] = {}
        self.subscriptions: Dict[str, Subscription] = {}

    def register_developer(self, name: str) -> Developer:
        dev = Developer(name)
        self.developers[dev.developer_id] = dev
        print(f"[Marketplace] Developer '{name}' registered with ID {dev.developer_id}")
        return dev

    def register_consumer(self, name: str) -> Consumer:
        consumer = Consumer(name)
        self.consumers[consumer.consumer_id] = consumer
        print(f"[Marketplace] Consumer '{name}' registered with ID {consumer.consumer_id}")
        return consumer

    def list_api_product(self, developer_id: str, name: str, billing_model: BillingModel, pricing: Dict[str, Any]) -> APIProduct:
        if developer_id not in self.developers:
            raise ValueError("Developer not found")

        product = APIProduct(name, developer_id, billing_model, pricing)
        self.api_products[product.product_id] = product
        self.developers[developer_id].api_products.append(product.product_id)
        print(f"[Marketplace] API '{name}' listed by {self.developers[developer_id].name}")
        return product

    def subscribe_to_api(self, consumer_id: str, product_id: str) -> Subscription:
        if consumer_id not in self.consumers:
            raise ValueError("Consumer not found")
        if product_id not in self.api_products:
            raise ValueError("API Product not found")

        subscription = Subscription(consumer_id, product_id)
        self.subscriptions[subscription.subscription_id] = subscription
        self.consumers[consumer_id].subscriptions.append(subscription.subscription_id)
        print(f"[Marketplace] Consumer '{self.consumers[consumer_id].name}' subscribed to '{self.api_products[product_id].name}'")
        return subscription

    def track_api_usage(self, subscription_id: str, calls: int):
        if subscription_id not in self.subscriptions:
            return

        sub = self.subscriptions[subscription_id]
        sub.usage_this_month += calls

        product = self.api_products[sub.product_id]
        product.total_calls += calls

    def _calculate_cost(self, product: APIProduct, usage: int) -> float:
        """Calculates the cost for a given usage based on the billing model."""
        if product.billing_model == BillingModel.PAY_AS_YOU_GO:
            return usage * product.pricing['per_call']

        elif product.billing_model == BillingModel.FIXED_RATE:
            return product.pricing['monthly_fee']

        elif product.billing_model == BillingModel.TIERED:
            cost = 0
            remaining_usage = usage
            # Tiers should be sorted by 'up_to'
            sorted_tiers = sorted(product.pricing['tiers'], key=lambda x: x['up_to'])

            last_tier_limit = 0
            for tier in sorted_tiers:
                tier_limit = tier['up_to']
                tier_price = tier['price']

                calls_in_this_tier = max(0, min(remaining_usage, tier_limit - last_tier_limit))
                cost += calls_in_this_tier * tier_price
                remaining_usage -= calls_in_this_tier
                last_tier_limit = tier_limit

                if remaining_usage <= 0:
                    break

            # Overage
            if remaining_usage > 0:
                cost += remaining_usage * product.pricing['overage_price']

            return cost
        return 0.0

    def process_monthly_billing(self):
        """Processes billing for all subscriptions and handles revenue sharing."""
        print("\n" + "="*40)
        print(f"Processing Monthly Billing for {datetime.now().strftime('%Y-%m')}")
        print("="*40)

        total_billed_this_month = 0.0

        for sub in self.subscriptions.values():
            if not sub.is_active or sub.usage_this_month == 0:
                continue

            product = self.api_products[sub.product_id]
            developer = self.developers[product.developer_id]

            # 1. Calculate cost for the consumer
            cost = self._calculate_cost(product, sub.usage_this_month)
            total_billed_this_month += cost

            # 2. Calculate revenue share
            platform_fee = cost * (self.platform_fee_percent / 100)
            developer_revenue = cost - platform_fee

            # 3. Update balances
            self.platform_revenue += platform_fee
            developer.balance += developer_revenue
            product.total_revenue += cost

            print(f"- Subscription {sub.subscription_id[:8]}: {sub.usage_this_month} calls to '{product.name}'")
            print(f"  - Billed Cost: €{cost:.2f}")
            print(f"  - Developer '{developer.name}' Earns: €{developer_revenue:.2f}")

            # 4. Reset monthly usage
            sub.usage_this_month = 0

        print("-"*40)
        print(f"Total Billed This Month: €{total_billed_this_month:.2f}")
        print(f"Total Platform Revenue This Month: €{total_billed_this_month * (self.platform_fee_percent / 100):.2f}")
        print("="*40 + "\n")

# --- Simulation ---

class MarketplaceSimulator:
    def __init__(self):
        self.marketplace = Marketplace(platform_fee_percent=15.0)

    def setup(self):
        print("--- Setting up Marketplace ---")
        # Register participants
        dev1 = self.marketplace.register_developer("Geo-Services Inc.")
        dev2 = self.marketplace.register_developer("AI-Analytics Co.")

        con1 = self.marketplace.register_consumer("LogisticsApp")
        con2 = self.marketplace.register_consumer("WeatherDashboard")
        con3 = self.marketplace.register_consumer("AdTechPlatform")

        # List API products
        maps_api = self.marketplace.list_api_product(
            dev1.developer_id, "Maps & Routing API", BillingModel.TIERED,
            pricing={
                "tiers": [
                    {"up_to": 1000, "price": 0.005},
                    {"up_to": 10000, "price": 0.003},
                ],
                "overage_price": 0.002
            }
        )

        sentiment_api = self.marketplace.list_api_product(
            dev2.developer_id, "Sentiment Analysis API", BillingModel.PAY_AS_YOU_GO,
            pricing={"per_call": 0.01}
        )

        analytics_suite = self.marketplace.list_api_product(
            dev2.developer_id, "Full Analytics Suite", BillingModel.FIXED_RATE,
            pricing={"monthly_fee": 100.0}
        )

        # Create subscriptions
        self.marketplace.subscribe_to_api(con1.consumer_id, maps_api.product_id)
        self.marketplace.subscribe_to_api(con2.consumer_id, maps_api.product_id)
        self.marketplace.subscribe_to_api(con2.consumer_id, sentiment_api.product_id)
        self.marketplace.subscribe_to_api(con3.consumer_id, analytics_suite.product_id)
        print("--- Marketplace Setup Complete ---\n")

    def run_simulation(self, months: int):
        for month in range(1, months + 1):
            print(f"\n--- Simulating Month {month} ---")

            # Simulate random usage for each subscription
            for sub in self.marketplace.subscriptions.values():
                product = self.marketplace.api_products[sub.product_id]
                # Simulate higher usage for apps that would naturally use more
                if "Maps" in product.name:
                    usage = random.randint(500, 15000)
                else:
                    usage = random.randint(100, 2000)

                self.marketplace.track_api_usage(sub.subscription_id, usage)

            # Process billing at the end of the month
            self.marketplace.process_monthly_billing()

            self.print_summary()

    def print_summary(self):
        print("\n--- Current Marketplace Summary ---")
        print(f"Total Platform Revenue: €{self.marketplace.platform_revenue:.2f}")

        print("\nDeveloper Balances:")
        for dev in self.marketplace.developers.values():
            print(f"- {dev.name}: €{dev.balance:.2f}")

        print("\nAPI Product Performance:")
        for prod in self.marketplace.api_products.values():
            print(f"- {prod.name}: {prod.total_calls} calls, €{prod.total_revenue:.2f} total revenue")
        print("-" * 33 + "\n")

if __name__ == "__main__":
    simulator = MarketplaceSimulator()
    simulator.setup()
    simulator.run_simulation(months=3)