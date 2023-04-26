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
  chain_RunIISummer20UL18     = 'chain_RunIISummer20UL18GEN_flowRunIISummer20UL18SIM_flowRunIISummer20UL18DIGIPremix_flowRunIISummer20UL18HLT_flowRunIISummer20UL18RECO_flowRunIISummer20UL18MiniAODv2_flowRunIISummer20UL18NanoAODv9'
  chain_RunIISummer20UL17     = 'chain_RunIISummer20UL17GEN_flowRunIISummer20UL17SIM_flowRunIISummer20UL17DIGIPremix_flowRunIISummer20UL17HLT_flowRunIISummer20UL17RECO_flowRunIISummer20UL17MiniAODv2_flowRunIISummer20UL17NanoAODv9'
  chain_RunIISummer20UL16     = 'chain_RunIISummer20UL16GEN_flowRunIISummer20UL16SIM_flowRunIISummer20UL16DIGIPremix_flowRunIISummer20UL16HLT_flowRunIISummer20UL16RECO_flowRunIISummer20UL16MiniAODv2_flowRunIISummer20UL16NanoAODv9'
  chain_RunIISummer20UL16APV  = 'chain_RunIISummer20UL16GENAPV_flowRunIISummer20UL16SIMAPV_flowRunIISummer20UL16DIGIPremixAPV_flowRunIISummer20UL16HLTAPV_flowRunIISummer20UL16RECOAPV_flowRunIISummer20UL16MiniAODAPVv2_flowRunIISummer20UL16NanoAODAPVv9'
  chain_Run3Summer22GS    = ''
  chain_Run3Summer22EEGS  = ''
  def __init__(self, mcm, name, pwg='BPH'):
    self.name = name
    self.mcm  = mcm
    self.pwg  = pwg

  def fetch(self):
    print("WARNING: fetch method not implemented for the base class")

  def __str__(self):
    return '\n'.join(["Requests in {}:".format(self.name)]+[
      "\t"+req['prepid'] for req in self.requests
    ])

  def checkid(self):
    ''' check that requests are valid
    '''
    return all('prepid' in req.keys() for req in self.requests)

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

  @staticmethod
  def new_ticket(mcm, requests, name, chains, pwg='BPH', block=3):
    ''' WIP
    '''
    ticket = {
      'pwg'     : pwg     ,
      'requests': requests,
      'block'   : block   ,
      'chains'  : chains  ,
    }
    tick = mcm.put(object_type='mccms', object_data=ticket, method='save')
    mcm.get(object_type="mccms", object_id=tick.prepid(), method='update_total_events')
    return workerT(name=name, ticket=tick['prepid'], mcm=mcm)
  
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

  @staticmethod
  def getlink(label, url):pass
#    return f"\u001b]8;;{url}\u001b\\{target}\u001b]8;;\u001b\\"
#    return f"\x1b]8;;{url}\a{label}\x1b]8;;\a"

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

  def prepid(self):
    return self._ticket

  def fetch(self, sleep=0):
    time.sleep(sleep)
    self.ticket     = self.mcm.get(object_id=self._ticket, object_type='mccms')
    self.requests   = self.mcm.root_requests_from_ticket(self._ticket)
    self._requests  = [req['prepid'] for req in self.requests]

  def clone(self, campaign, chains, pwg='BPH', block=3, newticket=True, name="cloned"):
    ''' clone the ticket requests in a new campaign and
    possibly in a new ticket
    '''
    tmp = copy.deepcopy(self.requests)
    for req in tmp:
      req['member_of_campaign'] = campaign

    cloned = [self.mcm.clone_request(req) for req in tmp]
    newids = [clo['prepid'] for clo in cloned]
    newset = workerR(name=name, requests=newids, mcm=self.mcm)
    newset.checkstate()
    if not newticket: return newset
    return worker.new_ticket(mcm=self.mcm, requests=newids, pwg=pwg, block=block, chains=chains, name=name)

  def get_request_string(self, million=True):
    tlink     = worker.getlink(self._ticket, "https://cms-pdmv.cern.ch/mcm/mccms?prepid="+self._ticket)
    campaign  = self.requests[0]['member_of_campaign']
    clink     = ' '.join(worker.getlink('chain', 'https://cms-pdmv.cern.ch/mcm/chained_campaigns?prepid='+str(chain)) for chain in self.ticket['chains']) 
    events    = self.ticket['total_events']/1.e+6 if million else self.ticket['total_events']
    print(f"{tlink} | {campaign} | {clink} | {events}")