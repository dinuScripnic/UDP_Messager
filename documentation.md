# Simple IMC Messaging Protocol (SIMP)
### Authors: Scripnic Dinu, David Bobek

## Introduction
The code provided is a simple client-server application using the UDP protocol and the socket library in Python. The project consists of 3 modules:
<ol>
<li>simp_client.py - the client side of the application
<li>simp_server.py -  the server side of the application
<li>header.py - a separate module that is used for encoding and decoding the header
</ol>
Server can be launched, then it will wait for the client. When the client will connect they both can chat, <b>IMPORTANT: synchronous conversation</b>. When the converstion needs to be ended, both sides can send a control message in order to do that.

## Header
### Header structure
The header is a 39 bytes long structure, that is used to identify the type of the message, the operation that needs to be done, the sequence number, the username and the length of the  message. ```SIMP_HEADER_FORMAT = '!BBB32sI'``` and it is defined in the header.py module. The structure is the following:
<ol>
<li>Type of the message. It could be either control message or chat message. Control message will be identified using the byte "0x01" and chat using "0x02".
<li>Operation of the message. In case of chat message type, this value will hold a constant of "0x01". For control message type, this value will hold the operation that needs to be done. 
<ul>
<li>0x01 - ERR, error
<li>0x02 - SYN, request for synchronisation
<li>0x04 - ACK, acknowledgment that a message reached the destination 
<li>0x06 - SYN+ACK, used in the 3 way handshake
<li>0x08 - FIN, used to end the conversation
</ul>
<li>Sequence number. This value will be used to identify if the message was resend or lost. Original message hold the value "0x00", while the lost ones "0x01".
<li> Username
<li> Lenght of the message
</ol>

### Header encoding
For encoding the header, we use the function "pack_simp_module" from the header.py module. It takes the values type(int), operation(int), sequence number(int), username(str) and length of the message(int) and returns the encoded header(bytes).

### Header decoding
For decoding the header, we use the function "unpack_simp_module" from the header.py module. It takes the encoded header(bytes) and returns a dictionary with the values type(int), operation(int), sequence number(int), username(str) and length of the message(int). We use the dictionary for a easier access to the values.

## Server
### Server structure
The server is a class that has the following attributes: host(int), port(int), timeout(int), name(str, inserted in the function), socket(socket), allowed_address(tuple[str,int]). The class has the following methods: recieve_message, send_control_message, send_chat_message, handle_control_message, connect, busy, reject, start, chat and quit. The class is defined in the simp_server.py module.
### Server methods description
#### recieve_message
This method is used to recieve a message from the client. In case the server is already busy, it will send a control message to reject the user. Otherwise it will decode the header and message and return them as a tuple.
#### send_control_message
This method is used to send a control message to the client. It takes the operation(int) and message(str), encodes the header and message and sends them to the client.
#### busy
This method is used to send a control message with the ERR operarion and "Server is busy!" to the client. It encodes the header and message and sends them to the client.
#### reject
This method is used to send a control message with the FIN operarion to the client in order to inform him that the server rejected the connection.
#### quit
This method is used to send a control message with the FIN operarion to the client in order to inform him that the server closed the connection. When the server will recieve an ACK it will close the connection.
#### send_chat_message
This method is used to send a chat message to the client. It takes the message(str), encodes the header and message and sends them to the client. Afterward it will wait for an ACK message from the client. If the ACK message is not received, it will resend the message.
#### handle_control_message
This method takes the header(dict) and message(str) and handles the control message. In has 2 cases: ERR and FIN. In case of ERR, it will print the error message, otherwise it will send an acknowledgement and close the connection.
#### start
This is the main loop of the server. First it asks the user for a name. Then will wait for a connection from the client. When the client will connect and the server will receieve a SYN message from the user it will go to the connect function.
#### connect
in this function the server will ask if the connection is acceptable. In case of a negative response it will send a reject control message. Otherwise it will send a SYN+ACK and wait for the ACK message. If the ACK message is received, connection is established and it will go to the chat function.
#### chat
This function is the main loop of the chat. It will recieve a message from the client and send it bacck an ACK. If the message is a control message, it will handle it. Otherwise it will ask for a message and send it back. If the message will be exit, it will send a FIN message and wait for an ACK message. If the ACK message is received, it will close the connection.

## Client
### Client structure
The client is a class that has the following attributes: host(int), port(int), timeout(int), name(str, inserted in the function), socket(socket), connected(bool). The class has the following methods: recieve_message, send_control_message, send_chat_message, handle_control_message, 3_way_handshake, start and chat. The class is defined in the simp_client.py module.
The functionality is simmilar to the one of the server.
### 3_way_handshake
This function is used to establish a connection with the server. It will send a SYN message and wait for a SYN+ACK message. If the SYN+ACK message is received, it will send an ACK message and return True. Otherwise it will close the connection.

## How to run the application
### Server
In order to run the applicaion we first have to start the server. In order to do so we have to run the following command in the terminal:
```
python3 simp_server.py <host> <port>
```
where <host> is the host of the server and <port> is the port of the server. Right after the app will ask for the name that has to be used in the chat.
### Client
Then we have to start the client. In order to do so we have to run the following command in the terminal:
```
python3 simp_client.py <host> <port>
```
where <host> is the host of the server and <port> is the port of the server. Right after the app will ask for the name that has to be used in the chat.
### Main loop
Consider both server and client are running. In that case the server will recieve a SYN message from the user and this question will apear:
```
Do you want to accept the connection? (y/n): 
```
in case thserver does not want to talk it can press 'n' and the client will recieve an message that will inform him that the server rejected the connection. If the server do want to connect press 'y'. In that case the connection will be established and the chating can start. Client is the one to start the chating, by inserting the message and pressing enter. When the server will recieve the message it will send the client the acknowledgement and after some time the message itself. This process will run until one of the sides will not send the 'quit' message. In that scenario the other part will recieve a FIN message, and after the initializer sends the acknowledgement the connection will be closed and the application will terminate.

## Libraries used
* Socket - standard python library
* struct - standard python library fro structuring and encoding the header