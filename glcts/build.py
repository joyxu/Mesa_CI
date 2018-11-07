#!/usr/bin/python

import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

def get_external_revisions(revisions_dict=None):
    return bs.deqp_external_revisions(project="glscts",
                                      revisions_dict=revisions_dict)

if __name__ == "__main__":
    bs.build(bs.CtsBuilder(suite="gl"))
