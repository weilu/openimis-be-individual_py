import os
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from core.test_helpers import create_test_interactive_user


class ViewTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_file_path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'individual_upload.csv'
        )

    def setUp(self):
        self.admin_user = create_test_interactive_user()

    def test_download_template_file(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('download_template_file')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn(
            'attachment; filename="individual_upload_template.csv"',
            response['Content-Disposition']
        )

        expected_base_csv_header = f'first_name,last_name,dob,location_name,id'
        content = b"".join(response.streaming_content).decode('utf-8')
        self.assertTrue(
            expected_base_csv_header in content,
            f'Expect csv template header to contain {expected_base_csv_header}, but got {content}'
        )

    @patch('individual.views.WorkflowService')
    @patch('individual.views.IndividualImportService')
    @patch('individual.views.DefaultStorageFileHandler')
    def test_import_individuals_success(
            self, mock_file_handler, mock_individual_import_service, mock_workflow_service):

        self.client.force_authenticate(user=self.admin_user)

        mock_workflow_service.get_workflows.return_value = {
            'success': True,
            'data': {
                'workflows': [{'id': 1, 'name': 'Test Workflow'}]
            }
        }

        mock_individual_import_service.return_value.import_individuals.return_value = {
            'success': True,
            'message': 'Import successful',
            'details': None
        }

        mock_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_handler_instance

        with open(self.test_file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('import_individuals'),
                data={
                    'file': test_file,
                    'workflow_name': 'Test Workflow',
                    'workflow_group': 'Test Group',
                    'group_aggregation_column': 'group_code'
                },
                format='multipart'
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertIn('message', response.data)

        mock_handler_instance.save_file.assert_called_once()

    @patch('individual.views.WorkflowService')
    @patch('individual.views.IndividualImportService')
    @patch('individual.views.DefaultStorageFileHandler')
    def test_import_individuals_import_service_failure(
            self, mock_file_handler, mock_individual_import_service, mock_workflow_service):

        self.client.force_authenticate(user=self.admin_user)

        mock_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_handler_instance

        mock_individual_import_service.return_value.import_individuals.return_value = {
            'success': False,
            'message': 'Import service not available',
            'details': 'Dummy import service issue'
        }

        mock_workflow_service.get_workflows.return_value = {
            'success': True,
            'data': {
                'workflows': [{'id': 1, 'name': 'Test Workflow'}]
            }
        }

        with open(self.test_file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('import_individuals'),
                data={
                    'file': test_file,
                    'workflow_name': 'Test Workflow',
                    'workflow_group': 'Test Group',
                    'group_aggregation_column': 'group_code'
                },
                format='multipart'
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        mock_handler_instance.save_file.assert_called_once()
        mock_handler_instance.remove_file.assert_called_once()


    @patch('individual.views.WorkflowService')
    @patch('individual.views.DefaultStorageFileHandler')
    def test_import_individuals_workflow_service_failure(
            self, mock_file_handler, mock_workflow_service):

        self.client.force_authenticate(user=self.admin_user)

        mock_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_handler_instance

        mock_workflow_service.get_workflows.return_value = {
            'success': False,
            'message': 'Workflow service not available',
            'details': 'Dummy workflow service issue'
        }

        with open(self.test_file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('import_individuals'),
                data={
                    'file': test_file,
                    'workflow_name': 'Test Workflow',
                    'workflow_group': 'Test Group',
                    'group_aggregation_column': 'group_code'
                },
                format='multipart'
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        mock_handler_instance.save_file.assert_not_called()
        mock_handler_instance.remove_file.assert_not_called()
