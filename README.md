more info: https://github.com/cms-PdmV/mcm_scripts

**NOTE**: this is a work in progress.

This repo implements two classes to handle request validation and cloning.
The class *workerR* is initialized from a group of requests (list of request PID's). These requests can be cloned into a new object using the method *clone* (this will create new requests online!).  
The class *workerT* is initialized from a McM ticket PID. The requests in the ticket can be cloned into a new ticket using the method *clone* (this will create new requests online!). **NOTE** cloning of tickets to be tested.  
Methods common to the two classes are define in the *worker* base class:
- *checkid*: checks that all requests in the object list are present online
- *checkstate*: prints the state of the requests in the list/ticket
- *reset*: reset all the requests in the list/ticket
- *update*: given a dictionary of the type {field: newvalue}, updates the specified fields of each request. If *newvalue* is a lambda function, it is evaluated on the request. 
- *validate*: runs the validation of the requests in the list/ticket. 
- *grasp*: creates a grasp link for monitoring

*NOTE* almost all methods act online on the McM website.
