from datetime import datetime

import pandas as pd
import requests


class MarketplaceFluxFactor:
    def __init__(self, api_url, data_file):
        """
        Initialize the Marketplace Flux Factor module.
        Args:
            api_url (str): URL of the API to fetch electricity prices.
            data_file (str): Path to the file where data will be stored.
        """
        self.api_url = api_url
        self.data_file = data_file

    def fetch_electricity_price(self):
        """
        Fetch the current electricity price from the API.
        Returns:
            float: Current electricity price.
        """
        response = requests.get(self.api_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch electricity price: {response.text}")

        price_data = response.json()
        return price_data["price"]

    def calculate_eusd(self, price):
        """
        Calculate the daily EUSD based on the electricity price.
        Args:
            price (float): Current electricity price.
        Returns:
            float: Calculated EUSD.
        """
        # Example calculation (this can be customized based on actual requirements)
        eusd = price * 1.1  # Assume a 10% markup for simplicity
        return eusd

    def update_eusd(self):
        """
        Update the EUSD value based on the latest electricity price.
        """
        price = self.fetch_electricity_price()
        eusd = self.calculate_eusd(price)

        # Store the updated EUSD value
        data = {"timestamp": datetime.now().isoformat(), "price": price, "eusd": eusd}

        df = pd.DataFrame([data])
        df.to_csv(
            self.data_file,
            mode="a",
            header=not pd.io.common.file_exists(self.data_file),
            index=False,
        )

        print(f"EUSD updated successfully: {eusd} based on price {price}.")

    def run(self):
        """
        Run the daily update process.
        """
        self.update_eusd()
