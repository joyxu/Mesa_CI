#!/usr/bin/python
import importlib
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs


def get_external_revisions(revisions_dict=None):
    return bs.skqp_external_revisions(project="skqp",
                                      revisions_dict=revisions_dict)


if __name__ == "__main__":
    bs.build(bs.SkqpBuilder())
