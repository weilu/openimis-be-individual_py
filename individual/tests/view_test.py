from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from core.test_helpers import create_test_interactive_user


class ViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = create_test_interactive_user()

    def test_download_template_file(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('download_template_file')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="individual_upload_template.csv"', response['Content-Disposition'])

        expected_base_csv_header = f'first_name,last_name,dob,location_name,id'
        content = b"".join(response.streaming_content).decode('utf-8')
        self.assertTrue(
            expected_base_csv_header in content,
            f'Expect csv template header to contain {expected_base_csv_header}, but got {content}'
        )
