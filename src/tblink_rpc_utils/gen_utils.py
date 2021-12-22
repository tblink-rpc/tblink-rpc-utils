'''
Created on Oct 29, 2021

@author: mballance
'''
from tblink_rpc_utils.type_spec import TypeSpec, TypeKind

class GenUtils(object):
    
    def __init__(self, cpp_ptr=False):
        self.cpp_ptr = cpp_ptr
        if cpp_ptr:
            self.ptr = "->"
        else:
            self.ptr = "."
            
        
    def gen_mk_type(self, iftype_b, t : TypeSpec) -> str:
        if t is None:
            if self.cpp_ptr:
                return "0"
            else:
                return "null"
        elif t.kind == TypeKind.Int:
            return "%s%smkTypeInt(%s, %d)" % (
                iftype_b,
                self.ptr,
                self.bool_str(t.is_signed),
                t.width)
        elif t.kind == TypeKind.Bool:
            return "%s%smkTypeBool()" % (
                iftype_b,
                self.ptr)
            
    def bool_str(self, v):
        if self.cpp_ptr:
            return "true" if v else "false"
        else:
            return "1" if v else "0"
        
    def to_id(self, v):
        return v.replace('.', '_')
