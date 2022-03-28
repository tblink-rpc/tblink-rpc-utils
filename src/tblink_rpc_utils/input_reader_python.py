'''
Created on Mar 27, 2022

@author: mballance
'''
import importlib
import sys
import traceback

from tblink_rpc.impl import iftype_rgy
from tblink_rpc_utils.idl_spec import IDLSpec
from tblink_rpc_utils.input_reader import InputReader
from tblink_rpc_utils.input_spec import InputSpec
from tblink_rpc_utils.interface_type_spec import InterfaceTypeSpec
from tblink_rpc_utils.method_spec import MethodSpec
from tblink_rpc_utils.type_spec import TypeKind, TypeSpec
from tblink_rpc_utils.type_spec_int import TypeSpecInt
from tblink_rpc_utils.type_spec_map import TypeSpecMap
from tblink_rpc_utils.type_spec_vec import TypeSpecVec


class InputReaderPython(InputReader):
    
    def read(self, in_spec:InputSpec)->IDLSpec:
        from tblink_rpc.impl.iftype_rgy import IftypeRgy
        
        for p in reversed(in_spec.libpath):
            sys.path.insert(0, p)
        
        if len(in_spec.files) == 0:
            raise Exception("No modules specified to load")

        iftype_rgy = IftypeRgy.reset()
        
        for m in in_spec.files:
            try:
                importlib.import_module(m)
            except Exception as e:
                print("TbLink-RPC Error: Failed to load module %s" % m)
                traceback.print_exc()
                raise e
            
        if len(iftype_rgy.iftypes) == 0:
            raise Exception("No TbLink-RPC Interface Types discovered")

        ret = IDLSpec()
        
        for i in iftype_rgy.iftypes:
            ret.add_iftype(self._iftype2idl(i))
            
        return ret

    def _iftype2idl(self, iftype) -> InterfaceTypeSpec:
        ret = InterfaceTypeSpec(iftype.name)
        
        for m in iftype.methods:
            ret.add_method(self._ifmethod2idl(m))

        return ret
    
    def _ifmethod2idl(self, method_t) -> MethodSpec:
        ret = MethodSpec(
            method_t.name,
            self._ptype2idl(method_t.rtype),
            method_t.is_export,
            method_t.is_task)
        
        return ret

    def _ptype2idl(self, ptype):
        from tblink_rpc.impl.type_decl import TypeDeclE
        
        int_m = {
            TypeDeclE.i8: (True, 8),
            TypeDeclE.i16: (True, 16),
            TypeDeclE.i32: (True, 32),
            TypeDeclE.i64: (True, 64),
            TypeDeclE.u8: (False, 8),
            TypeDeclE.u16: (False, 16),
            TypeDeclE.u32: (False, 32),
            TypeDeclE.u64: (False, 64)
            }
        
        if ptype is None:
            return None
        else:
            if ptype.base_t == TypeDeclE.bool:
                return TypeSpec(TypeKind.Bool)
            elif ptype.base_t in int_m.keys():
                return TypeSpecInt(
                    int_m[ptype.base_t][1],
                    int_m[ptype.base_t][0])
            elif ptype.base_t == TypeDeclE.str:
                return TypeSpec(TypeKind.Str)
            elif ptype.base_t == TypeDeclE.vec:
                return TypeSpecVec(
                    self._ptype2idl(ptype.elem_t))
            elif ptype.base_t == TypeDeclE.map:
                return TypeSpecMap(
                    self._ptype2idl(ptype.key_t),
                    self._ptype2idl(ptype.elem_t))
            else:
                raise Exception("Unknown ptype %s" % str(ptype))
            pass
        