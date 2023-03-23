import sys, os
assert sys.version_info.major>2 and sys.version_info.minor>5, "Python 3.6+ required"
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')

import copy
from json import dumps
import time


class worker:
  ''' base class to work on group of requests
  based on pdmv rest api python implementation
  https://cms-pdmv.gitbook.io/project/mccontact/scripting-in-mcm
  https://github.com/cms-PdmV/mcm_scripts
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

  def fetch(self):
    print("WARNING: fetch method not implemented for the base class")

  def __str__(self):
    return '\n'.join(["Requests in {}:".format(self.name)]+[
      "\t"+req['prepid'] for req in self.requests
    ])

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
    self.fetch(sleep=2)
    print('\n'.join([
      '{ID}\tstatus {S}\tapproval {A}'.format(
        ID=req['prepid'], S=req['status'], A=req['approval']
      ) for req in self.requests])
    )

  def reset(self):
    for req in self._requests:
      self.mcm.reset(req)
    print("requests for {} have been reset".format(self.name))
    self.fetch(sleep=2)

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
    self.fetch(sleep=2)

  def validate(self):
    ''' validate the requests.
    Equivalent of pushing the "approve" button on McM
    '''
    for req in self._requests:
      self.mcm.approve(object_type='requests', object_id=req)
    print("validation run for {}".format(self.name))
    self.fetch(sleep=2)

  def new_ticket(self, pwg, block, chain):
    ''' WIP
    '''
    ticket = {
      'pwg'     : pwg   ,
      'block'   : block ,
      'chains'  : chain ,
      'requests': self.requests,
    }
  
  def grasp(self, campaigns, shorten=False):
    ''' returns the link to the grasp monitor page.
    can (WIP) interface with CERN url shortening service
    https://espace.cern.ch/webservices-help/other-services/Shorten-long-URL/Pages/Usage.aspx
    '''
    LINK="https://cms-pdmv.cern.ch/grasp/samples?dataset_query={D}&campaign={C}".format(
      D=','.join(req['dataset_name'] for req in self.requests),
      C=','.join(campaigns)
    )
    if not shorten: return LINK
    import requests
    service = "https://webservices.web.cern.ch/webservices/Services/ShortenURL/"
    cookie  = worker.generate_cookie(url=service)
    url     = service+"default?shorten="+LINK
    req     = requests.get(url, verify=True, cookies=cookie, allow_redirects=True)
    import pdb; pdb.set_trace()

  @staticmethod
  def generate_cookie(url):
    '''generate a cookie. WIP.
    '''
    import tempfile
    import http.cookiejar as cookielib
    cookiepath = '/tmp/{}/cookiefile_SU.txt'.format(os.getlogin())
    cmd = 'auth-get-sso-cookie --url "{}" -o {}'.format(url, cookiepath)
    ret = os.system(cmd)
    cookie = cookielib.MozillaCookieJar(cookiepath)
    cookie.load()
    return cookie

class workerR(worker):
  ''' init a group of requests from prepids
  '''
  def __init__(self, requests, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._requests = requests
    self.fetch()

  def fetch(self, sleep=0):
    time.sleep(sleep)
    self.requests = [self.mcm.get(object_type='requests', object_id=req) for req in self._requests]

  def clone(self, campaign, update={}):
    cloned = copy.deepcopy(self.requests)
    for clo in cloned:
      for k, v in update.items():
        clo[k]=v
      clo['member_of_campaign']=campaign

    clone_answers = [self.mcm.clone_request(clo) for clo in cloned]
    _cloned       = [clo['prepid'] for clo in clone_answers]
    newset = workerR(name="cloned_{}_{}".format(self.name, campaign), mcm=self.mcm, requests=_cloned)
    newset.checkid()
    print(newset)

    return newset

class workerT(worker):
  ''' fetch and work on requests from a ticket id
  '''
  def __init__(self, ticket, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._ticket    = ticket
    self.fetch()

  def fetch(self, sleep=0):
    time.sleep(sleep)
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
