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
from sklearn.model_selection import train_test_split

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
        self.config = config or self._get_default_config()

        # ML Models
        self.price_predictor = None
        self.volatility_predictor = None
        self.trade_classifier = None
        self.scaler = StandardScaler()

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

    async def train_models(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train ML models using historical market data.

        Args:
            historical_data: Historical price and volume data

        Returns:
            Training results
        """
        try:
            self.logger.info("Training AI models for trading agent")

            # Prepare data
            df = self._prepare_training_data(historical_data)

            if len(df) < 100:
                raise ValueError("Insufficient training data")

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
                "training_samples": len(df)
            }

        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            return {"error": str(e)}

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
        X = df[features]
        y = df['price_target']

        X_scaled = self.scaler.fit_transform(X)

        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
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
        current_market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate market price prediction.

        Args:
            current_market_data: Current market conditions

        Returns:
            Prediction results
        """
        try:
            # Prepare features
            features = self._extract_features(current_market_data)
            features_scaled = self.scaler.transform([features])

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

    def _extract_features(self, market_data: Dict[str, Any]) -> List[float]:
        """Extract features from market data for prediction."""
        # This would extract the same features used in training
        # Simplified implementation
        return [
            market_data["price"],
            market_data.get("volume", 0),
            market_data.get("volatility", 0),
            market_data.get("sma_24", market_data["price"]),
            market_data.get("rsi", 50)
        ]

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
            # Check risk limits
            if not self._check_risk_limits():
                return None

            # Generate trading signal
            signal = self._generate_trading_signal(prediction)

            if signal["action"] == "hold":
                return None

            # Calculate position size
            position_size = self._calculate_position_size(signal, market_data)

            if position_size == 0:
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

        if self.config["strategy"] == TradingStrategy.MOMENTUM.value:
            if price_change_pct > 2.0:  # Expected >2% increase
                return {"action": "buy", "strength": confidence, "expected_return": price_change_pct}
            elif price_change_pct < -2.0:  # Expected >2% decrease
                return {"action": "sell", "strength": confidence, "expected_return": abs(price_change_pct)}

        elif self.config["strategy"] == TradingStrategy.MEAN_REVERSION.value:
            if price_change_pct < -1.0:  # Expected price increase
                return {"action": "buy", "strength": confidence, "expected_return": abs(price_change_pct)}
            elif price_change_pct > 1.0:  # Expected price decrease
                return {"action": "sell", "strength": confidence, "expected_return": price_change_pct}

        return {"action": "hold", "reason": "no_clear_signal"}

    def _calculate_position_size(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
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
        if self._would_exceed_risk_limits(position_size, market_data["price"]):
            position_size = 0

        return position_size

    def _check_risk_limits(self) -> bool:
        """Check if current risk is within limits."""
        return self.current_risk < self.risk_limits["max_drawdown"]

    def _would_exceed_risk_limits(self, position_size: float, price: float) -> bool:
        """Check if proposed position would exceed risk limits."""
        position_value = position_size * price
        portfolio_value = sum(self.portfolio.values())

        if portfolio_value == 0:
            return False

        new_risk = position_value / portfolio_value
        return new_risk > self.risk_limits["max_position_risk"]

    async def _execute_trade(
        self,
        signal: Dict[str, Any],
        position_size: float,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual trade."""
        # In real implementation, this would interface with the trading marketplace
        # For now, simulate trade execution

        trade = {
            "trade_id": f"trade_{self.agent_id}_{int(datetime.now().timestamp())}",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "action": signal["action"],
            "energy_amount": position_size,
            "price": market_data["price"],
            "total_value": position_size * market_data["price"],
            "expected_return": signal.get("expected_return", 0),
            "strategy": self.config["strategy"],
            "market_conditions": market_data,
            "status": "executed"
        }

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
        initial_balance: float = 10000.0
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

            # Train models on subset of data
            train_data = historical_data[:int(len(historical_data) * 0.7)]
            await self.train_models(train_data)

            # Run backtest
            test_data = historical_data[int(len(historical_data) * 0.7):]

            for market_data in test_data:
                # Generate prediction
                prediction = await self.generate_market_prediction(market_data)

                # Execute strategy
                trade = await self.execute_trading_strategy(market_data, prediction)

                # Simulate market movement
                await asyncio.sleep(0.001)  # Small delay for simulation

            # Calculate performance metrics
            performance = self._calculate_performance_metrics()

            return {
                "status": "completed",
                "trades_executed": len(self.trade_history),
                "final_balance": self.portfolio.get("cash", 0) + self.portfolio.get("energy", 0) * 0.15,
                "performance": performance,
                "trade_history": self.trade_history[-10:]  # Last 10 trades
            }

        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            return {"error": str(e)}

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate trading performance metrics."""
        if not self.trade_history:
            return {"error": "No trades executed"}

        # Calculate returns
        initial_balance = 10000.0
        final_balance = self.portfolio.get("cash", 0) + self.portfolio.get("energy", 0) * 0.15
        total_return = (final_balance - initial_balance) / initial_balance * 100

        # Calculate win rate
        profitable_trades = sum(1 for trade in self.trade_history if trade.get("pnl", 0) > 0)
        win_rate = profitable_trades / len(self.trade_history) * 100

        # Calculate Sharpe ratio (simplified)
        returns = [trade.get("pnl", 0) for trade in self.trade_history]
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0

        # Calculate maximum drawdown
        portfolio_values = [10000.0]
        for trade in self.trade_history:
            pnl = trade.get("pnl", 0)
            portfolio_values.append(portfolio_values[-1] + pnl)

        peak = max(portfolio_values)
        trough = min(portfolio_values)
        max_drawdown = (peak - trough) / peak * 100

        return {
            "total_return_pct": total_return,
            "win_rate_pct": win_rate,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown,
            "total_trades": len(self.trade_history),
            "avg_trade_pnl": np.mean(returns) if returns else 0
        }

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


# Global trading agent instance
ai_trading_agent = AITradingAgent("primary_agent")


async def create_trading_agent(agent_id: str, config: Dict[str, Any]) -> AITradingAgent:
    """Create a new AI trading agent."""
    return AITradingAgent(agent_id, config)


async def get_market_prediction(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get market prediction from AI agent."""
    return await ai_trading_agent.generate_market_prediction(market_data)


async def execute_automated_trade(market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Execute automated trade based on AI prediction."""
    prediction = await ai_trading_agent.generate_market_prediction(market_data)
    return await ai_trading_agent.execute_trading_strategy(market_data, prediction)


async def run_strategy_backtest(
    historical_data: List[Dict[str, Any]],
    initial_balance: float = 10000.0
) -> Dict[str, Any]:
    """Run strategy backtest."""
    return await ai_trading_agent.backtest_strategy(historical_data, initial_balance)