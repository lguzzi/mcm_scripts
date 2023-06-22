import sys, os
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/..")
from rest import McM

import argparse
parser = argparse.ArgumentParser('''ugly and pretentious script to fetch all the requests in a campaign.
Works by brute force creating --max rest calls of increasing PID to the input campaigns.
Merge everything in a nice gdoc style.
''')
parser.add_argument('--max'       , default=100, help='max pid to brute fetch')
parser.add_argument('--campaigns' , default=["BPH-Run3Summer22GS"], nargs="+", help="list of campaigns to fetch")
parser.add_argument('--minpid'    , default=0, help='ignore requests with lower PID')
args = parser.parse_args()

mcm = McM(dev=False)


class Campaign:
  MAX = args.max
  def __init__(self, campaign):
    ''' create the dictionary
    {
      dataset_1 = {
        campaign_name: [request list]
      },
      dataset_2 = {
        campaign_name: [request list]
      },
      ...
    }'''
    self.camp = campaign
    self.reql = self.fetch()
    self.reqd = {}
    for req in self.reql:
      dname = req['dataset_name']
      prepid= req['prepid']
      if not dname in self.reqd.keys():
        self.reqd[dname] = {}
        self.reqd[dname][self.camp] = []
      self.reqd[dname][self.camp].append(prepid)
  
  def fetch(self):
    pidder= lambda idx: '0'*(5-len(str(int(idx))))+str(int(idx)) if not idx>99999 else 'MAXPIDREACHED'
    brute = lambda idx, c: mcm.get("requests", "{C}-{PID}".format(C=c, PID=pidder(idx)), method="get")
    return [r for r in [
      brute(i, self.camp) for i in range(Campaign.MAX)
    ] if r is not None and int(r['prepid'][-5:])>=args.minpid]

def merge(campaigns):
  ''' merge multiple Campaign dictionaries
  {
    dataset_1:{
      campaign1: [requests],
      campaign2: [requests],
      ...
    }
    ...
  }'''
  ret = {}
  for c in campaigns:
    for d, r in c.reqd.items():
      if not d in ret.keys():
        ret[d] = {}
      ret[d].update(c.reqd[d])
  return ret

def write(dictionary, outfile, gstyle=False):
  ''' write the merged dictionary into a file
  dataset_name \t PID_campaign1_request1 \t PID_campaign2_request1 \n
  \t              PID_campaign1_request2 \t PID_campaign2_request2 \n
  ...
  and uses gsheet HYPERLINK syntax
  '''
  ext = lambda l, max: l+['']*(max-len(l)) if len(l)<max else l
  frm = lambda s, what: '=HYPERLINK("https://cms-pdmv.cern.ch/mcm/requests?{W}={S}";"{S}")'.format(W=what,S=s) if gstyle else s
  with open(outfile, 'w') as ofile:
    for dname, camps in dictionary.items():
      reqs = [camps[k] for k in camps.keys()]
      maxs = max(len(r) for r in reqs)
      reqs = [ext(r,maxs) for r in reqs]
      rtxt = '\n\t'.join('\t'.join(frm(reqs[i][j], 'prepid') for i in range(len(reqs))) for j in range(maxs))
      ofile.write('{}\t{}\n'.format(frm(dname,'dataset_name'), rtxt))

campaigns = [
  Campaign(c) for c in args.campaigns
]
merged = merge(campaigns)

write(merged, "Run3Samples.txt", True)