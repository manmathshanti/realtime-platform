from django.test import TestCase

from apps.accounts.models import Organization, User, OrganizationMembership, RoleChoices

from .services import DashboardService


class DashboardOverviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='Password123',
            first_name='Owner',
        )
        self.org = Organization.objects.create(name='Acme', slug='acme')
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org,
            role=RoleChoices.OWNER,
        )

    def test_overview_contains_expected_shape(self):
        payload = DashboardService().get_overview(self.org)
        self.assertEqual(payload['organization']['slug'], 'acme')
        self.assertIn('kpis', payload)
        self.assertEqual(payload['kpis']['dashboards'], 0)
