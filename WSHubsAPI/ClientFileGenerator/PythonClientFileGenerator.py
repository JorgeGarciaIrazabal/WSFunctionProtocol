import inspect
import os
from WSHubsAPI.utils import isNewFunction, getDefaults, getArgs

__author__ = 'jgarc'

class PythonClientFileGenerator():
    FILE_NAME = "WSHubsApi.py"
    TAB = "    "

    @classmethod
    def __getHubClassStr(cls, class_):
        funcStrings = ("\n" + cls.TAB * 2).join(cls.__getFunctionStr(class_))
        return cls.CLASS_TEMPLATE.format(name=class_.__HubName__, functions=funcStrings)

    @classmethod
    def __getFunctionStr(cls, class_):
        funcStrings = []
        functions = inspect.getmembers(class_, predicate=isNewFunction)
        for name, method in functions:
            args = getArgs(method)
            defaults = getDefaults(method)
            formattedArgs = []
            for i, arg in enumerate(reversed(args)):
                if i >= len(defaults):
                    formattedArgs.insert(0, arg)
                else:
                    formattedArgs.insert(0, arg + "=" + str(defaults[-i - 1]))
            appendInArgs = ("\n" + cls.TAB * 4).join([cls.ARGS_COOK_TEMPLATE.format(name=arg) for arg in args])
            funcStrings.append(
                cls.FUNCTION_TEMPLATE.format(name=name, args=", ".join(formattedArgs), cook=appendInArgs))
        return funcStrings

    @classmethod
    def __getAttributesHub(cls, hubs):
        return [cls.ATTRIBUTE_HUB_TEMPLATE.format(name=h.__HubName__) for h in hubs]

    @classmethod
    def createFile(cls, path, hubs):
        if not os.path.exists(path): os.makedirs(path)
        with open(os.path.join(path,"__init__.py"),'w'): #creating __init__.py if not exist
            pass
        with open(os.path.join(path, cls.FILE_NAME), "w") as f:
            classStrings = "".join(cls.__getClassStrings(hubs))
            attributesHubs = "\n".join(cls.__getAttributesHub(hubs))
            f.write(cls.WRAPPER.format(Hubs=classStrings, attributesHubs=attributesHubs))

    @classmethod
    def __getClassStrings(cls, hubs):
        classStrings = []
        for h in hubs:
            classStrings.append(cls.__getHubClassStr(h))
        return classStrings

    WRAPPER = '''import json
import logging
import threading
from ws4py.client.threadedclient import WebSocketClient
from threading import Timer

log = logging.getLogger(__name__)

class WSSimpleObject(object):
    def __setattr__(self, key, value):
        return super(WSSimpleObject, self).__setattr__(key, value)

class WSReturnObject:
    class WSCallbacks:
        def __init__(self, onSuccess=None, onError=None):
            self.onSuccess = onSuccess
            self.onError = onError

    def done(self, onSuccess, onError=None):
        pass


class WSHubsAPIClient(WebSocketClient):
    def __init__(self, api, url, serverTimeout):
        super(WSHubsAPIClient, self).__init__(url)
        self.__returnFunctions = dict()
        self.isOpened = False
        self.serverTimeout = serverTimeout
        self.api = api
        """:type dict of WSReturnObject.WSCallbacks"""

    def opened(self):
        self.isOpened = True
        log.debug("Connection opened")

    def closed(self, code, reason=None):
        log.debug("Connection closed with code:\\n%s\\nAnd reason:\\n%s" % (code, reason))

    def received_message(self, m):
        try:
            msgObj = json.loads(m.data.decode('utf-8'))
            if "replay" in msgObj:
                f = self.__returnFunctions.get(msgObj["ID"], None)
                if f and msgObj["success"]:
                    f.onSuccess(msgObj["replay"])
                elif f and f.onError:
                    f.onError(msgObj["replay"])
            else:
                self.api.__getattribute__(msgObj["hub"]).client.__dict__[msgObj["function"]](*msgObj["args"])
        except Exception as e:
            self.onError(e)

    def getReturnFunction(self, ID):
        """
        :rtype : WSReturnObject
        """

        def returnFunction(onSuccess, onError=None):
            callBacks = self.__returnFunctions.get(ID, WSReturnObject.WSCallbacks())

            def onSuccessWrapper(*args, **kwargs):
                onSuccess(*args, **kwargs)
                self.__returnFunctions.pop(ID, None)

            callBacks.onSuccess = onSuccessWrapper
            if onError is not None:
                def onErrorWrapper(*args, **kwargs):
                    onError(*args, **kwargs)
                    self.__returnFunctions.pop(ID, None)

                callBacks.onError = onErrorWrapper
            else:
                callBacks.onError = None
            self.__returnFunctions[ID] = callBacks
            r = Timer(self.serverTimeout, self.onTimeOut, (ID,))
            r.start()

        retObject = WSReturnObject()
        retObject.done = returnFunction

        # todo create timeout
        return retObject

    def onError(self, exception):
        log.exception("Error in protocol")

    def onTimeOut(self, messageId):
        f = self.__returnFunctions.pop(messageId, None)
        if f and f.onError:
            f.onError("timeOut Error")

class HubsAPI(object):
    def __init__(self, url, serverTimeout=5.0):
        self.wsClient = WSHubsAPIClient(self, url, serverTimeout)
{attributesHubs}

    def connect(self):
        self.wsClient.connect()

{Hubs}

'''

    CLASS_TEMPLATE = '''
    class __{name}(object):
        def __init__(self, wsClient):
            hubName = self.__class__.__name__[2:]
            self.server = self.__server(wsClient, hubName)
            self.client = WSSimpleObject()

        class __server(object):
            __messageID = 0
            __messageLock = threading.RLock()

            def __init__(self, wsClient, hubName):
                """
                :type wsClient: WSHubsAPIClient
                """
                self.wsClient = wsClient
                self.hubName = hubName

            @classmethod
            def __getNextMessageID(cls):
                with cls.__messageLock:
                    cls.__messageID += 1
                    return cls.__messageID

            {functions}
        '''
    FUNCTION_TEMPLATE = '''
            def {name}(self, {args}):
                """
                :rtype : WSReturnObject
                """
                args = list()
                {cook}
                id = self.__getNextMessageID()
                body = {{"hub": self.hubName, "function": "{name}", "args": args, "ID": id}}
                self.wsClient.send(json.dumps(body))
                return self.wsClient.getReturnFunction(id)'''
    ARGS_COOK_TEMPLATE = "args.append({name})"
    ATTRIBUTE_HUB_TEMPLATE = "        self.{name} = self.__{name}(self.wsClient)"
