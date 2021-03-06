#!/usr/bin/python
__author__ = "Guillaume Bonamis"
__license__ = "MIT"
__copyright__ = "2015, ESRF"

import argparse
from os.path import dirname, abspath
base = dirname(dirname(abspath(__file__)))
from freesas.align import InputModels, AlignModels
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("log_freesas")

usage = "supycomb.py FILES [OPTIONS]"
description = "align several models and calculate NSD"
parser = argparse.ArgumentParser(usage=usage, description=description)
parser.add_argument("file", metavar="FILE", nargs='+', help="pdb files to align")
parser.add_argument("-m", "--mode",dest="mode", type=str, choices=["SLOW", "FAST"], default="SLOW", help="Either SLOW or FAST, default: %(default)s)")
parser.add_argument("-e", "--enantiomorphs",type=str, choices=["YES", "NO"], default="YES", help="Search enantiomorphs, YES or NO, default: %(default)s)")
parser.add_argument("-q", "--quiet", type=str, choices=["ON", "OFF"], default="ON", help="Hide log or not, default: %(default)s")
parser.add_argument("-g", "--gui", type=str, choices=["YES", "NO"], default="YES", help="Use GUI for figures or not, default: %(default)s")
parser.add_argument("-o", "--output", type=str, default="aligned.pdb", help="output filename, default: %(default)s")

args = parser.parse_args()
input_len = len(args.file)
logger.info("%s input files"%input_len)
selection = InputModels()

if args.mode=="SLOW":
    slow = True
    logger.info("SLOW mode")
else:
    slow = False
    logger.info("FAST mode")

if args.enantiomorphs=="YES":
    enantiomorphs = True
else:
    enantiomorphs = False
    logger.info("NO enantiomorphs")

if args.quiet=="OFF":
    logger.setLevel(logging.DEBUG)
    logger.info("setLevel: Debug")

if args.gui=="NO":
    save = True
    logger.info("Figures saved automatically : \n  R factor values and selection =>  Rfactor.png \n  NSD table and selection =>  nsd.png")
else:
    save = False

align = AlignModels(args.file, slow=slow, enantiomorphs=enantiomorphs)
if input_len==2:
    align.outputfiles = args.output
    align.assign_models()
    dist = align.alignment_2models()
    logger.info("%s and %s aligned"%(args.file[0], args.file[1]))
    logger.info("NSD after optimized alignment = %.2f" % dist)
else:
    align.outputfiles = ["model-%02i.pdb" % (i+1) for i in range(input_len)]
    selection.inputfiles = args.file
    selection.models_selection()
    selection.rfactorplot(save=save)
    align.models = selection.sasmodels
    align.validmodels = selection.validmodels

    align.makeNSDarray()
    align.alignment_reference()
    logger.info("valid models aligned on the model %s"%(align.reference+1))
    align.plotNSDarray(rmax=round(selection.rmax, 4), save=save)

if not save and input_len > 2:
    raw_input("Press any key to exit")