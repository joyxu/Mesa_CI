#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from builders import SkqpBuilder, skqp_external_revisions
from build_support import build


def get_external_revisions(revisions_dict=None):
    return skqp_external_revisions(project="skqp",
                                   revisions_dict=revisions_dict)


if __name__ == "__main__":
    build(SkqpBuilder())
