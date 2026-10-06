from django.test import TestCase
from .models import Entreprise


class EntrepriseQuotaTests(TestCase):
    def test_undefined_palier_has_no_quotas(self):
        entreprise = Entreprise(palier='pas_defini')

        self.assertEqual(entreprise.quota_livreurs, 0)
        self.assertEqual(entreprise.quota_admins, 0)

    def test_unknown_palier_has_no_quotas(self):
        entreprise = Entreprise(palier='inconnu')

        self.assertEqual(entreprise.quota_livreurs, 0)
        self.assertEqual(entreprise.quota_admins, 0)

    def test_defined_palier_keeps_its_quotas(self):
        entreprise = Entreprise(palier='pro')

        self.assertEqual(entreprise.quota_livreurs, 20)
        self.assertEqual(entreprise.quota_admins, 3)
