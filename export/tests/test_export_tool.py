import json
import six

from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase

from export import tools


class MockDjangoObject(models.Model):
    field1 = models.IntegerField()
    field2 = models.IntegerField()


class ToolsTestCase(TestCase):
    """
    Testcase for tools.Export.
    """
    def setUp(self):
        self.export = tools.Export(MockDjangoObject)
        self.obj = MockDjangoObject(field1=1, field2=2)

    def test_serialize(self):
        string_types = [str]
        if six.PY2:
            string_types = [unicode, basestring]
        self.assertRaises(
            TypeError, self.export.serialize, args=['json', object]
        )
        self.assertIn(
            type(self.export.serialize('json', queryset=[])), string_types
        )
        object_list = json.loads(
            self.export.serialize('json', queryset=[self.obj])
        )
        self.assertEqual(object_list[0]['fields']['field1'], self.obj.field1)
        self.assertEqual(object_list[0]['fields']['field2'], self.obj.field2)

        # ensure fields are honored
        object_list = json.loads(
            self.export.serialize(
                'json', queryset=[self.obj], fields=['field1']
            )
        )
        self.assertEqual(object_list[0]['fields']['field1'], self.obj.field1)
        self.assertNotIn('field2', object_list[0]['fields'])

    def test_serialize_formats(self):
        for format in ['csv', 'json', 'python', 'xml']:
            self.assertTrue(self.export.serialize(format, queryset=[self.obj]))

    def test_gen_filename(self):
        self.assertEqual(
            self.export.gen_filename('json'),
            "export-export-mockdjangoobject.json"
        )

    def tearDown(self):
        pass


class ExportFlowTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser("super", "super@user.com", "superuser007")
        cls.another_user = User.objects.create_user("another", "another@user.com", "another007")

    def setUp(self):
        self.client.login(username="super", password="superuser007")

    def test_export_xml(self):
        response = self.client.get("/admin/auth/user/")
        self.assertEquals(response.status_code, 200)
        export_form_data_asc = {
            "export_format": "xml",
            "export_order_by": "username",
            "export_order_direction": "asc"
        }
        export_form_data_dsc = {
            "export_format": "xml",
            "export_order_by": "username",
            "export_order_direction": "dsc"
        }
        response_asc = self.client.post("/object-tools/auth/user/export/", data=export_form_data_asc, follow=True)
        response_dsc = self.client.post("/object-tools/auth/user/export/", data=export_form_data_dsc, follow=True)
        self.assertContains(response_asc, "<?xml")
        self.assertNotEqual(response_asc, response_dsc)

    def test_export_json(self):
        export_form_data_jsn = {
            "export_format": "json",
            "export_order_by": "username",
            "export_order_direction": "asc"
        }
        response = self.client.post("/object-tools/auth/user/export/", data=export_form_data_jsn, follow=True)
        json_content = json.loads(response.content.decode("utf-8"))
        objects = User.objects.all().count()
        self.assertEquals(type(json_content[0]), dict)
        self.assertEquals(json_content[0]["model"], "auth.user")
        self.assertEquals(objects, len(json_content))

    def test_export_csv(self):
        export_form_data_csv = {
            "export_format": "csv",
            "export_order_by": "username",
            "export_order_direction": "asc"
        }
        response = self.client.post("/object-tools/auth/user/export/", data=export_form_data_csv, follow=True)
        self.assertContains(response, "auth.user")
        # Check if True has been serialized to TRUE for 'is_superuser'
        self.assertContains(response, "TRUE")
