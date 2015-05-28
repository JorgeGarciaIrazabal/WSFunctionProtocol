import inspect
import logging
import os
from utils import isPublicFunction, getArgs, ASCII_UpperCase, getModulePath
import shutil
from os import listdir
from os.path import isfile

__author__ = 'jgarc'
log = logging.getLogger(__name__)

class JAVAFileGenerator:
    SERVER_FILE_NAME = "WSProtocolServer.java"
    CLIENT_FILE_NAME = "WSClient.java"
    EXTRA_FILES_FOLDER = "JavaExtraFiles"

    @classmethod
    def __getHubClassStr(cls, class_):
        funcStrings = "\n".join(cls.__getJSFunctionsStr(class_))
        return cls.CLASS_TEMPLATE.format(name=class_.__HubName__, functions=funcStrings)

    @classmethod
    def __getJSFunctionsStr(cls, class_):
        funcStrings = []
        functions = inspect.getmembers(class_, predicate=isPublicFunction)
        for name, method in functions:
            args = getArgs(method)
            types = ["TYPE_" + l for l in ASCII_UpperCase[:len(args)]]
            argsTypes = [types[i] + " " + arg for i, arg in enumerate(args)]
            types = "<" + ", ".join(types) + ">" if len(types) > 0 else ""
            toJson = "\n\t\t\t".join([cls.ARGS_COOK_TEMPLATE.format(arg=a) for a in args])
            argsTypes = ", ".join(argsTypes)
            funcStrings.append(cls.FUNCTION_TEMPLATE.format(name=name, args=argsTypes, types=types, cook=toJson))
        return funcStrings


    @classmethod
    def createFile(cls, path, package, hubs):
        with open(os.path.join(path, cls.SERVER_FILE_NAME), "w") as f:
            classStrings = "".join(cls.__getClassStrings(hubs))
            f.write((cls.WRAPPER % package).format(main=classStrings))
        cls.__copyExtraFiles(path)

    @classmethod
    def createClientTemplate(cls, path, package, hubs): #todo: dynamically get client function names
        hubs = "\n".join([cls.CLIENT_HUB_TEMPLATE.format(name=hub.__HubName__) for hub in hubs])
        classString = cls.CLIENT_CLASS_TEMPLATE.format(package=package, hubs=hubs)
        with open(os.path.join(path, cls.CLIENT_FILE_NAME), "w") as f:
            f.write(classString)


    @classmethod
    def __getClassStrings(cls, hubs):
        classStrings = []
        for h in hubs:
            classStrings.append(cls.__getHubClassStr(h))
        return classStrings

    @classmethod
    def __copyExtraFiles(cls, dstPath):
        filesPath = os.path.join(getModulePath(), cls.EXTRA_FILES_FOLDER)
        files = [f for f in listdir(filesPath) if isfile(os.path.join(filesPath, f)) and f.endswith(".java")]
        for f in files:
            if not isfile(os.path.join(dstPath, f)):
                log.info("Created file: %s", os.path.join(dstPath, f))
                shutil.copyfile(os.path.join(filesPath, f), os.path.join(dstPath, f))

    CLASS_TEMPLATE = """
    public static class {name} {{
        public static final String HUB_NAME = "{name}";
        {functions}
    }}"""
    FUNCTION_TEMPLATE = """
        public static {types} FunctionResult {name} ({args}) throws JSONException{{
            JSONArray argsArray = new JSONArray();
            {cook}
            return constructMessage(HUB_NAME, "{name}",argsArray);
        }}"""
    ARGS_COOK_TEMPLATE = "addArg(argsArray,{arg});"

    WRAPPER = """package %s;
import com.google.gson.Gson;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.net.URISyntaxException;

public class WSProtocolServer {{
    private static Gson gson = new Gson();
    private static WSConnection connection;

    public static void init(String uriStr) throws URISyntaxException {{
        connection = new WSConnection(uriStr);
        connection.connect();
    }}
    private static FunctionResult constructMessage (String hubName, String functionName, JSONArray argsArray) throws JSONException{{
        int messageId= connection.getNewMessageId();
        JSONObject msgObj = new JSONObject();
        msgObj.put("hub",hubName);
        msgObj.put("function",functionName);
        msgObj.put("args", argsArray);
        msgObj.put("ID", messageId);
        connection.send(msgObj.toString());
        return new FunctionResult(connection,messageId);
    }}

    private static <TYPE_ARG> void addArg(JSONArray argsArray, TYPE_ARG arg) throws JSONException {{
        try {{
            argsArray.put(arg);
        }} catch (Exception e) {{
            argsArray.put(new JSONObject(gson.toJson(arg)));
        }}
    }}
    {main}
}}
    """

    CLIENT_CLASS_TEMPLATE = """package {package};
public class WSClient {{
    {hubs}
}}"""
    CLIENT_HUB_TEMPLATE = """
    public static class {name} {{
        /*create functions here*/
    }}"""
