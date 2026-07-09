"""
Computer Vision for Industrial Maintenance
Advanced defect detection, anomaly identification, and predictive maintenance using CV
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import cv2

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DefectDetector(nn.Module):
    """CNN-based defect detection model."""

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256 * 4 * 4, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


class AnomalyDetector:
    """Autoencoder-based anomaly detection."""

    def __init__(self, input_dim: Tuple[int, int, int] = (3, 224, 224)):
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 64, 4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, 4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, 4, stride=2, padding=1),
            nn.ReLU()
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 3, 4, stride=2, padding=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

    def detect_anomaly(self, image: torch.Tensor, threshold: float = 0.1) -> Dict[str, Any]:
        """Detect anomalies in image."""
        with torch.no_grad():
            reconstructed = self.forward(image.unsqueeze(0))
            mse = nn.MSELoss()(reconstructed, image.unsqueeze(0)).item()
            is_anomaly = mse > threshold

        return {
            "is_anomaly": is_anomaly,
            "reconstruction_error": mse,
            "threshold": threshold,
            "confidence": 1 - min(mse / threshold, 1)
        }


class SurfaceInspector:
    """Advanced surface inspection using traditional CV and deep learning."""

    def __init__(self):
        self.orb = cv2.ORB_create()
        self.sift = cv2.SIFT_create() if hasattr(cv2, 'SIFT_create') else None

    def detect_surface_defects(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect surface defects using multiple methods."""
        defects = []

        # Method 1: Threshold-based defect detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small noise
                x, y, w, h = cv2.boundingRect(contour)
                defects.append({
                    "type": "threshold_defect",
                    "bbox": [x, y, x+w, y+h],
                    "area": area,
                    "severity": "medium" if area > 1000 else "low"
                })

        # Method 2: Edge-based defect detection
        edges = cv2.Canny(gray, 50, 150)
        edge_contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in edge_contours:
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 50:
                defects.append({
                    "type": "edge_defect",
                    "contour": contour.tolist(),
                    "perimeter": perimeter,
                    "severity": "high" if perimeter > 200 else "medium"
                })

        return {
            "total_defects": len(defects),
            "defects": defects,
            "methods_used": ["threshold", "edge_detection"]
        }


class MaintenanceRecommender:
    """AI-powered maintenance recommendation system."""

    def __init__(self):
        self.maintenance_rules = {
            "corrosion": {
                "severity_threshold": 0.7,
                "recommendations": ["Immediate inspection required", "Apply protective coating"],
                "priority": "high"
            },
            "crack": {
                "severity_threshold": 0.5,
                "recommendations": ["Structural integrity check", "Monitor crack growth"],
                "priority": "critical"
            },
            "wear": {
                "severity_threshold": 0.6,
                "recommendations": ["Schedule replacement", "Monitor wear rate"],
                "priority": "medium"
            }
        }

    def generate_recommendations(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate maintenance recommendations based on analysis."""
        recommendations = []
        actions = []
        schedule = "as_needed"

        defects = analysis_results.get("defects", [])
        anomalies = analysis_results.get("anomalies", [])

        # Process defects
        for defect in defects:
            defect_type = defect.get("type", "unknown")
            severity = defect.get("severity", "low")

            if defect_type in self.maintenance_rules:
                rule = self.maintenance_rules[defect_type]
                if self._calculate_severity_score(severity) >= rule["severity_threshold"]:
                    recommendations.extend(rule["recommendations"])
                    if rule["priority"] == "critical":
                        schedule = "immediate"
                    elif rule["priority"] == "high" and schedule == "as_needed":
                        schedule = "within_week"

        # Process anomalies
        if anomalies:
            recommendations.append("Anomaly detected - investigate unusual patterns")
            actions.append("Schedule detailed inspection")

        # Generate preventive actions
        if len(defects) > 5:
            recommendations.append("High defect density detected - consider system overhaul")
            schedule = "immediate"

        return {
            "recommendations": list(set(recommendations)),  # Remove duplicates
            "actions": actions,
            "schedule": schedule,
            "priority_score": self._calculate_priority_score(defects, anomalies)
        }

    def _calculate_severity_score(self, severity: str) -> float:
        """Convert severity string to numerical score."""
        severity_map = {"low": 0.3, "medium": 0.6, "high": 0.8, "critical": 1.0}
        return severity_map.get(severity.lower(), 0.5)

    def _calculate_priority_score(self, defects: List[Dict], anomalies: List[Dict]) -> float:
        """Calculate overall maintenance priority score."""
        defect_score = min(len(defects) * 0.1, 1.0)
        anomaly_score = min(len(anomalies) * 0.2, 1.0)

        return max(defect_score, anomaly_score)


class ComputerVisionMaintenance:
    """Complete computer vision system for industrial maintenance."""

    def __init__(self, device: str = 'cpu'):
        self.device = device
        self.defect_detector = DefectDetector()
        self.anomaly_detector = AnomalyDetector()
        self.surface_inspector = SurfaceInspector()
        self.recommender = MaintenanceRecommender()

        # Move models to device
        self.defect_detector.to(device)
        self.anomaly_detector.to(device)

        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Comprehensive image analysis for maintenance."""
        try:
            logger.info(f"Analyzing image: {image_path}")

            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            tensor_image = self.transform(image).unsqueeze(0).to(self.device)

            # Convert to numpy for traditional CV
            cv_image = cv2.imread(image_path)
            if cv_image is None:
                cv_image = np.array(image)[:, :, ::-1]  # RGB to BGR

            results = {
                "image_path": image_path,
                "timestamp": asyncio.get_event_loop().time(),
                "status": "analyzed"
            }

            # Defect detection with DL
            with torch.no_grad():
                defect_outputs = self.defect_detector(tensor_image)
                defect_probs = torch.softmax(defect_outputs, dim=1)
                defect_confidence, defect_class = torch.max(defect_probs, dim=1)

            results["defect_detection"] = {
                "predicted_class": defect_class.item(),
                "confidence": defect_confidence.item(),
                "defect_types": ["corrosion", "crack", "wear", "normal"]  # Mock classes
            }

            # Anomaly detection
            anomaly_result = self.anomaly_detector.detect_anomaly(tensor_image.squeeze(0))
            results["anomaly_detection"] = anomaly_result

            # Surface inspection
            surface_defects = self.surface_inspector.detect_surface_defects(cv_image)
            results["surface_inspection"] = surface_defects

            # Combine defects
            all_defects = surface_defects["defects"]
            if anomaly_result["is_anomaly"]:
                all_defects.append({
                    "type": "anomaly",
                    "severity": "high" if anomaly_result["reconstruction_error"] > 0.2 else "medium",
                    "confidence": anomaly_result["confidence"]
                })

            results["defects"] = all_defects
            results["total_defects"] = len(all_defects)

            # Generate recommendations
            recommendations = self.recommender.generate_recommendations(results)
            results["maintenance_recommendations"] = recommendations

            logger.info(f"Analysis completed for {image_path}: {len(all_defects)} defects found")
            return results

        except Exception as e:
            logger.error(f"Image analysis failed for {image_path}: {e}")
            return {
                "image_path": image_path,
                "status": "failed",
                "error": str(e),
                "defects": [],
                "total_defects": 0
            }

    async def batch_analyze(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple images in batch."""
        results = []
        for path in image_paths:
            result = await self.analyze_image(path)
            results.append(result)

        return results

    def detect_defects(self, image_data: np.ndarray) -> Dict[str, Any]:
        """Legacy defect detection method."""
        # Convert to PIL Image for processing
        if isinstance(image_data, np.ndarray):
            image = Image.fromarray(image_data)
        else:
            image = image_data

        # Use surface inspector for traditional CV defects
        cv_image = np.array(image)[:, :, ::-1] if hasattr(image, 'convert') else image_data
        surface_results = self.surface_inspector.detect_surface_defects(cv_image)

        return {
            "defects_found": surface_results["total_defects"],
            "types": [d["type"] for d in surface_results["defects"]],
            "severity": max([d.get("severity", "low") for d in surface_results["defects"]], default="none"),
            "detailed_defects": surface_results["defects"]
        }

    def maintenance_recommendation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate maintenance recommendations."""
        return self.recommender.generate_recommendations(analysis_result)


# Legacy functions for backward compatibility
async def analyze_image(image_path: str) -> Dict[str, Any]:
    """Legacy image analysis function."""
    cv_system = ComputerVisionMaintenance()
    return await cv_system.analyze_image(image_path)


def detect_defects(image_data: np.ndarray) -> Dict[str, Any]:
    """Legacy defect detection function."""
    cv_system = ComputerVisionMaintenance()
    return cv_system.detect_defects(image_data)


def maintenance_recommendation(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy maintenance recommendation function."""
    recommender = MaintenanceRecommender()
    return recommender.generate_recommendations(analysis_result)