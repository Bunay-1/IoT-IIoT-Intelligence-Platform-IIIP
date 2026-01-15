"""
AI Trading Agent Module

This module implements AI-powered trading agents for automated energy trading,
market prediction, risk management, and portfolio optimization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
import matplotlib.pyplot as plt
import seaborn as sns

from utils.logging_config import get_logger

logger = get_logger(__name__)


class TradingStrategy(Enum):
    """Available trading strategies."""
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"


class RiskLevel(Enum):
    """Risk management levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class AITradingAgent:
    """
    AI-powered trading agent for automated energy trading.

    Features:
    - Market prediction using ML models
    - Automated trading strategy execution
    - Risk management and position sizing
    - Portfolio optimization
    - Backtesting framework
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AI trading agent.

        Args:
            agent_id: Unique agent identifier
            config: Agent configuration
        """
        self.agent_id = agent_id

        # Merge provided config with defaults
        default_config = self._get_default_config()
        if config:
            default_config.update(config)
        self.config = default_config

        # ML Models
        self.price_predictor = None
        self.volatility_predictor = None
        self.trade_classifier = None
        self.scaler = StandardScaler()
        self.training_features: Optional[List[str]] = None

        # Trading state
        self.portfolio: Dict[str, float] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}

        # Risk management
        self.risk_limits = self.config["risk_limits"]
        self.current_risk = 0.0

        # Market data
        self.market_data: List[Dict[str, Any]] = []
        self.predictions: List[Dict[str, Any]] = []

        self.logger = get_logger(__name__)
        self.logger.info(f"AI Trading Agent {agent_id} initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default agent configuration."""
        return {
            "strategy": TradingStrategy.MOMENTUM.value,
            "risk_level": RiskLevel.MODERATE.value,
            "max_position_size": 1000.0,  # kWh
            "max_portfolio_risk": 0.1,     # 10% max risk
            "prediction_horizon": 24,      # hours
            "rebalance_interval": 3600,    # 1 hour
            "backtest_period_days": 30,
            "confidence_threshold": 0.7,
            "risk_limits": {
                "max_drawdown": 0.05,      # 5%
                "max_daily_loss": 0.02,    # 2%
                "max_position_risk": 0.01, # 1%
                "var_limit": 0.95         # 95% VaR
            }
        }

    async def train_models(self, historical_data: List[Dict[str, Any]], tune_hyperparameters: bool = False) -> Dict[str, Any]:
        """
        Train ML models using historical market data.

        Args:
            historical_data: Historical price and volume data
            tune_hyperparameters: Whether to perform hyperparameter tuning

        Returns:
            Training results
        """
        try:
            self.logger.info("Training AI models for trading agent")

            # Prepare data
            df = self._prepare_training_data(historical_data)

            if len(df) < 100:
                raise ValueError("Insufficient training data")

            if tune_hyperparameters:
                self.logger.info("Hyperparameter tuning enabled.")
                # This can be a very long process, so we'll just demonstrate for one model
                tuned_params = await self.tune_hyperparameters(df)
                self.config['model_params'] = tuned_params

            # Train price prediction model
            self.price_predictor = await self._train_price_predictor(df)

            # Train volatility prediction model
            self.volatility_predictor = await self._train_volatility_predictor(df)

            # Train trade decision model
            self.trade_classifier = await self._train_trade_classifier(df)

            # Evaluate models
            evaluation = await self._evaluate_models(df)

            self.logger.info(f"AI models trained successfully. Performance: {evaluation}")
            return {
                "status": "trained",
                "models": ["price_predictor", "volatility_predictor", "trade_classifier"],
                "evaluation": evaluation,
                "training_samples": len(df),
                "hyperparameters_tuned": tune_hyperparameters
            }

        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            return {"error": str(e)}

    async def tune_hyperparameters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform hyperparameter tuning for the price predictor."""
        self.logger.info("Starting hyperparameter tuning for RandomForestRegressor...")
        features = [col for col in df.columns if col not in ['timestamp', 'price_target', 'trade_signal']]
        X = df[features]
        y = df['price_target']
        X_scaled = self.scaler.fit_transform(X)

        param_grid = {
            'n_estimators': [50, 100, 150],
            'max_depth': [5, 10, 15],
            'min_samples_leaf': [1, 2, 4]
        }

        grid_search = GridSearchCV(
            estimator=RandomForestRegressor(random_state=42, n_jobs=-1),
            param_grid=param_grid,
            cv=3,
            n_jobs=-1,
            scoring='neg_mean_squared_error'
        )

        # This will run in a thread pool executor to not block the event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, grid_search.fit, X_scaled, y)

        self.logger.info(f"Best parameters found: {grid_search.best_params_}")
        return grid_search.best_params_

    def _prepare_training_data(self, historical_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare historical data for ML training."""
        df = pd.DataFrame(historical_data)

        # Add technical indicators
        df['returns'] = df['price'].pct_change()
        df['volatility'] = df['returns'].rolling(window=24).std()
        df['sma_24'] = df['price'].rolling(window=24).mean()
        df['sma_168'] = df['price'].rolling(window=168).mean()
        df['rsi'] = self._calculate_rsi(df['price'])

        # Add lagged features
        for lag in [1, 2, 3, 6, 12, 24]:
            df[f'price_lag_{lag}'] = df['price'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)

        # Target variables
        df['price_target'] = df['price'].shift(-self.config["prediction_horizon"])
        df['trade_signal'] = (df['price_target'] > df['price'] * 1.02).astype(int)  # 2% profit target

        return df.dropna()

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    async def _train_price_predictor(self, df: pd.DataFrame) -> RandomForestRegressor:
        """Train price prediction model."""
        features = [col for col in df.columns if col not in ['timestamp', 'price_target', 'trade_signal']]
        self.training_features = features  # Save feature names
        X = df[features]
        y = df['price_target']

        X_scaled = self.scaler.fit_transform(X)

        params = self.config.get('model_params', {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42,
            'n_jobs': -1
        })
        model = RandomForestRegressor(**params)
        model.fit(X_scaled, y)

        return model

    async def _train_volatility_predictor(self, df: pd.DataFrame) -> RandomForestRegressor:
        """Train volatility prediction model."""
        features = [col for col in df.columns if col not in ['timestamp', 'price_target', 'trade_signal']]
        X = df[features]
        y = df['volatility']

        X_scaled = self.scaler.fit_transform(X)

        model = RandomForestRegressor(
            n_estimators=50,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled, y)

        return model

    async def _train_trade_classifier(self, df: pd.DataFrame) -> GradientBoostingClassifier:
        """Train trade decision model."""
        features = [col for col in df.columns if col not in ['timestamp', 'price_target', 'trade_signal']]
        X = df[features]
        y = df['trade_signal']

        X_scaled = self.scaler.fit_transform(X)

        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42
        )
        model.fit(X_scaled, y)

        return model

    async def _evaluate_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Evaluate trained models."""
        features = [col for col in df.columns if col not in ['timestamp', 'price_target', 'trade_signal']]
        X = df[features]
        X_scaled = self.scaler.transform(X)

        # Price prediction evaluation
        price_pred = self.price_predictor.predict(X_scaled)
        price_mape = np.mean(np.abs((df['price_target'] - price_pred) / df['price_target'])) * 100

        # Trade classification evaluation
        trade_pred = self.trade_classifier.predict(X_scaled)
        trade_accuracy = np.mean(trade_pred == df['trade_signal'])

        return {
            "price_prediction_mape": price_mape,
            "trade_classification_accuracy": trade_accuracy,
            "feature_importance": dict(zip(features, self.price_predictor.feature_importances_))
        }

    async def generate_market_prediction(
        self,
        current_market_data: Dict[str, Any],
        historical_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate market price prediction.

        Args:
            current_market_data: Current market conditions
            historical_df: DataFrame with historical data for feature calculation

        Returns:
            Prediction results
        """
        try:
            # Prepare features using historical context
            features = self._extract_features(current_market_data, historical_df)
            features_scaled = self.scaler.transform(features.to_frame().T)

            # Generate predictions
            predicted_price = self.price_predictor.predict(features_scaled)[0]
            predicted_volatility = self.volatility_predictor.predict(features_scaled)[0]
            trade_probability = self.trade_classifier.predict_proba(features_scaled)[0][1]

            prediction = {
                "timestamp": datetime.now().isoformat(),
                "current_price": current_market_data["price"],
                "predicted_price": predicted_price,
                "predicted_volatility": predicted_volatility,
                "trade_probability": trade_probability,
                "confidence": min(trade_probability, 1 - trade_probability) * 2,  # Convert to 0-1 scale
                "price_change_pct": (predicted_price - current_market_data["price"]) / current_market_data["price"] * 100,
                "horizon_hours": self.config["prediction_horizon"]
            }

            self.predictions.append(prediction)

            return prediction

        except Exception as e:
            self.logger.error(f"Market prediction failed: {e}")
            return {"error": str(e)}

    def _extract_features(self, market_data: Dict[str, Any], historical_df: pd.DataFrame) -> pd.Series:
        """Extract features from market data for prediction, using historical context."""
        # Create a temporary DataFrame for the new data point
        temp_df = pd.DataFrame([market_data])
        # Ensure timestamp is datetime object for proper indexing, handling potential ISO format string
        if isinstance(temp_df['timestamp'].iloc[0], str):
            temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'])
        temp_df = temp_df.set_index('timestamp')

        # Combine with historical data to calculate rolling features
        if isinstance(historical_df, pd.DataFrame) and not historical_df.empty:
            # Ensure index types match
            if not isinstance(historical_df.index, pd.DatetimeIndex):
                 historical_df.index = pd.to_datetime(historical_df.index)

            combined_price_series = pd.concat([historical_df['price'], temp_df['price']])
            combined_volume_series = pd.concat([historical_df['volume'], temp_df['volume']])
        else:
            combined_price_series = temp_df['price']
            combined_volume_series = temp_df['volume']


        # Use a temporary dataframe to calculate all features in a consistent way
        features = pd.DataFrame(index=temp_df.index)
        features['price'] = temp_df['price']
        features['volume'] = temp_df['volume']

        # Add technical indicators
        features['returns'] = combined_price_series.pct_change().iloc[-1]
        features['volatility'] = combined_price_series.rolling(window=24, min_periods=1).std().iloc[-1]
        features['sma_24'] = combined_price_series.rolling(window=24, min_periods=1).mean().iloc[-1]
        features['sma_168'] = combined_price_series.rolling(window=168, min_periods=1).mean().iloc[-1]
        features['rsi'] = self._calculate_rsi(combined_price_series).iloc[-1]

        # Add lagged features from the historical dataframe
        for lag in [1, 2, 3, 6, 12, 24]:
            if len(combined_price_series) > lag:
                features[f'price_lag_{lag}'] = combined_price_series.iloc[-(lag+1)]
                features[f'volume_lag_{lag}'] = combined_volume_series.iloc[-(lag+1)]
            else:
                features[f'price_lag_{lag}'] = np.nan
                features[f'volume_lag_{lag}'] = np.nan

        # Ensure order and columns match training
        if not self.training_features:
            raise ValueError("Model has not been trained yet, feature names are unknown.")
        features = features.reindex(columns=self.training_features)

        # Fill any missing values that might occur from lagging (e.g., at the start)
        features = features.fillna(method='ffill').fillna(method='bfill')

        # Final check to prevent any NaN values if all are missing
        features = features.fillna(0)

        return features.iloc[0]

    async def execute_trading_strategy(
        self,
        market_data: Dict[str, Any],
        prediction: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Execute trading strategy based on prediction.

        Args:
            market_data: Current market data
            prediction: Price prediction

        Returns:
            Trade execution result or None
        """
        try:
            portfolio_value = self.portfolio.get('cash', 0) + self.portfolio.get('energy', 0) * market_data['price']

            # Check risk limits
            if not self._check_risk_limits(portfolio_value):
                self.logger.warning("Trade halted due to risk limit breach.")
                return None

            # Generate trading signal
            signal = self._generate_trading_signal(prediction)

            if signal["action"] == "hold":
                return None

            # Calculate position size
            position_size = self._calculate_position_size(signal, market_data, portfolio_value)

            if position_size <= 0:
                return None

            # Execute trade
            trade = await self._execute_trade(signal, position_size, market_data)

            # Update portfolio
            self._update_portfolio(trade)

            # Update risk metrics
            self._update_risk_metrics()

            self.trade_history.append(trade)

            return trade

        except Exception as e:
            self.logger.error(f"Trading strategy execution failed: {e}")
            return None

    def _generate_trading_signal(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on prediction."""
        confidence = prediction["confidence"]
        price_change_pct = prediction["price_change_pct"]

        if confidence < self.config["confidence_threshold"]:
            return {"action": "hold", "reason": "low_confidence"}

        strategy = self.config["strategy"]

        if strategy == TradingStrategy.MOMENTUM.value:
            if price_change_pct > 2.0:
                return {"action": "buy", "strength": confidence, "expected_return": price_change_pct}
            elif price_change_pct < -2.0:
                return {"action": "sell", "strength": confidence, "expected_return": abs(price_change_pct)}

        elif strategy == TradingStrategy.MEAN_REVERSION.value:
            if prediction.get("rsi", 50) > 70 and price_change_pct > 1.0: # Overbought, expect drop
                return {"action": "sell", "strength": confidence, "expected_return": price_change_pct}
            elif prediction.get("rsi", 50) < 30 and price_change_pct < -1.0: # Oversold, expect rise
                return {"action": "buy", "strength": confidence, "expected_return": abs(price_change_pct)}

        elif strategy == TradingStrategy.ARBITRAGE.value:
            # Requires multiple market data sources, which we simulate here
            other_market_price = prediction.get("other_market_price", prediction['current_price'])
            price_diff = prediction['current_price'] - other_market_price
            if price_diff > 2.0: # Our market is expensive
                return {"action": "sell", "strength": confidence, "reason": "arbitrage_opportunity"}
            elif price_diff < -2.0: # Our market is cheap
                return {"action": "buy", "strength": confidence, "reason": "arbitrage_opportunity"}

        elif strategy == TradingStrategy.MARKET_MAKING.value:
            # Aims to profit from the bid-ask spread
            spread = prediction.get("bid_ask_spread", 0.5)
            if spread > 0.2: # If spread is wide enough, place buy and sell orders
                 # This is a simplified representation. A real market maker would place limit orders.
                return {"action": "market_make", "strength": confidence, "spread": spread}

        return {"action": "hold", "reason": "no_clear_signal"}

    def _calculate_position_size(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any],
        portfolio_value: float
    ) -> float:
        """Calculate position size based on risk management."""
        max_size = self.config["max_position_size"]
        risk_level = self.config["risk_level"]

        # Adjust for risk level
        if risk_level == RiskLevel.CONSERVATIVE.value:
            max_size *= 0.5
        elif risk_level == RiskLevel.AGGRESSIVE.value:
            max_size *= 1.5

        # Adjust for volatility
        volatility = market_data.get("volatility", 0.1)
        size_adjustment = 1.0 / (1.0 + volatility)  # Reduce size in high volatility

        # Adjust for signal strength
        signal_strength = signal.get("strength", 0.5)
        size_adjustment *= signal_strength

        position_size = max_size * size_adjustment

        # Check risk limits
        if self._would_exceed_risk_limits(position_size, market_data["price"], portfolio_value):
            position_size = 0

        return position_size

    def _check_risk_limits(self, portfolio_value: float) -> bool:
        """Check if current risk is within limits, including VaR."""
        # Check drawdown
        if self.current_risk >= self.risk_limits["max_drawdown"]:
            self.logger.warning("Risk limit exceeded: Max drawdown.")
            return False

        # Calculate and check Value at Risk (VaR)
        if self.trade_history:
            returns = pd.Series([t.get('pnl', 0) for t in self.trade_history if 'pnl' in t])
            if not returns.empty:
                var_limit_quantile = 1 - self.config["risk_limits"]["var_limit"]
                value_at_risk = returns.quantile(var_limit_quantile) * portfolio_value
                if abs(value_at_risk) > self.config["risk_limits"]["max_daily_loss"] * portfolio_value:
                    self.logger.warning(f"Risk limit exceeded: VaR ({value_at_risk:.2f}) is over the daily loss limit.")
                    return False

        return True

    def _would_exceed_risk_limits(self, position_size: float, price: float, portfolio_value: float) -> bool:
        """Check if proposed position would exceed risk limits."""
        position_value = position_size * price

        if portfolio_value == 0:
            return False

        new_risk = position_value / portfolio_value if portfolio_value > 0 else 0

        if new_risk > self.risk_limits["max_position_risk"]:
            self.logger.warning(f"Trade blocked: Position risk ({new_risk:.2%}) exceeds limit ({self.risk_limits['max_position_risk']:.2%}).")
            return True

        return False

    async def _execute_trade(
        self,
        signal: Dict[str, Any],
        position_size: float,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual trade."""
        # In real implementation, this would interface with the trading marketplace
        # For now, simulate trade execution

        trade_timestamp = datetime.now()
        trade = {
            "trade_id": f"trade_{self.agent_id}_{int(trade_timestamp.timestamp())}",
            "agent_id": self.agent_id,
            "timestamp": trade_timestamp.isoformat(),
            "action": signal["action"],
            "energy_amount": position_size,
            "price": market_data["price"],
            "total_value": position_size * market_data["price"],
            "expected_return": signal.get("expected_return", 0),
            "strategy": self.config["strategy"],
            "market_conditions": market_data,
            "status": "executed"
        }

        # Simulate P&L for backtesting
        if "price_target" in market_data:
            price_change = market_data["price_target"] - market_data["price"]
            if trade["action"] == "buy":
                trade["pnl"] = price_change * position_size
            elif trade["action"] == "sell":
                trade["pnl"] = -price_change * position_size
            else:
                trade["pnl"] = 0

        return trade

    def _update_portfolio(self, trade: Dict[str, Any]):
        """Update portfolio after trade execution."""
        energy_amount = trade["energy_amount"]
        price = trade["price"]

        if trade["action"] == "buy":
            self.portfolio["energy"] = self.portfolio.get("energy", 0) + energy_amount
            self.portfolio["cash"] = self.portfolio.get("cash", 10000) - (energy_amount * price)
        elif trade["action"] == "sell":
            self.portfolio["energy"] = self.portfolio.get("energy", 0) - energy_amount
            self.portfolio["cash"] = self.portfolio.get("cash", 0) + (energy_amount * price)

    def _update_risk_metrics(self):
        """Update risk metrics after portfolio changes."""
        # Calculate current portfolio value
        energy_value = self.portfolio.get("energy", 0) * 0.15  # Assume €0.15/kWh
        cash_value = self.portfolio.get("cash", 0)
        total_value = energy_value + cash_value

        # Calculate drawdown (simplified)
        if hasattr(self, 'peak_value'):
            drawdown = (self.peak_value - total_value) / self.peak_value
            self.current_risk = max(self.current_risk, drawdown)
        else:
            self.peak_value = total_value

    async def backtest_strategy(
        self,
        historical_data: List[Dict[str, Any]],
        initial_balance: float = 10000.0,
        tune_hyperparameters: bool = False
    ) -> Dict[str, Any]:
        """
        Backtest trading strategy on historical data.

        Args:
            historical_data: Historical market data
            initial_balance: Initial portfolio balance

        Returns:
            Backtest results
        """
        try:
            self.logger.info("Starting strategy backtest")

            # Reset portfolio
            self.portfolio = {"cash": initial_balance, "energy": 0}
            self.trade_history = []

            # Prepare dataframes
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp').sort_index()

            split_point = int(len(df) * 0.7)
            train_df = df.iloc[:split_point]
            test_df = df.iloc[split_point:]

            # Train models on subset of data
            await self.train_models(train_df.reset_index().to_dict('records'), tune_hyperparameters=tune_hyperparameters)

            # Run backtest
            history_df = train_df.copy()

            for timestamp, market_data_row in test_df.iterrows():
                market_data = market_data_row.to_dict()
                market_data['timestamp'] = timestamp.isoformat() # Add timestamp back in as iso string

                # We need to simulate the 'price_target' for PnL calculation
                current_time_index = test_df.index.get_loc(timestamp)
                if current_time_index + self.config['prediction_horizon'] < len(test_df):
                    market_data['price_target'] = test_df['price'].iloc[current_time_index + self.config['prediction_horizon']]
                else:
                    market_data['price_target'] = market_data['price'] # No future price available

                # Generate prediction using historical context
                prediction = await self.generate_market_prediction(market_data, history_df)
                if 'error' in prediction:
                    self.logger.error(f"Prediction failed for {timestamp}, skipping trade. Error: {prediction['error']}")
                    # Still need to update history
                    new_row_df = pd.DataFrame([market_data])
                    new_row_df['timestamp'] = pd.to_datetime(new_row_df['timestamp'])
                    new_row_df = new_row_df.set_index('timestamp')
                    history_df = pd.concat([history_df, new_row_df[train_df.columns.intersection(new_row_df.columns)]])
                    continue

                # Execute strategy
                trade = await self.execute_trading_strategy(market_data, prediction)

                # Update history for next iteration's feature calculation
                new_row_df = pd.DataFrame([market_data])
                new_row_df['timestamp'] = pd.to_datetime(new_row_df['timestamp'])
                new_row_df = new_row_df.set_index('timestamp')
                history_df = pd.concat([history_df, new_row_df[train_df.columns.intersection(new_row_df.columns)]])

                # Simulate market movement
                await asyncio.sleep(0.001)  # Small delay for simulation

            # Calculate performance metrics
            performance, portfolio_over_time = self._calculate_performance_metrics(initial_balance)
            self.performance_metrics = performance

            # Plot results
            self.plot_backtest_results(portfolio_over_time)

            return {
                "status": "completed",
                "trades_executed": len(self.trade_history),
                "final_balance": portfolio_over_time.iloc[-1]['total_value'] if not portfolio_over_time.empty else initial_balance,
                "performance": performance,
                "trade_history": self.trade_history[-10:],  # Last 10 trades
                "plot_path": f"{self.agent_id}_backtest_results.png"
            }

        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            return {"error": str(e)}

    def _calculate_performance_metrics(self, initial_balance: float) -> Tuple[Dict[str, Any], pd.DataFrame]:
        """Calculate trading performance metrics and portfolio value over time."""
        if not self.trade_history:
            return {"error": "No trades executed"}, pd.DataFrame()

        trade_df = pd.DataFrame(self.trade_history)
        trade_df['timestamp'] = pd.to_datetime(trade_df['timestamp'])
        trade_df = trade_df.set_index('timestamp').sort_index()

        trade_df['pnl'] = trade_df['pnl'].fillna(0)
        trade_df['cumulative_pnl'] = trade_df['pnl'].cumsum()
        trade_df['total_value'] = initial_balance + trade_df['cumulative_pnl']

        final_balance = trade_df['total_value'].iloc[-1]
        total_return = (final_balance - initial_balance) / initial_balance * 100

        profitable_trades = trade_df[trade_df['pnl'] > 0].shape[0]
        win_rate = profitable_trades / len(trade_df) * 100 if len(trade_df) > 0 else 0

        returns = trade_df['pnl']
        sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0

        # Max Drawdown
        rolling_max = trade_df['total_value'].cummax()
        drawdown = (trade_df['total_value'] - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min()) * 100

        metrics = {
            "total_return_pct": total_return,
            "win_rate_pct": win_rate,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown,
            "total_trades": len(self.trade_history),
            "avg_trade_pnl": returns.mean()
        }
        return metrics, trade_df[['total_value']]

    def plot_backtest_results(self, portfolio_over_time: pd.DataFrame):
        """Generate and save a plot of backtest results."""
        if portfolio_over_time.empty:
            self.logger.warning("Cannot plot results, no portfolio data available.")
            return

        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(15, 7))

        portfolio_over_time['total_value'].plot(ax=ax, color='navy', label='Portfolio Value')

        ax.set_title(f'Backtest Results for Agent {self.agent_id} ({self.config["strategy"]})', fontsize=16)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Portfolio Value (€)', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True)

        # Annotate with final metrics
        metrics_text = (
            f"Total Return: {self.performance_metrics['total_return_pct']:.2f}%\n"
            f"Sharpe Ratio: {self.performance_metrics['sharpe_ratio']:.2f}\n"
            f"Max Drawdown: {self.performance_metrics['max_drawdown_pct']:.2f}%"
        )
        ax.text(0.02, 0.98, metrics_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))

        plot_path = f"{self.agent_id}_backtest_results.png"
        plt.savefig(plot_path)
        plt.close(fig)
        self.logger.info(f"Backtest plot saved to {plot_path}")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        return {
            "agent_id": self.agent_id,
            "strategy": self.config["strategy"],
            "risk_level": self.config["risk_level"],
            "portfolio": self.portfolio,
            "current_risk": self.current_risk,
            "total_trades": len(self.trade_history),
            "active_positions": len(self.positions),
            "performance_metrics": self.performance_metrics,
            "last_prediction": self.predictions[-1] if self.predictions else None,
            "status": "active"
        }


class TradingAgentManager:
    """Manages multiple AI trading agents."""

    def __init__(self):
        self.agents: Dict[str, AITradingAgent] = {}
        self.logger = get_logger(__name__)

    def create_agent(self, agent_id: str, config: Optional[Dict[str, Any]] = None) -> AITradingAgent:
        """Create and register a new trading agent."""
        if agent_id in self.agents:
            raise ValueError(f"Agent with ID '{agent_id}' already exists.")

        agent = AITradingAgent(agent_id, config)
        self.agents[agent_id] = agent
        self.logger.info(f"Created new trading agent: {agent_id}")
        return agent

    def get_agent(self, agent_id: str) -> Optional[AITradingAgent]:
        """Retrieve a trading agent by its ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self.agents.keys())


async def run_live_simulation(agent: AITradingAgent, historical_data: List[Dict[str, Any]], duration_minutes: int = 1):
    """Run a live trading simulation."""
    logger.info(f"Starting live simulation for agent {agent.agent_id} for {duration_minutes} minutes.")
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)

    # Use historical data as the basis for the live simulation
    history_df = pd.DataFrame(historical_data)
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
    history_df = history_df.set_index('timestamp').sort_index()

    # Get the last known market state
    last_market_data = history_df.iloc[-1].to_dict()

    while datetime.now() < end_time:
        # Simulate a new market data tick
        price_change = np.random.normal(0, 0.5)
        last_market_data['price'] += price_change
        last_market_data['volume'] = int(max(0, last_market_data.get('volume', 1000) + np.random.randint(-100, 100)))
        current_timestamp = datetime.now()

        market_data = {
            "price": last_market_data['price'],
            "volume": last_market_data['volume'],
            "timestamp": current_timestamp.isoformat()
        }
        logger.info(f"[Live Sim] New market price: {market_data['price']:.2f}")

        # Generate prediction using the full history
        prediction = await agent.generate_market_prediction(market_data, history_df)
        if 'error' in prediction:
            logger.error(f"[Live Sim] Prediction failed: {prediction['error']}")
            new_row = pd.DataFrame([market_data])
            new_row['timestamp'] = pd.to_datetime(new_row['timestamp'])
            new_row = new_row.set_index('timestamp')
            history_df = pd.concat([history_df, new_row])
            await asyncio.sleep(5)
            continue

        logger.info(f"[Live Sim] Prediction: Price will be {prediction['predicted_price']:.2f} with {prediction['confidence']:.2%} confidence.")

        # Execute trade
        trade = await agent.execute_trading_strategy(market_data, prediction)
        if trade:
            logger.info(f"[Live Sim] Trade executed: {trade['action']} {trade['energy_amount']:.2f} kWh at €{trade['price']:.2f}")
        else:
            logger.info("[Live Sim] No trade executed.")

        await asyncio.sleep(5) # Wait for the next market tick

    logger.info("Live simulation finished.")


if __name__ == '__main__':

    def generate_sample_historical_data(days=90):
        """Generates sample time-series data for backtesting."""
        base_price = 100
        dates = pd.date_range(end=datetime.now(), periods=days * 24, freq='h')
        prices = base_price + np.random.randn(len(dates)).cumsum() * 0.4
        volumes = np.random.randint(500, 2000, size=len(dates))

        data = pd.DataFrame({'timestamp': dates, 'price': prices, 'volume': volumes})
        return data.to_dict('records')

    async def main():
        """Main execution block."""
        historical_data = generate_sample_historical_data()

        # Initialize the agent manager
        manager = TradingAgentManager()

        # Create a momentum trading agent
        momentum_agent_config = {
            "strategy": TradingStrategy.MOMENTUM.value,
            "risk_level": RiskLevel.MODERATE.value,
        }
        momentum_agent = manager.create_agent("momentum_agent_01", momentum_agent_config)

        # Train the agent's models (with optional hyperparameter tuning)
        logger.info("--- Training Momentum Agent ---")
        await momentum_agent.train_models(historical_data, tune_hyperparameters=False)

        # Run a backtest
        logger.info("\n--- Running Backtest for Momentum Agent ---")
        backtest_results = await momentum_agent.backtest_strategy(historical_data, initial_balance=10000.0)

        if 'error' in backtest_results:
            logger.error(f"Backtest failed: {backtest_results['error']}")
        else:
            logger.info(f"Backtest complete. Final Balance: €{backtest_results['final_balance']:.2f}")
            logger.info(f"Performance: {backtest_results['performance']}")
            logger.info(f"Results plot saved to: {backtest_results['plot_path']}")

        # Create a mean-reversion agent
        mean_reversion_agent_config = {
            "strategy": TradingStrategy.MEAN_REVERSION.value,
            "risk_level": RiskLevel.CONSERVATIVE.value
        }
        mean_reversion_agent = manager.create_agent("mean_reversion_agent_02", mean_reversion_agent_config)

        # Train and backtest the second agent
        logger.info("\n--- Training and Backtesting Mean Reversion Agent ---")
        await mean_reversion_agent.train_models(historical_data)
        await mean_reversion_agent.backtest_strategy(historical_data)

        # Run a short live simulation with the first agent
        logger.info("\n--- Starting Live Trading Simulation ---")
        # In a real scenario, the models should be trained on the most recent data
        await run_live_simulation(momentum_agent, historical_data, duration_minutes=1)

    # Run the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
