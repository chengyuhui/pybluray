__author__ = 'Harry'

from index_parser import Index


idx = Index('index.bdmv')
idx.parse()

print idx.app_info
