'''
Created on Mar 27, 2022

@author: mballance
'''
from tblink_rpc_utils.output_spec import OutputSpec
from tblink_rpc_utils.output_writer import OutputWriter
from tblink_rpc_utils.output import Output
from tblink_rpc.decorators import iftype
import sys
from tblink_rpc_utils.method_spec import MethodSpec
from tblink_rpc_utils.type_spec import TypeSpec, TypeKind


class OutputWriterSv(OutputWriter):
    
    def __init__(self, is_uvm):
        self.is_uvm = is_uvm
    
    def write(self, out_s:OutputSpec):

        # For each output...
        for iftype in out_s.iftypes:
            out = Output(sys.stdout)

            self._gen_iftype(out, iftype)
                    
        pass


    def _gen_iftype(self, out, iftype):
        out.println("typedef class %s_proxy;" % iftype.name)
        out.println("typedef class %s_t;" % iftype.name)
        out.println()
        
        self._gen_base_impl(out, iftype, False)
        out.println()
        self._gen_proxy(out, iftype, False)
        out.println()
        self._gen_base_impl(out, iftype, True)
        out.println()
        self._gen_proxy(out, iftype, True)
        out.println()
        self._gen_type_factory(out, iftype)
        out.println()
        pass

    def _gen_base_impl(self, out, iftype, is_mirror):
        # TODO: for non-uvm output, should use a tblink base class
        if is_mirror:
            out.println("class %s_mirror_base #(type Tbase=uvm_pkg::uvm_object) extends Tbase;" % (
                iftype.name))
        else:
            out.println("class %s_base #(type Tbase=uvm_pkg::uvm_object) extends Tbase;" % (
                iftype.name))
            
        out.inc_ind()

        if is_mirror:        
            out.println("typedef %s_mirror_proxy #(%s_mirror_base) proxy_t;" % (iftype.name, iftype.name))
        else:
            out.println("typedef %s_proxy #(%s_base) proxy_t;" % (iftype.name, iftype.name))
            
        out.println("proxy_t m_proxy;")
        
        if self.is_uvm:
            out.println("function new(string name=\"%s\");" % iftype.name)
            out.inc_ind()
            out.println("super.new(name);")
            out.dec_ind()
            out.println("endfunction")

        out.println()
        
        out.println("virtual function void set_proxy(proxy_t proxy);")
        out.inc_ind()
        out.println("m_proxy = proxy;")
        out.dec_ind()
        out.println("endfunction")
        
        out.println()

        # Generate function wrappers        
        for m in iftype.methods:
            pass
        
        out.println()
        
        out.dec_ind()
        out.println("endclass")
        pass
    
    def _gen_proxy(self, out, iftype, is_mirror):
        pass
        
    def _gen_type_factory(self, out : Output, iftype):
        out.println("class %s_t extends tblink_rpc::InterfaceTypeRgy #(" % iftype.name)
        out.inc_ind()
        out.inc_ind()
        out.println("%s_factory," % iftype.name)
        out.println("\"%s\"," % iftype.name)
        out.println("tblink_rpc::InterfaceImplFactoryBase #(%s_proxy #(%s_base))," % (
            iftype.name,
            iftype.name))
        out.println("tblink_rpc::InterfaceImplFactoryBase #(%s_mirror_proxy #(%s_mirror_base)));" % (
            iftype.name,
            iftype.name))
        out.dec_ind()
        
        out.println("virtual function tblink_rpc::IInterfaceType defineType(tblink_rpc::IEndpoint ep);")
        out.inc_ind()
        out.println("tblink::IInterfaceType iftype = ep.findInterfaceType(name());")
        out.println()
        out.println("if iftype == null) begin")
        out.inc_ind()
        out.println("tblink_rpc::IInterfaceTypeBuilder iftype_b =")
        out.inc_ind()
        out.println("ep.newInterfaceTypeBuilder(name());")
        out.dec_ind()
        out.println("tblink_rpc::IMethodTypeBuilder mt_b;")
        out.println()
        
        for i,m in enumerate(iftype.methods):
            self._gen_method_t(out, i+1, m)
            
        out.println()
        out.println("iftype = ep.defineInterfaceType(")
        out.inc_ind()
        out.inc_ind()
        out.println("iftype_b,")
        out.println("getImplFactory(),")
        out.println("getMirrorImplFactory());")
        out.dec_ind()
        out.dec_ind()
        
        out.dec_ind()
        out.println("end")
        out.println()
        out.println("return iftype;")
        out.dec_ind()
        out.println("endfunction")

        out.dec_ind()
        out.println()
        
        out.println("endclass")
        pass
    
    def _gen_method_t(self, out : Output, id, m : MethodSpec):
        
        out.println("mt_b = iftype_b.newMethodTypeBuilder(")
        out.inc_ind()
        out.println("\"%s\"," % m.name)
        out.println("%d," % id)
        out.println(self._gen_mkptype(m.rtype) + ",")
        out.println("%d," % m.is_export)
        out.println("%d);" % m.is_blocking)
        out.dec_ind()
        
        for p in m.params:
            out.println("mt_b.add_param(\"%s\", %s);" % (
                p[0],
                self._gen_mkptype(p[1])))

        out.println("void'(iftype_b.add_method(mt_b));")

        pass
    
    def _gen_mkptype(self, t : TypeSpec):
        if t is None:
            return "null"
        elif t.kind == TypeKind.Bool:
            return "iftype_b.mkTypeBool()"
        elif t.kind == TypeKind.Int:
            return "iftype_b.mkTypeInt(%d, %d)" % (t.is_signed, t.width)
        elif t.kind == TypeKind.Map:
            return "iftype_b.mkTypeMap(%s, %s)" % (
                self._gen_mkptype(t.key_t),
                self._gen_mkptype(t.elem_t))
        elif t.kind == TypeKind.Str:
            return "iftype_b.mkTypeStr()"
        elif t.kind == TypeKind.Vec:
            return "iftype_b.mkTypeVec(%s)" % (
                self._gen_mkptype(t.key_t))
        else:
            return "XX"
        pass
        
    