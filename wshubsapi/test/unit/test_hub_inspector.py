import os
import unittest

from wshubsapi.hub import Hub
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.hubs_inspector import HubsInspectorError, HubError
from wshubsapi.test.utils import path_utils
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses

# do not remove this
from wshubsapi.utils_api_hub import UtilsAPIHub


class TestHubInspector(unittest.TestCase):
    def setUp(self):
        # Building hubs for testing
        class TestHub(Hub):
            def get_data(self):
                pass

        class TestHub2(Hub):
            pass

        self.resources_path = path_utils.get_resources_path("hubs_inspector")
        self.testHubClass = TestHub
        self.testHub2Class = TestHub2
        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

    def tearDown(self):
        del self.testHubClass
        del self.testHub2Class
        remove_hubs_subclasses()

    def test_constructor_should_raise_exception(self):
        def create_instance():
            return HubsInspector()

        self.assertRaises(HubsInspectorError, create_instance)

    def test_hubs_inspection(self):
        self.assertEqual(len(HubsInspector.HUBS_DICT), 3, 'Detects all Hubs')
        self.assertTrue(issubclass(HubsInspector.HUBS_DICT['TestHub'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(issubclass(HubsInspector.HUBS_DICT['TestHub2'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(getattr(HubsInspector.HUBS_DICT['TestHub'], "get_data"), 'Detects function')

    def test_hubs_limitations(self):
        class TestHubLimitation(Hub):
            pass

        class TestHubLimitation2(Hub):
            __HubName__ = "TestHubLimitation"

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)
        TestHubLimitation2.__HubName__ = "TestHubLimitation2"

        class TestHubLimitation3(Hub):
            def __init__(self, aux):
                super(TestHubLimitation3, self).__init__()

        self.assertRaises(HubsInspectorError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)
        TestHubLimitation3.__init__ = lambda: 1 + 1

    def test_hubs_limitations_starts_with_underscores(self):
        class __TestHubLimitation(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)

    def test_hubs_limitations_cant_be_named_ws_client(self):
        class ws_client(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)

    def test_HubCreation_insertsInstanceInHUBs_DICT(self):
        class TestHub1(Hub):
            pass

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        self.assertTrue(HubsInspector.get_hub_instance(TestHub1) in HubsInspector.HUBS_DICT.values())

    def test_hub_creation_inserts_new__HubName__in_HUBS_DICT(self):
        class TestHub1(Hub):
            __HubName__ = "newValue"
            pass

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        self.assertIn("newValue", HubsInspector.HUBS_DICT.keys())

    def test_HubCreation_RaisesExceptionIfClassNameStartsWith__(self):
        class __TestHub1(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, True)

    def test_HubCreation_RaisesExceptionIfClassNameIsWsClient(self):
        class ws_client(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, True)

    def test_getHubInstance_returnsAnInstanceOfHubIfExists(self):
        self.assertIsInstance(HubsInspector.get_hub_instance(self.testHubClass), Hub)

    def test_getHubInstance_RaisesErrorIfNotAHub(self):
        self.assertRaises(AttributeError, HubsInspector.get_hub_instance, (str,))

    def test_getHubsInformation_ReturnsDictionaryWithNoClientFunctions(self):
        hubs_info = HubsInspector.get_hubs_information()

        self.assertIn("TestHub2", hubs_info)
        self.assertIn("get_data", hubs_info["TestHub"]["serverMethods"])

    def test_getHubsInformation_ReturnsDictionaryWithClientFunctions(self):
        class TestHubWithClient(Hub):
            def get_data(self):
                pass

            def _define_client_functions(self):
                return dict(client1=lambda x, y: None,
                            client2=lambda x, y=1: None,
                            client3=lambda x=0, y=1: None)

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        info_report = HubsInspector.get_hubs_information()

        self.assertIn("TestHubWithClient", info_report)
        client1method = info_report["TestHubWithClient"]["clientMethods"]["client1"]
        client2method = info_report["TestHubWithClient"]["clientMethods"]["client2"]
        client3method = info_report["TestHubWithClient"]["clientMethods"]["client3"]
        self.assertEqual(client1method["args"], ["x", "y"])
        self.assertEqual(client2method["defaults"], [1])
        self.assertEqual(client3method["defaults"], [0, 1])

    def test_include_hubs_in_withOneModule(self):
        hubs_info = HubsInspector.get_hubs_information()
        self.assertNotIn("SubHub", hubs_info)

        HubsInspector.include_hubs_in(self.resources_path + os.sep + "one_module/*.py")
        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        hubs_info = HubsInspector.get_hubs_information()
        self.assertIn("SubHub", hubs_info)

    def test_include_hubs_in_withMultipleModules(self):
        hubs_info = HubsInspector.get_hubs_information()
        self.assertNotIn("SubHub2", hubs_info)

        HubsInspector.include_hubs_in(self.resources_path + os.sep + "multiple_module/*.py")
        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        hubs_info = HubsInspector.get_hubs_information()
        self.assertIn("SubHub2", hubs_info)
        self.assertIn("SubHub3", hubs_info)

    def test_include_hubs_in_addsModulesIfPathIncluded(self):
        hubs_info = HubsInspector.get_hubs_information()
        self.assertNotIn("InPath1", hubs_info)
        self.assertNotIn("InPath2", hubs_info)

        HubsInspector.include_hubs_in(self.resources_path + os.sep + "in_path")
        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        hubs_info = HubsInspector.get_hubs_information()
        self.assertIn("InPath1", hubs_info)
        self.assertIn("InPath2", hubs_info)
