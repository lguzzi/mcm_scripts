import sys, os
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/..")
from rest import McM
from worker import worker,workerR,workerT

## init the mcm object (requires access permissions)
mcm = McM(dev=False)
## create an object handling an existing online ticket
bmm_R3 = workerT(mcm=mcm, name="bmmR3", ticket="BPH-2023Mar22-00001")

## operate on the ticket
bmm_R3.checkstate()
#bmm_R3.validate()
## etc.

#print the grasp link
print(bmm_R3.grasp(campaigns=["Run3Summer22*GS"]))