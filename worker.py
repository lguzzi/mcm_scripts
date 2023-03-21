from __future__ import print_function
from json import dumps
import copy

import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

assert sys.version_info.major>2 and sys.version_info.minor>5, "Python 3.6+ required"

class worker:
  ''' base class to work on group of requests
  '''
  chain_RunIISummer20UL18     = ''
  chain_RunIISummer20UL17     = ''
  chain_RunIISummer20UL16     = ''
  chain_RunIISummer20UL16APV  = ''
  chain_Run3Summer22GS    = ''
  chain_Run3Summer22EEGS  = ''
  def __init__(self, mcm, name):
    self.name = name
    self.mcm  = mcm

  def fetch():
    pass

  def checkid(self):
    ''' check that requests are valid
    '''
    if all('prepid' in req.keys() for req in self.requests):
      print("check {} OK".format(self.name))
    else:
      print("check {} FAILED".format(self.name))

  def checkstate(self):
    ''' check the status and approval state of the requests
    '''
    print('\n'.join([
      '{ID}\tstatus {S}\tapproval {A}'.format(
        ID=req['prepid'], S=req['status'], A=req['approval']
      ) for req in self.requests])
    )

  def update(self, fields):
    ''' WARNING: are you sure you don't want to use the McM webpage? 
    update request attributes from json.
    If the value is a lambda, the request dictionary is fed to it
    '''
    for req in self.requests:
      for k, v in fields.items():
        req[k] = v if not type(v)==type(lambda: None) else v(req)
      update_response = self.mcm.update('requests', req)
      print('Update response: %s' % (update_response))
    self.fetch()

  def validate(self):
    ''' validate the requests.
    Equivalent of pushing the "approve" button on McM
    '''
    for req in self._requests:
      self.mcm.approve(object_type='requests', object_id=req)
    print("validation run for {}".format(self.name))
    self.fetch()

  def new_ticket(self, pwg, block, chain):
    ''' WIP
    '''
    ticket = {
      'pwg'     : pwg   ,
      'block'   : block ,
      'chains'  : chain ,
      'requests': self.requests,
    }

class workerR(worker):
  ''' init a group of requests from prepids
  '''
  def __init__(self, name, requests, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._requests = [self.mcm.get(req) for req in requests]

class workerT(worker):
  ''' fetch and work on requests from a ticket id
  '''
  def __init__(self, ticket, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._ticket    = ticket
    self.fetch()

  def fetch(self):
    self.ticket     = self.mcm.get(object_id=self._ticket, object_type='mccms')
    self.requests   = self.mcm.root_requests_from_ticket(self._ticket)
    self._requests  = [req['prepid'] for req in self.requests]
  
  def clone(self, campaign, newname='cloned', newticket=True):
    ''' clone the ticket requests in a new campaign and
    possibly in a new ticket
    '''
    tmp = copy.deepcopy(self.requests)
    for req in self.cloned:
      req['member_of_campaign'] = campaign

    cloned = [
      self.mcm.clone_request(req) for req in requests
    ]
    return workerR(name=newname, requests=cloned)
