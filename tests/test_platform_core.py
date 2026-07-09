import unittest
from src.security.security import check_access, rbac
from src.ai_ml.advanced_analytics import AdvancedAnalytics
import numpy as np

class TestPlatformSecurity(unittest.TestCase):
    def test_rbac_access_granted(self):
        # Admin should have read access
        self.assertTrue(check_access('admin_user', 'read'))
        # Operator should have write access
        self.assertTrue(check_access('op_user', 'write'))

    def test_rbac_access_denied(self):
        # Viewer should NOT have write access
        self.assertFalse(check_access('view_user', 'write'))
        # Unknown user should NOT have any access
        self.assertFalse(check_access('guest', 'read'))

class TestAdvancedAnalytics(unittest.TestCase):
    def setUp(self):
        self.analytics = AdvancedAnalytics()
        # Generate some dummy data: two clusters
        cluster1 = np.random.randn(50, 5) + 2
        cluster2 = np.random.randn(50, 5) - 2
        self.data = np.vstack([cluster1, cluster2])

    def test_pca_transformation(self):
        reduced_data = self.analytics.reduce_dimensions(self.data, n_components=2)
        self.assertEqual(reduced_data.shape, (100, 2))

    def test_clustering(self):
        labels = self.analytics.perform_clustering(self.data, n_clusters=2)
        self.assertEqual(len(labels), 100)
        # Check that we have two unique labels
        self.assertEqual(len(np.unique(labels)), 2)

if __name__ == "__main__":
    unittest.main()
