from __future__ import print_function
import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
from json import dumps
import copy

class worker():
  ''' base class to work on group of requests
  '''
  chain_RunIISummer20UL18     = ''
  chain_RunIISummer20UL17     = ''
  chain_RunIISummer20UL16     = ''
  chain_RunIISummer20UL16APV  = ''
  chain_Run3Summer22GS    = ''
  chain_Run3Summer22EEGS  = ''
  def __init__(self, mcm, name, *args, **kwargs)
    self.name = name
    self.mcm  = mcm
    self.requests = []

  def checkid(self):
    _ = '====checking {}===='.format(self.name)
    print(_)
    print('\n'.join([
      'Clone PrepID: {}'.format(req['prepid']) if req.get('results') else "\nCLONE ERROR: {}\n".format(dumps(req))
      for req in self.requests
    ]))
    print("="*len(_))

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

  def validate(self):
    for req in self.requests:
      self.mcm.approve(object_type='requests', object_id=req)

  def new_ticket(self, pwg, block, chain):
    ticket = {
      'pwg'     : pwg   ,
      'block'   : block ,
      'chains'  : chain ,
      'requests': self.requests,
    }

class workerR(worker):
  ''' init a group of requests from prepids
  '''
  def __init__(self, name, requests, *args, **kwargs)
    super().__init__(*args, **kwargs)
    self._requests = [self.mcm.get(req) for req in requests]

class workerT(worker):
  ''' fetch and work on requests from a ticket id
  '''
  def __init__(self, name, ticket, *args, **kwargs)
    super().__init__(*args, **kwargs)
    self._ticket    = ticket
    self.ticket     = self.mcm.get(object_id=self._ticket, object_type='mccms')
    self.requests   = self.mcm.root_requests_from_ticket(self._ticket)
    self._requests  = [req.prepid for req in self.requests]
  
  def clone(self, campaign):
    tmp = copy.deepcopy(self.requests)
    for req in self.cloned:
      req['member_of_campaign'] = campaign

    cloned = [
      self.mcm.clone_request(req) for req in requests
    ]
    return workerR(requests=cloned)
