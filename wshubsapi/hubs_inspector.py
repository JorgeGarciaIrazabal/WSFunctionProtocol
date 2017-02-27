import glob
import imp
import inspect
import os

from wshubsapi import utils
from wshubsapi.client_file_generator.dart_file_generator import DartClientFileGenerator
from wshubsapi.client_file_generator.js_file_generator import JSClientFileGenerator
from wshubsapi.client_file_generator.python_file_generator import PythonClientFileGenerator
from wshubsapi.hub import Hub
from wshubsapi.utils import is_function_for_ws_client, get_args, get_defaults


class HubsInspectorError(Exception):
    pass


class HubError(Exception):
    pass


class HubsInspector:
    __hubs_constructed = False
    HUBS_DICT = {}
    DEFAULT_JS_API_FILE_NAME = "hubsApi.js"
    DEFAULT_PY_API_FILE_NAME = "hubs_api.py"
    DEFAULT_DART_API_FILE_NAME = "hubs_api.dart"

    def __init__(self):
        raise HubsInspectorError("Static class, do not create an instance of HubsInspector")

    @classmethod
    def _handle_hub_construction_error(cls, e, hub_class):
        if "__init__()" in str(e):
            constructor_with_params_text = "Hubs can't have a constructor with parameters. Check Hub: %s"
            raise HubsInspectorError(constructor_with_params_text % hub_class.__name__)
        else:
            raise e

    @classmethod
    def _construct_hub(cls, hub_class):
        try:
            hub = hub_class()
            hub_name = hub.__class__.__HubName__
            if hub_name in cls.HUBS_DICT:
                raise HubError("Hub's name must be unique, found duplicated name with: {}".format(hub_name))
            if hub_name.startswith("__"):
                raise HubError("Hub's name can not start with '__'")
            if hub_name == "ws_client":
                raise HubError("Hub's name can not be 'wsClient', it is a  reserved name")
            cls.HUBS_DICT[hub_name] = hub
        except TypeError as e:
            cls._handle_hub_construction_error(e, hub_class)

    @classmethod
    def _ignore_hub_implementation(cls, hub_class):
        return "__HubName__" in hub_class.__dict__ and hub_class.__HubName__ is None

    @classmethod
    def get_all_hubs_subclasses(cls, hub_class_to_inspect, current_hub_classes=None):
        current_hub_classes = current_hub_classes if current_hub_classes is not None else []
        for hub_class in hub_class_to_inspect.__subclasses__():
            if not cls._ignore_hub_implementation(hub_class):
                current_hub_classes.append(hub_class)
            else:
                cls.get_all_hubs_subclasses(hub_class, current_hub_classes)
        return current_hub_classes

    @classmethod
    def inspect_implemented_hubs(cls, force_reconstruction=False):
        if not cls.__hubs_constructed or force_reconstruction:
            cls.HUBS_DICT.clear()
            for hub_class in cls.get_all_hubs_subclasses(Hub):
                cls._construct_hub(hub_class)

            cls.__hubs_constructed = True

    @classmethod
    def construct_js_file(cls, path=DEFAULT_JS_API_FILE_NAME):
        cls.inspect_implemented_hubs()
        JSClientFileGenerator.create_file(cls.get_hubs_information(), path)

    @classmethod
    def construct_java_file(cls, package, path="."):
        raise NotImplementedError("coming in new versions")
        # cls.inspect_implemented_hubs()
        # hubs = cls.HUBS_DICT.values()
        # JAVAFileGenerator.create_file(path, package, hubs)
        # JAVAFileGenerator.create_client_template(path, package, hubs)

    @classmethod
    def construct_python_file(cls, path=DEFAULT_PY_API_FILE_NAME):
        cls.inspect_implemented_hubs()
        PythonClientFileGenerator.create_file(cls.get_hubs_information(), path)

    @classmethod
    def construct_dart_file(cls, path=DEFAULT_DART_API_FILE_NAME):
        cls.inspect_implemented_hubs()
        DartClientFileGenerator.create_file(cls.get_hubs_information(), path)

    @classmethod
    def construct_cpp_file(cls, path="."):
        raise NotImplementedError("coming in new versions")
        # cls.inspect_implemented_hubs()
        # CppFileGenerator.create_file(path, cls.get_hubs_information())

    @classmethod
    def get_hub_instance(cls, hub):
        """
        :rtype: Hub
        """
        if not isinstance(hub, utils.string_class):
            hub = hub.__HubName__
        return cls.HUBS_DICT[hub]

    @classmethod
    def get_hubs_information(cls):
        info_report = {}
        hubs = cls.HUBS_DICT.values()
        for hub in hubs:
            functions = inspect.getmembers(hub, predicate=is_function_for_ws_client)
            server_methods = {}
            for name, method in functions:
                # filtering functions to ignore
                if inspect.getdoc(method) is not None and "HUBS_API_IGNORE" in inspect.getdoc(method):
                    continue
                args_dict = dict(args=get_args(method), defaults=get_defaults(method))
                server_methods[name] = args_dict
            client_methods = {}
            for name, method in hub.client_functions.items():
                args_dict = dict(args=get_args(method), defaults=get_defaults(method))
                client_methods[name] = args_dict

            info_report[hub.__HubName__] = dict(serverMethods=server_methods, clientMethods=client_methods)
        return info_report

    @classmethod
    def include_hubs_in(cls, paths):
        if paths not in (tuple, list, set):
            paths = [paths]
        for i, path in enumerate(paths):
            paths[i] = os.path.join(path, '*.py') if os.path.isdir(path) else path

        paths = list(paths)
        python_files = set()
        for path in paths:
            python_files |= set([f for f in glob.glob(path) if f.endswith(".py")])

        for python_file in python_files:
            module_name, _ = os.path.splitext(os.path.split(python_file)[-1])
            imp.load_source(module_name, python_file)




