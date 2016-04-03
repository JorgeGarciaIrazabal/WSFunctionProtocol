WSHubsAPI
================================================

The ``wshubsapi`` package/module allows an intuitive communication between back-end (Python) and front-end (Python, JS, JAVA or Android) applications through the webSocket protocol.

Installation
-----------------
```bash
pip install wshubsapi
```

Examples of usage
-----------------
Bellow you can find an example of how easy is to create a chat room with this library.

Server side
-----------------
In this example we will use the WS4Py library and the ws4py clientHandler for the webssocket connections.

```python
from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.ConnectionHandlers.WS4Py import ConnectionHandler
from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from wshubsapi.Hub import Hub
from ws4py.server.wsgiutils import WebSocketWSGIApplication


if __name__ == '__main__':
    class ChatHub(Hub):
        def sendToAll(self, name, message):
            allConnectedClients = self._getClientsHolder().getAllClients()
            #onMessage function has to be defined in the client side
            allConnectedClients.onMessage(name, message)
            return "Sent to %d clients" % len(allConnectedClients)
    HubsInspector.inspectImplementedHubs() #setup api
    HubsInspector.constructPythonFile("_static") #only if you will use a python client
    HubsInspector.constructJSFile("_static") #only if you will use a js client
    server = make_server('127.0.0.1', 8888, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=ConnectionHandler))
    server.initialize_websockets_manager()
    server.serve_forever()
```
    
Client side JS client
-----------------
works like:

```javascript
<!DOCTYPE html>
<html>
<head>
    <title>tornado WebSocket example</title>
    <!--File auto-generated by the server.
    Path needs to match with Hub.constructJSFile path parameter-->
    <script type="text/javascript" src="_static/WSHubsApi.js"></script>
    <script type="text/javascript" src="http://code.jquery.com/jquery-1.4.2.js"></script>
</head>
<body>
<div class="container">
    <h1>tornado WebSocket example with WSHubsAPI</h1>
    <hr>
    WebSocket status : <span id="status">Waiting connection</span><br>
    Name: <input type="text" id="name" value="Kevin"/><br>
    <input type="text" id="message" />
    <input type="button" id="sendmessage" value="Send" />
    <input type="hidden" id="displayname" />
    <ul id="discussion">
    </ul>
</div>
    <script>
    var hubsApi = new HubsAPI('ws://127.0.0.1:8888/');
        function sendToAll() {
            var name = $('#name').val(),
                message = $('#message').val();
            $('#discussion').append('<li><strong> Me'
                + '</strong>: ' + message + '</li>');


            hubsApi.ChatHub.server.sendToAll(name, message)
                .then(function (numOfMessagesSent) {
                    console.log("message sent to " + numOfMessagesSent + " client(s)");
                }, function (err) {
                    console.log("message not sent " + err);
                }).finally(function () {
                    console.log("I am in finnally");
                });
            $('#message').val('').focus();
        }

        hubsApi.connect().then(function () {
            $('#status').text("Connected")

            //function to be called from server
            hubsApi.ChatHub.client.onMessage = function (from, message) {
                $('#discussion').append('<li><strong>' + from
                    + '</strong>: ' + message + '</li>');
                return "received"
            }

            //sending message
            $('#sendmessage').click(sendToAll);
            $('#message').keypress(function (e) {
                if (e.which == 13)
                    sendToAll()
            });
        }, function (error) {
            console.error(error);
        });

        hubsApi.wsClient.onerror = function (ev) {
            console.error(ev.reason);
        };
</script>
</body>
</html>
```

Client side Python client
-----------------
change raw_input for input for python 3.*
```python
import json
import logging
import logging.config
import sys

logging.config.dictConfig(json.load(open('logging.json')))
if sys.version_info[0] == 2:
    input = raw_input

# file created by the server
from _static.WSHubsApi import HubsAPI


if __name__ == '__main__':
    ws = HubsAPI('ws://127.0.0.1:8888/')
    ws.connect()
    ws.defaultOnError = lambda m: sys.stdout.write("message could not be sent!!!!! {}\n".format(m))
    ws.UtilsAPIHub.server.setId("testing")
    
    def printMessage(senderName, message):
        print(u"From {0}: {1}".format(senderName, message))
        
    ws.ChatHub.client.onMessage = printMessage
    ws.ChatHub.server.subscribeToHub().done(lambda x: ws.ChatHub.server.getSubscribedClientsToHub())
    name = input("Enter your name:")
    print("Hello %s. You have entered in the chat room, write and press enter to send message" % name)
    while True:
        message = input("")
        if sys.version_info[0] == 2:
            message = message.decode(sys.stdin.encoding)
        ws.ChatHub.server.sendToAll(name, message).done(lambda m: sys.stdout.write("message sent to {} client(s)\n".format(m)))
                                                       
```

Client side JAVA/Android client
-----------------

Not a beta version yet, working on it! ;)

Enabling logging
-----------------

To view and log any message from and to the server, user the logging package

```python
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
```
Contact
-------

The latest version of ``WSHubsAPI`` is available on PyPI and GitHub.
For bug reports please create an issue on GitHub.
If you have questions, suggestions, etc. feel free to send me
an e-mail at `jorge.girazabal@gmail.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2015 Jorge Garcia Irazabal.
