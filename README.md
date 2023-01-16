# Networking-project


 # SIMP
Specification
SIMP represents a lightweight protocol. As such, it won’t need all connection-oriented functionalities pro-vided by TCP.
Therefore, it was decided to implement it on top of UDP. Nevertheless, SIMP needs somefunctionality for ensuring that messages are delivered – otherwise, 
user messages could get lost on its way.The protocol operates in the following way: first, any user may contact another user for starting a chat. 
Usersare identified by their IP address and port number (of course, every user needs to run a SIMP implementationin order to get contacted in the first place). 
The user can accept or decline the invitation to chat. Afteraccepting the invitation, both users can send messages to each other until one of them closes the connection.
If a user already in a chat gets an invitation to chat from another user, that invitation will be automaticallyrejected by sending an error message
(user is busy in another chat).
