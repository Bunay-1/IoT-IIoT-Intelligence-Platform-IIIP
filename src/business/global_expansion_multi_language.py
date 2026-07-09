"""
Global Expansion and Multi-Language Support Module

This module provides comprehensive support for global expansion of the IoT IIoT Intelligence Platform,
including multi-language interfaces, regional compliance, cultural adaptation, and localization features.

Features:
- Multi-language user interface support
- Regional regulatory compliance
- Cultural adaptation for different markets
- Currency and localization handling
- International partnership management
- Cross-border data compliance
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import locale
import babel
from babel import Locale
import pycountry

class MultiLanguageManager:
    """
    Manages multi-language support for the platform.
    """

    def __init__(self, default_language: str = 'en'):
        self.default_language = default_language
        self.supported_languages = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어',
            'ar': 'العربية',
            'hi': 'हिन्दी'
        }

        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        """
        Load translation files for supported languages.
        """
        # In production, this would load from JSON/YAML files
        # For demo, we'll define some key translations
        self.translations = {
            'dashboard': {
                'en': 'Dashboard',
                'es': 'Panel de Control',
                'fr': 'Tableau de Bord',
                'de': 'Dashboard',
                'it': 'Pannello di Controllo',
                'pt': 'Painel de Controle',
                'ru': 'Панель Управления',
                'zh': '仪表板',
                'ja': 'ダッシュボード',
                'ko': '대시보드',
                'ar': 'لوحة التحكم',
                'hi': 'डैशबोर्ड'
            },
            'alerts': {
                'en': 'Alerts',
                'es': 'Alertas',
                'fr': 'Alertes',
                'de': 'Warnungen',
                'it': 'Avvisi',
                'pt': 'Alertas',
                'ru': 'Оповещения',
                'zh': '警报',
                'ja': 'アラート',
                'ko': '알림',
                'ar': 'تنبيهات',
                'hi': 'अलर्ट'
            },
            'analytics': {
                'en': 'Analytics',
                'es': 'Análisis',
                'fr': 'Analyses',
                'de': 'Analysen',
                'it': 'Analisi',
                'pt': 'Análises',
                'ru': 'Аналитика',
                'zh': '分析',
                'ja': '分析',
                'ko': '분석',
                'ar': 'تحليلات',
                'hi': 'एनालिटिक्स'
            }
        }

    def translate(self, key: str, language: str) -> str:
        """
        Translate a text key to the specified language.

        Args:
            key: Translation key
            language: Target language code

        Returns:
            str: Translated text
        """
        if key in self.translations and language in self.translations[key]:
            return self.translations[key][language]

        # Fallback to default language
        if key in self.translations and self.default_language in self.translations[key]:
            return self.translations[key][self.default_language]

        # Final fallback to key itself
        return key

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages.

        Returns:
            Dict[str, str]: Language code -> Language name mapping
        """
        return self.supported_languages.copy()

    def detect_user_language(self, user_info: Dict[str, Any]) -> str:
        """
        Detect appropriate language for user based on their information.

        Args:
            user_info: User information (location, preferences, etc.)

        Returns:
            str: Detected language code
        """
        # Check explicit preference
        if 'preferred_language' in user_info:
            lang = user_info['preferred_language']
            if lang in self.supported_languages:
                return lang

        # Check browser language
        if 'browser_language' in user_info:
            browser_lang = user_info['browser_language'].split('-')[0]
            if browser_lang in self.supported_languages:
                return browser_lang

        # Check location-based language
        if 'country' in user_info:
            country_langs = self._get_country_languages(user_info['country'])
            for lang in country_langs:
                if lang in self.supported_languages:
                    return lang

        # Default fallback
        return self.default_language

    def _get_country_languages(self, country_code: str) -> List[str]:
        """
        Get official languages for a country.

        Args:
            country_code: ISO country code

        Returns:
            List[str]: List of language codes
        """
        country_language_map = {
            'US': ['en'],
            'GB': ['en'],
            'ES': ['es'],
            'FR': ['fr'],
            'DE': ['de'],
            'IT': ['it'],
            'PT': ['pt'],
            'BR': ['pt'],
            'RU': ['ru'],
            'CN': ['zh'],
            'JP': ['ja'],
            'KR': ['ko'],
            'SA': ['ar'],
            'AE': ['ar'],
            'IN': ['hi', 'en']
        }

        return country_language_map.get(country_code.upper(), ['en'])

    def format_localized_number(self, number: float, language: str) -> str:
        """
        Format number according to locale conventions.

        Args:
            number: Number to format
            language: Language code

        Returns:
            str: Localized number string
        """
        try:
            locale_code = self._language_to_locale(language)
            return babel.numbers.format_number(number, locale=locale_code)
        except:
            return str(number)

    def format_localized_currency(self, amount: float, currency: str, language: str) -> str:
        """
        Format currency according to locale conventions.

        Args:
            amount: Amount to format
            currency: Currency code (USD, EUR, etc.)
            language: Language code

        Returns:
            str: Localized currency string
        """
        try:
            locale_code = self._language_to_locale(language)
            return babel.numbers.format_currency(amount, currency, locale=locale_code)
        except:
            return f"{currency} {amount}"

    def format_localized_date(self, date: datetime, language: str) -> str:
        """
        Format date according to locale conventions.

        Args:
            date: Date to format
            language: Language code

        Returns:
            str: Localized date string
        """
        try:
            locale_code = self._language_to_locale(language)
            return babel.dates.format_date(date, locale=locale_code)
        except:
            return date.strftime('%Y-%m-%d')

    def _language_to_locale(self, language: str) -> str:
        """
        Convert language code to locale code.

        Args:
            language: Language code

        Returns:
            str: Locale code
        """
        locale_map = {
            'en': 'en_US',
            'es': 'es_ES',
            'fr': 'fr_FR',
            'de': 'de_DE',
            'it': 'it_IT',
            'pt': 'pt_PT',
            'ru': 'ru_RU',
            'zh': 'zh_CN',
            'ja': 'ja_JP',
            'ko': 'ko_KR',
            'ar': 'ar_SA',
            'hi': 'hi_IN'
        }

        return locale_map.get(language, 'en_US')

class RegionalComplianceManager:
    """
    Manages regional regulatory compliance.
    """

    def __init__(self):
        self.regulations = {
            'GDPR': {
                'regions': ['EU'],
                'requirements': ['data_protection', 'consent_management', 'right_to_be_forgotten'],
                'fines': 'up to 4% of global revenue'
            },
            'CCPA': {
                'regions': ['US-CA'],
                'requirements': ['data_rights', 'opt_out', 'privacy_notices'],
                'fines': 'up to $7500 per violation'
            },
            'PDPA': {
                'regions': ['SG'],
                'requirements': ['data_protection', 'consent', 'data_breach_notification'],
                'fines': 'up to SGD 1M'
            },
            'LGPD': {
                'regions': ['BR'],
                'requirements': ['data_protection', 'consent', 'data_subject_rights'],
                'fines': 'up to 2% of revenue'
            },
            'PIPL': {
                'regions': ['CN'],
                'requirements': ['data_localization', 'security_assessment', 'personal_info_protection'],
                'fines': 'up to 5% of revenue'
            }
        }

    def check_compliance(self, operation: str, region: str, data_types: List[str]) -> Dict[str, Any]:
        """
        Check compliance requirements for an operation in a specific region.

        Args:
            operation: Type of operation (data_processing, storage, transfer)
            region: Region code (EU, US-CA, etc.)
            data_types: Types of data involved

        Returns:
            Dict[str, Any]: Compliance check results
        """
        applicable_regulations = []
        requirements = []
        risks = []

        for reg_name, reg_info in self.regulations.items():
            if any(r in region.upper() for r in reg_info['regions']):
                applicable_regulations.append(reg_name)

                # Check specific requirements
                reg_requirements = reg_info['requirements']
                requirements.extend(reg_requirements)

                # Assess risks
                if 'personal' in data_types or 'sensitive' in data_types:
                    if 'data_protection' in reg_requirements:
                        risks.append(f"High risk under {reg_name} - personal data protection required")

        compliance_status = "compliant" if len(risks) == 0 else "requires_attention"

        return {
            'compliance_status': compliance_status,
            'applicable_regulations': applicable_regulations,
            'requirements': list(set(requirements)),
            'risks': risks,
            'recommendations': self._generate_compliance_recommendations(requirements, risks)
        }

    def _generate_compliance_recommendations(self, requirements: List[str], risks: List[str]) -> List[str]:
        """
        Generate compliance recommendations.
        """
        recommendations = []

        if 'data_protection' in requirements:
            recommendations.append("Implement comprehensive data protection measures")
            recommendations.append("Conduct regular data protection impact assessments")

        if 'consent_management' in requirements:
            recommendations.append("Implement granular consent management system")
            recommendations.append("Provide clear privacy notices in local languages")

        if 'data_localization' in requirements:
            recommendations.append("Ensure data residency requirements are met")
            recommendations.append("Implement data localization controls")

        if risks:
            recommendations.append("Consult with local legal experts for compliance")
            recommendations.append("Establish compliance monitoring and reporting")

        return recommendations

class CulturalAdaptationManager:
    """
    Manages cultural adaptation for different markets.
    """

    def __init__(self):
        self.cultural_dimensions = {
            'US': {'individualism': 0.91, 'power_distance': 0.40, 'uncertainty_avoidance': 0.46},
            'JP': {'individualism': 0.46, 'power_distance': 0.54, 'uncertainty_avoidance': 0.92},
            'DE': {'individualism': 0.67, 'power_distance': 0.35, 'uncertainty_avoidance': 0.65},
            'BR': {'individualism': 0.38, 'power_distance': 0.69, 'uncertainty_avoidance': 0.76},
            'CN': {'individualism': 0.20, 'power_distance': 0.80, 'uncertainty_avoidance': 0.30},
            'IN': {'individualism': 0.48, 'power_distance': 0.77, 'uncertainty_avoidance': 0.40}
        }

    def adapt_interface(self, base_interface: Dict[str, Any], target_country: str) -> Dict[str, Any]:
        """
        Adapt user interface for specific cultural context.

        Args:
            base_interface: Base interface configuration
            target_country: Target country code

        Returns:
            Dict[str, Any]: Culturally adapted interface
        """
        adapted = base_interface.copy()

        if target_country.upper() in self.cultural_dimensions:
            dimensions = self.cultural_dimensions[target_country.upper()]

            # Adapt based on cultural dimensions
            if dimensions['power_distance'] > 0.5:
                # High power distance - more formal language, hierarchical displays
                adapted['communication_style'] = 'formal'
                adapted['hierarchy_display'] = 'prominent'
            else:
                # Low power distance - casual language, egalitarian displays
                adapted['communication_style'] = 'casual'
                adapted['hierarchy_display'] = 'minimal'

            if dimensions['individualism'] < 0.5:
                # Collectivist culture - emphasize group benefits, team features
                adapted['focus'] = 'group_benefits'
                adapted['collaboration_features'] = 'enhanced'
            else:
                # Individualist culture - emphasize personal achievement, individual features
                adapted['focus'] = 'personal_achievement'
                adapted['individual_features'] = 'enhanced'

            if dimensions['uncertainty_avoidance'] > 0.5:
                # High uncertainty avoidance - detailed instructions, risk warnings
                adapted['instructions'] = 'detailed'
                adapted['risk_communication'] = 'prominent'
            else:
                # Low uncertainty avoidance - concise instructions, minimal warnings
                adapted['instructions'] = 'concise'
                adapted['risk_communication'] = 'minimal'

        return adapted

    def adapt_business_practices(self, base_practices: Dict[str, Any], target_country: str) -> Dict[str, Any]:
        """
        Adapt business practices for specific cultural context.

        Args:
            base_practices: Base business practices
            target_country: Target country code

        Returns:
            Dict[str, Any]: Culturally adapted business practices
        """
        adapted = base_practices.copy()

        # Add country-specific adaptations
        if target_country.upper() == 'JP':
            adapted['negotiation_style'] = 'indirect'
            adapted['decision_making'] = 'consensus_based'
            adapted['relationship_building'] = 'long_term'
        elif target_country.upper() == 'BR':
            adapted['communication_style'] = 'expressive'
            adapted['time_orientation'] = 'flexible'
            adapted['relationship_building'] = 'personal'
        elif target_country.upper() == 'DE':
            adapted['communication_style'] = 'direct'
            adapted['planning_horizon'] = 'long_term'
            adapted['quality_focus'] = 'high'

        return adapted

class GlobalExpansionManager:
    """
    Comprehensive global expansion management system.
    """

    def __init__(self):
        self.language_manager = MultiLanguageManager()
        self.compliance_manager = RegionalComplianceManager()
        self.cultural_manager = CulturalAdaptationManager()
        self.market_entries = {}

    def prepare_market_entry(self, country_code: str, business_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare comprehensive market entry strategy for a country.

        Args:
            country_code: Target country code
            business_model: Base business model configuration

        Returns:
            Dict[str, Any]: Market entry preparation
        """
        # Language and localization
        primary_language = self.language_manager._get_country_languages(country_code)[0]
        localization = {
            'primary_language': primary_language,
            'supported_languages': self.language_manager._get_country_languages(country_code),
            'currency': self._get_country_currency(country_code),
            'date_format': self.language_manager.format_localized_date(datetime.now(), primary_language),
            'number_format': self.language_manager.format_localized_number(1234.56, primary_language)
        }

        # Compliance requirements
        compliance = self.compliance_manager.check_compliance(
            'data_processing', country_code, ['personal', 'operational']
        )

        # Cultural adaptation
        adapted_interface = self.cultural_manager.adapt_interface(
            {'theme': 'default', 'layout': 'standard'}, country_code
        )
        adapted_practices = self.cultural_manager.adapt_business_practices(
            business_model, country_code
        )

        # Market assessment
        market_assessment = self._assess_market_potential(country_code)

        # Entry strategy
        entry_strategy = {
            'localization': localization,
            'compliance': compliance,
            'cultural_adaptation': {
                'interface': adapted_interface,
                'business_practices': adapted_practices
            },
            'market_assessment': market_assessment,
            'implementation_priority': self._calculate_entry_priority(compliance, market_assessment),
            'risk_assessment': self._assess_entry_risks(compliance, market_assessment)
        }

        # Store market entry
        self.market_entries[country_code] = {
            'entry_date': datetime.utcnow(),
            'strategy': entry_strategy,
            'status': 'planned'
        }

        return entry_strategy

    def _get_country_currency(self, country_code: str) -> str:
        """
        Get primary currency for a country.
        """
        currency_map = {
            'US': 'USD',
            'GB': 'GBP',
            'EU': 'EUR',  # For EU countries
            'JP': 'JPY',
            'CN': 'CNY',
            'IN': 'INR',
            'BR': 'BRL',
            'RU': 'RUB',
            'KR': 'KRW',
            'SA': 'SAR',
            'AE': 'AED'
        }

        # Default mappings for common countries
        if country_code.upper() in ['DE', 'FR', 'IT', 'ES', 'NL']:
            return 'EUR'
        elif country_code.upper() in currency_map:
            return currency_map[country_code.upper()]

        return 'USD'  # Default

    def _assess_market_potential(self, country_code: str) -> Dict[str, Any]:
        """
        Assess market potential for IoT/IIoT solutions.
        """
        # Mock market assessment - in production, use real market data
        base_assessment = {
            'market_size': 'medium',
            'growth_rate': 0.15,
            'competition_level': 'medium',
            'regulatory_environment': 'moderate',
            'infrastructure_readiness': 'good'
        }

        # Country-specific adjustments
        if country_code.upper() in ['US', 'DE', 'JP']:
            base_assessment.update({
                'market_size': 'large',
                'infrastructure_readiness': 'excellent'
            })
        elif country_code.upper() in ['CN', 'IN']:
            base_assessment.update({
                'market_size': 'large',
                'growth_rate': 0.25,
                'competition_level': 'high'
            })

        return base_assessment

    def _calculate_entry_priority(self, compliance: Dict, market: Dict) -> str:
        """
        Calculate market entry priority.
        """
        compliance_score = 1 if compliance['compliance_status'] == 'compliant' else 0.5
        market_score = 1 if market['market_size'] == 'large' else 0.7 if market['market_size'] == 'medium' else 0.3

        overall_score = (compliance_score + market_score) / 2

        if overall_score > 0.8:
            return "high"
        elif overall_score > 0.6:
            return "medium"
        else:
            return "low"

    def _assess_entry_risks(self, compliance: Dict, market: Dict) -> List[str]:
        """
        Assess risks for market entry.
        """
        risks = []

        if compliance['compliance_status'] != 'compliant':
            risks.append("Regulatory compliance challenges")

        if market['competition_level'] == 'high':
            risks.append("Intense market competition")

        if market['regulatory_environment'] == 'strict':
            risks.append("Complex regulatory landscape")

        if market['infrastructure_readiness'] == 'poor':
            risks.append("Infrastructure limitations")

        return risks

# Example usage
if __name__ == "__main__":
    global_manager = GlobalExpansionManager()

    # Prepare market entry for Germany
    germany_entry = global_manager.prepare_market_entry('DE', {
        'pricing_model': 'subscription',
        'target_segments': ['manufacturing', 'automotive'],
        'partnership_strategy': 'local_distributors'
    })

    print("Germany Market Entry Strategy:")
    print(f"Primary Language: {germany_entry['localization']['primary_language']}")
    print(f"Currency: {germany_entry['localization']['currency']}")
    print(f"Compliance Status: {germany_entry['compliance']['compliance_status']}")
    print(f"Entry Priority: {germany_entry['implementation_priority']}")
    print(f"Market Size: {germany_entry['market_assessment']['market_size']}")

    # Test language translation
    translated = global_manager.language_manager.translate('dashboard', 'de')
    print(f"'Dashboard' in German: {translated}")

    # Test number formatting
    formatted = global_manager.language_manager.format_localized_number(1234.56, 'de')
    print(f"Number in German format: {formatted}")

    # Test currency formatting
    currency_formatted = global_manager.language_manager.format_localized_currency(1234.56, 'EUR', 'de')
    print(f"Currency in German format: {currency_formatted}")