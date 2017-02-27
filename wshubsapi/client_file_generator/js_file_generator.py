import inflection

from wshubsapi import utils
from wshubsapi.client_file_generator.client_file_generator import ClientFileGenerator
from wshubsapi.serializer import Serializer

__author__ = 'jgarc'


class JSClientFileGenerator(ClientFileGenerator):
    @classmethod
    def __get_class_strs(cls, hubs_info):
        class_strings = []
        for hub_name, hub_info in hubs_info.items():
            class_strings.append(cls.__get_hub_class_str(hub_name, hub_info))
        return class_strings

    @classmethod
    def __get_hub_class_str(cls, hub_name, hub_info):
        functions_str = dict(serverFunctions=cls.__get_server_functions_str(hub_name, hub_info),
                             clientFunctions=cls.__get_client_functions_str(hub_name, hub_info),
                             bridgeFunctions=cls.__get_bridge_functions_str(hub_name, hub_info))
        return cls.CLASS_TEMPLATE.format(name=hub_name, **functions_str)

    @classmethod
    def __get_functions_parameters(cls, hub_name, methods_info):
        all_parameters = []
        serializer = Serializer()

        for method_name, method_info in methods_info.items():
            defaults = method_info["defaults"]
            for i, default in enumerate(defaults):
                if not isinstance(default, utils.string_class) or not default.startswith("\""):
                    defaults[i] = serializer.serialize(default)
            args = [inflection.camelize(arg, False) for arg in method_info["args"]]
            defaults_array = []
            for i, d in list(enumerate(defaults)):
                arg_pos = len(args) - len(defaults) + i  # argument with the default value
                defaults_array.append(cls.ARGS_COOK_TEMPLATE.format(iter=arg_pos, name=args[arg_pos], default=d))
            defaults_str = "\n\t\t\t".join(defaults_array)
            func_parameters = dict(name=method_name, args=", ".join(args),
                                   cook=defaults_str, hubName=hub_name,
                                   camelCaseName=inflection.camelize(method_name, False))
            all_parameters.append(func_parameters)
        return all_parameters

    @classmethod
    def __get_server_functions_str(cls, hub_name, hub_info):
        all_parameters = cls.__get_functions_parameters(hub_name, hub_info["serverMethods"])
        return ",\n".join([cls.SERVER_FUNCTION_TEMPLATE.format(**params) for params in all_parameters])

    @classmethod
    def __get_client_functions_str(cls, hub_name, hub_info):
        all_parameters = cls.__get_functions_parameters(hub_name, hub_info["clientMethods"])
        return ",\n".join([cls.CLIENT_FUNCTION_TEMPLATE.format(**params) for params in all_parameters])

    @classmethod
    def __get_bridge_functions_str(cls, hub_name, hub_info):
        all_parameters = cls.__get_functions_parameters(hub_name, hub_info["clientMethods"])
        return ",\n".join([cls.BRIDGE_FUNCTIONS_TEMPLATE.format(**params) for params in all_parameters])

    @classmethod
    def create_file(cls, hubs_info, path):
        cls._construct_api_path(path)
        with open(path, "w") as f:
            class_strings = "".join(cls.__get_class_strs(hubs_info))
            f.write(cls.WRAPPER.format(main=class_strings))

    WRAPPER = """'use strict';
/* jshint ignore:start */
/* ignore jslint start */

function __serialize(obj) {{
    return JSON.stringify(__jsonize(obj));
}}

function __jsonize(obj){{
    if(obj instanceof Date){{
        return {{__date_time__: obj.getTime()}}
    }}
    else if(obj instanceof Array){{
        obj.forEach(function (elem, i, list){{
            list[i] = __jsonize(elem);
        }});
    }}
    else if(obj instanceof Object){{
        for(var key in obj) {{
            if(obj.hasOwnProperty(key)){{
                obj[key] = __jsonize(obj[key]);
            }}
        }}
    }}
    return obj;
}}

function __unserialize(objStr) {{
    return __unjsonizer(JSON.parse(objStr));
}}

function __unjsonizer(obj) {{
    if(obj instanceof Object && '__date_time__' in obj) {{
        return new Date(obj.__date_time__);
    }}
    else if(obj instanceof Array){{
        obj.forEach(function (elem, i, list){{
            list[i] = __unjsonizer(elem);
        }});
    }}
    else if(obj instanceof Object){{
        for(var key in obj) {{
            if(obj.hasOwnProperty(key)){{
                obj[key] = __unjsonizer(obj[key]);
            }}
        }}
    }}
    return obj;
}}


function HubsAPI(serverTimeout, wsClientClass, PromiseClass) {{

    var messageID = 0,
        promisesHandler = {{}},
        defaultRespondTimeout = serverTimeout || 5000,
        thisApi = this,
        messagesBeforeOpen = [],
        emptyFunction = function () {{return function () {{}}}}, //redefine any empty function as required
        onOpenTriggers = [];

    PromiseClass = PromiseClass || Promise;
    if (!PromiseClass.prototype.finally) {{
        PromiseClass.prototype.finally = function (callback) {{
            var p = this.constructor;
            return this.then(
                function (value) {{
                    return p.resolve(callback()).then(function () {{
                        return value;
                    }});
                }},
                function (reason) {{
                    return p.resolve(callback()).then(function () {{
                        throw reason;
                    }});
                }});
        }};
    }}

    if (!PromiseClass.prototype.setTimeout) {{
        PromiseClass.prototype.setTimeout = function (timeout) {{
            clearTimeout(this._timeoutID);
            setTimeout(timeoutError(this._reject), timeout);
            return this;
        }};
    }}

    function timeoutError(reject) {{
        return function () {{
            reject(new Error('timeout error'));
        }};
    }}

    function toCamelCase(str) {{
        return str.replace(/_([a-z])/g, function (g) {{ return g[1].toUpperCase(); }});
    }}

    this.clearTriggers = function () {{
        messagesBeforeOpen = [];
        onOpenTriggers = [];
    }};

    this.connect = function (url, reconnectTimeout) {{
        return new PromiseClass(function (resolve, reject) {{
            reconnectTimeout = reconnectTimeout || -1;
            function reconnect(error) {{
                if (reconnectTimeout !== -1) {{
                    window.setTimeout(function () {{
                        thisApi.connect(url, reconnectTimeout);
                        thisApi.onReconnecting(error);
                    }}, reconnectTimeout);
                }}
            }}

            try {{
                thisApi.wsClient = wsClientClass === undefined ? new WebSocket(url) : new wsClientClass(url);
            }} catch (error) {{
                reconnect(error);
                return reject(error);
            }}

            thisApi.wsClient.onopen = function () {{
                resolve();
                thisApi.onOpen(thisApi);
                onOpenTriggers.forEach(function (trigger) {{
                    trigger();
                }});
                messagesBeforeOpen.forEach(function (message) {{
                    thisApi.wsClient.send(message);
                }});
            }};

            thisApi.wsClient.onclose = function (error) {{
                reject(error);
                thisApi.onClose(error);
                reconnect(error);
            }};

            thisApi.wsClient.addOnOpenTrigger = function (trigger) {{
                if (thisApi.wsClient.readyState === 0) {{
                    onOpenTriggers.push(trigger);
                }} else if (thisApi.wsClient.readyState === 1) {{
                    trigger();
                }} else {{
                    throw new Error('web socket is closed');
                }}
            }};

            thisApi.wsClient.onmessage = function (ev) {{
                try {{
                    var promiseHandler,
                        msgObj = __unserialize(ev.data);
                    if (msgObj.hasOwnProperty('reply')) {{
                        promiseHandler = promisesHandler[msgObj.ID];
                        msgObj.success ? promiseHandler.resolve(msgObj.reply) : promiseHandler.reject(msgObj.reply);
                    }} else {{
                        msgObj.function = toCamelCase(msgObj.function);
                        var executor = thisApi[msgObj.hub].client[msgObj.function];
                        if (executor !== undefined) {{
                            var replayMessage = {{ID: msgObj.ID}};
                            try {{
                                replayMessage.reply = executor.apply(executor, msgObj.args);
                                replayMessage.success = true;
                            }} catch (e) {{
                                replayMessage.success = false;
                                replayMessage.reply = e.toString();
                            }} finally {{
                                if (replayMessage.reply instanceof PromiseClass) {{
                                    replayMessage.reply.then(function (result) {{
                                        replayMessage.success = true;
                                        replayMessage.reply = result;
                                        thisApi.wsClient.send(__serialize(replayMessage));
                                    }}, function (error) {{
                                        replayMessage.success = false;
                                        replayMessage.reply = error;
                                        thisApi.wsClient.send(__serialize(replayMessage));
                                    }});
                                }} else {{
                                    replayMessage.reply = replayMessage.reply === undefined ? null : replayMessage.reply;
                                    thisApi.wsClient.send(__serialize(replayMessage));
                                }}
                            }}
                        }} else {{
                            thisApi.onClientFunctionNotFound(msgObj.hub, msgObj.function, msgObj.args);
                        }}
                    }}
                }} catch (err) {{
                    thisApi.wsClient.onMessageError(err);
                }}
            }};

            thisApi.wsClient.onMessageError = function (error) {{
                thisApi.onMessageError(error);
            }};
        }});
    }};

    this.onClose = emptyFunction();
    this.onOpen = emptyFunction();
    this.onReconnecting = emptyFunction();
    this.onMessageError = emptyFunction();
    this.onClientFunctionNotFound = emptyFunction();

    this.defaultErrorHandler = null;

    var constructMessage = function (hubName, functionName, args) {{
        if (thisApi.wsClient === undefined) {{
            throw new Error('ws not connected');
        }}
        var promise,
            timeoutID = null,
            _reject;
        promise = new PromiseClass(function (resolve, reject) {{
            args = Array.prototype.slice.call(args);
            var id = messageID++,
                body = {{'hub': hubName, 'function': functionName, 'args': args, 'ID': id}};
            promisesHandler[id] = {{}};
            promisesHandler[id].resolve = resolve;
            promisesHandler[id].reject = reject;
            timeoutID = setTimeout(timeoutError(reject), defaultRespondTimeout);
            _reject = reject;

            if (thisApi.wsClient.readyState === WebSocket.CONNECTING) {{
                messagesBeforeOpen.push(__serialize(body));
            }} else if (thisApi.wsClient.readyState !== WebSocket.OPEN) {{
                reject('webSocket not connected');
            }} else {{
                thisApi.wsClient.send(__serialize(body));
            }}
        }});
        promise._timeoutID = timeoutID;
        promise._reject = _reject;
        return promise;
    }};
    {main}
}}

if (module && module.exports) {{
  module.exports = HubsAPI;
}}

/* jshint ignore:end */
/* ignore jslint end */
    """
    CLASS_TEMPLATE = """
    this.{name} = {{}};
    this.{name}.server = {{
        __HUB_NAME : '{name}',
        {serverFunctions}
    }};
    this.{name}.client = {{
        __HUB_NAME : '{name}',
        {clientFunctions}
    }};
    this.{name}.getClients = function(clientsIds){{
        return {{
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {{
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('{name}', '_client_to_clients_bridge', bodyArgs);
            }},{bridgeFunctions}
        }}
    }};"""

    SERVER_FUNCTION_TEMPLATE = """
        {camelCaseName} : function ({args}){{
            {cook}
            return constructMessage('{hubName}', '{name}', arguments);
        }}"""

    BRIDGE_FUNCTIONS_TEMPLATE = """
            {camelCaseName} : function ({args}){{
                {cook}
                var funcArgs = Array.prototype.slice.call(arguments);
                var bodyArgs = [this.clientsIds, '{name}', funcArgs];
                return constructMessage('{hubName}', '_client_to_clients_bridge', bodyArgs);
            }}"""

    CLIENT_FUNCTION_TEMPLATE = """
        {camelCaseName} : emptyFunction()"""

    ARGS_COOK_TEMPLATE = "arguments[{iter}] = {name} === undefined ? {default} : {name};"
