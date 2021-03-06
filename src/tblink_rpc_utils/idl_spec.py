'''
Created on Oct 19, 2021

@author: mballance
'''
from tblink_rpc_utils.interface_type_spec import InterfaceTypeSpec

class IDLSpec(object):
    
    def __init__(self):
        self.iftype_m = {}
        self.iftypes = []
        pass
    
    def add_iftype(self, iftype):
        if iftype.name in self.iftype_m.keys():
            raise Exception("Duplicate iftype %s" % iftype.name)
        self.iftype_m[iftype.name] = iftype
        self.iftypes.append(iftype)
        
    def find_iftype(self, iftype) -> InterfaceTypeSpec:
        if iftype in self.iftype_m.keys():
            return self.iftype_m[iftype]
        else:
            return None
    
    
