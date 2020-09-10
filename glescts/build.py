#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import CtsBuilder
from testers import deqp_external_revisions


def get_external_revisions(revisions_dict=None):
    return deqp_external_revisions(project="glescts",
                                   revisions_dict=revisions_dict)


if __name__ == "__main__":
    build(CtsBuilder(suite="es"))
