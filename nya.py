__author__ = 'Harry'

from index_parser import Index
from mobj_parse import MovieObject
from mpls_parse import Playlist


idx = Index('index.bdmv')
idx.parse()
mobj = MovieObject('MovieObject.bdmv')
mobj.parse()

pls = Playlist('00000.mpls')
print pls.parse()
