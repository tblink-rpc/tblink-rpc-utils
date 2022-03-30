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
        out_sv = out_s.out
        
        if out_sv is None:
            if len(out_s.iftypes) == 1:
                out_sv = out_s.iftypes[0].name + ".svh"
            else:
                out_sv = "tblink_rpc_iftypes.svh"

        with open(out_sv, "w") as fp:
            out = Output(fp)

            # For each output...
            for iftype in out_s.iftypes:
                self._gen_iftype(out, iftype)
                    
        pass


    def _gen_iftype(self, out, iftype):
        out.println("typedef class %s_proxy;" % iftype.name)
        out.println("typedef class %s_mirror_proxy;" % iftype.name)
        out.println("typedef class %s_t;" % iftype.name)
        out.println()

        self._gen_proxy_if(out, iftype, False)        
        out.println()
        self._gen_base_impl(out, iftype, False)
        out.println()
        self._gen_proxy(out, iftype, False)
        out.println()
        self._gen_proxy_if(out, iftype, True)
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

        mirror_s = ""        
        if is_mirror:
            mirror_s = "_mirror"
            
        out.println("class %s%s_base #(type Tbase=uvm_pkg::uvm_object) extends Tbase;" % (
                iftype.name, mirror_s))
            
        out.inc_ind()

        out.println("%s%s_proxy_if m_proxy;" % (iftype.name, mirror_s))
        out.println()
        
        if self.is_uvm:
            out.println("function new(string name=\"%s\");" % iftype.name)
            out.inc_ind()
            out.println("super.new(name);")
            out.dec_ind()
            out.println("endfunction")

        out.println()
        
        out.println("virtual function void set_proxy(%s%s_proxy_if proxy);" % (
            iftype.name, mirror_s))
        out.inc_ind()
        out.println("m_proxy = proxy;")
        out.dec_ind()
        out.println("endfunction")
        
        out.println()

        # Generate function wrappers        
        for m in iftype.methods:
            self._gen_method_impl(out, iftype, m, is_mirror)
        
        out.println()
        
        out.dec_ind()
        out.println("endclass")
        pass
    
    def _gen_method_impl(self, out, iftype, m : MethodSpec, is_mirror):
        if m.is_blocking:
            out.println("virtual task %s(" % m.name)
        else:
            rtype_str = "void"
            if m.rtype is not None: 
                rtype_str = self._gen_mksvtype(m.rtype)
                
            out.println("virtual function %s %s(" % (rtype_str, m.name))
        out.inc_ind()
        out.inc_ind()

        # Add an output parameter for task return value
        if m.is_blocking and m.rtype is not None:
            comma = ""
            if len(m.params) > 0:
                comma = ","
            out.println("output retval %s%s" % (self._gen_mksvtype(m.rtype), comma))

        # Now, generate the remaining parameters
        for i,p in enumerate(m.params):
            comma = ""
            if i+1 < len(m.params):
                comma = ","
            out.println("input %s %s%s" % (self._gen_mksvtype(p[1]), p[0], comma))

        out.println(");")        
        out.dec_ind()

        
        if (m.is_export and not is_mirror) or (not m.is_export and is_mirror):
            # Generate a sanity-check implementation
            if self.is_uvm:
                out.println("`uvm_fatal(\"%s\", \"Method %s is not implemented\");" % (
                    iftype.name, m.name))
            else:
                out.println("$display(\"TbLink-RPC Error: Method %s::%s is not implemented\");" % (
                    iftype.name, m.name))
                out.println("$finish;")
                
            if m.rtype is not None:
                if m.is_blocking:
                    out.println("reval = %s;" % self._gen_dfltval(m.rtype))
                else:
                    out.println("return %s;" % self._gen_dfltval(m.rtype))
        else:
            # Generate an implementation that invokes the proxy
            if m.rtype is not None and not m.is_blocking:
                out.println("return m_proxy.%s(" % m.name)
            else:
                out.println("m_proxy.%s(" % m.name)
                
            out.inc_ind()
            out.inc_ind()
                
            if m.rtype is not None and m.is_blocking:
                comma = ""
                if len(m.params) > 0:
                    comma = ","
                out.println("retval%s" % comma)
                
            # Now, remaining parameters
            for i,p in enumerate(m.params):
                comma = ""
                if i+1 < len(m.params):
                    comma = ","
                out.println("%s%s" % (p[0], comma))
            out.println(");")
                
            out.dec_ind()
            out.dec_ind()
                
            pass

        out.dec_ind()
        if m.is_blocking:
            out.println("endtask")
        else:
            out.println("endfunction")                        

    def _gen_proxy_if(self, out, iftype, is_mirror):
        
        mirror_s = ""
        if is_mirror:
            mirror_s = "_mirror"
        
        out.println("class %s%s_proxy_if extends tblink_rpc::IInterfaceImplProxy;" % (
            iftype.name, mirror_s))
        out.inc_ind()
        
        # Now, generate base virtual methods all imports
        for m in iftype.methods:
            if not m.is_export and not is_mirror or m.is_export and is_mirror:
                if not m.is_blocking:
                    if m.rtype is None:
                        out.println("virtual function void %s(" % m.name)
                    else:
                        out.println("virtual function %s %s(" % (
                            self._gen_mksvtype(m.rtype), m.name))
                else:
                    out.println("virtual task %s(" % m.name)
                    
                out.inc_ind()
                out.inc_ind()

                # Handle return value for tasks                    
                if m.is_blocking and m.rtype is not None:
                    comma = ""
                    if len(m.params) > 0:
                        comma = ","
                    out.println("output %s retval%s" % (
                        self._gen_mksvtype(m.rtype), comma))
                    
                for i,p in enumerate(m.params):
                    comma = ""
                    if i+1 < len(m.params):
                        comma = ","
                    out.println("input %s %s%s" % (
                        self._gen_mksvtype(p[1]), p[0], comma))
                out.println(");")
                out.dec_ind()
                
                # Now the body...
                
                out.dec_ind()
                if m.is_blocking:
                    out.println("endtask")
                else:
                    out.println("endfunction")
        
        out.dec_ind()
        out.println("endclass")
        
    def _gen_proxy(self, out, iftype, is_mirror):
        
        mirror_s = ""
        if is_mirror:
            mirror_s = "_mirror"
        
        out.println("class %s%s_proxy #(type T=%s_base) extends %s%s_proxy_if;" % (
            iftype.name, mirror_s, iftype.name, iftype.name, mirror_s))
        out.inc_ind()
        out.println("typedef %s_t IfTypeT;" % iftype.name)
        out.println("typedef T ImplT;")
        out.println()
        out.println("tblink_rpc::IInterfaceInst m_ifinst;")
        out.println("ImplT m_impl;")
        
        out.println()
        out.println("// Handles for import methods")
        for m in iftype.methods:
            if not m.is_export and not is_mirror or m.is_export and is_mirror:
                out.println("tblink_rpc::IMethodType m_method_t_%s;" % m.name)
        out.println()
        
        out.println("function new(T impl=null);")
        out.inc_ind()
        out.println("if (impl == null) begin")
        out.inc_ind()
        out.println("m_impl = new();")
        out.dec_ind()
        out.println("end else begin")
        out.inc_ind()
        out.println("m_impl = impl;")
        out.dec_ind()
        out.println("end")
        out.println("m_impl.set_proxy(this);")
        out.dec_ind()
        out.println("endfunction")
        
        out.println()
        
        # Generate the initialization method that looks up method handles
        out.println("virtual function void init(tblink_rpc::IInterfaceInst ifinst);")
        out.inc_ind()
        out.println("tblink_rpc::IInterfaceType iftype = ifinst.iftype();")
        out.println()
        out.println("m_ifinst = ifinst;")
        out.println()
        
        for m in iftype.methods:
            if not m.is_export and not is_mirror or m.is_export and is_mirror:
                out.println("if ((m_method_t_%s=iftype.findMethod(\"%s\")) == null) begin" % (m.name, m.name))
                out.inc_ind()
                if self.is_uvm:
                    out.println("`uvm_fatal(\"%s\", \"Failed to find method '%s'\");" % (iftype.name, m.name))
                else:
                    out.println("$display(\"TbLink Error: Failed to find method '%s::%s'\");" % (iftype.name, m.name))
                    out.println("$finish;")
                out.println("return;")
                out.dec_ind()
                out.println("end")
        out.println()
        out.dec_ind()
        out.println("endfunction")
        
        # Now, generate 'pack' methods for any imports
        for m in iftype.methods:
            if not m.is_export and not is_mirror or m.is_export and is_mirror:
                if not m.is_blocking:
                    if m.rtype is None:
                        out.println("virtual function void %s(" % m.name)
                    else:
                        out.println("virtual function %s %s(" % (
                            self._gen_mksvtype(m.rtype), m.name))
                else:
                    out.println("virtual task %s(" % m.name)
                    
                out.inc_ind()
                out.inc_ind()

                # Handle return value for tasks                    
                if m.is_blocking and m.rtype is not None:
                    comma = ""
                    if len(m.params) > 0:
                        comma = ","
                    out.println("output %s retval%s" % (
                        self._gen_mksvtype(m.rtype), comma))
                    
                for i,p in enumerate(m.params):
                    comma = ""
                    if i+1 < len(m.params):
                        comma = ","
                    out.println("input %s %s%s" % (
                        self._gen_mksvtype(p[1]), p[0], comma))
                out.println(");")
                out.dec_ind()
                
                # Now the body...
                out.println("tblink_rpc::IParamValVec _params = m_ifinst.mkValVec();")
                out.println("tblink_rpc::IParamVal _rv_base;")
                if m.rtype is not None:
                    out.println("%s _rv_tv;" % self._gen_mkvtype(m.rtype))
                    if not m.is_blocking:
                        out.println("%s _rv;" % self._gen_mksvtype(m.rtype))
                        
                out.println()
                        
                # Pack up parameters
                for p in m.params:
                    out.println("_params.push_back(%s);" % self._gen_mkpval("m_ifinst", p[1], p[0]))
                    
                out.println()

                if not m.is_blocking:
                    out.println("_rv_base = m_ifinst.invoke_nb(")
                    out.inc_ind()
                else:
                    out.println("m_ifinst.invoke_b(")
                    out.inc_ind()
                    out.println("_rv_base,")
                
                out.println("m_method_t_%s," % m.name)
                out.println("_params);")
                out.dec_ind()
                
                if m.rtype is not None:
                    out.println()
                    out.println("$cast(_rv_tv, _rv);")
                    val_s = "val"
                    
                    if m.rtype.kind == TypeKind.Int:
                        if m.rtype.is_signed:
                            val_s = "val_s"
                        else:
                            val_s = "val_u"
                    if m.is_blocking:
                        out.println("retval = _rv_tv.%s();" % val_s)
                    else:
                        out.println("_rv = _rv_tv.%s();" % val_s)

                    out.println("_rv_base.dispose();")                        
                    
                    if not m.is_blocking:
                        out.println("return _rv;")
                
                out.dec_ind()
                if m.is_blocking:
                    out.println("endtask")
                else:
                    out.println("endfunction")
        
        out.dec_ind()
        out.println("endclass")
        pass
        
    def _gen_type_factory(self, out : Output, iftype):
        out.println("class %s_t extends tblink_rpc::InterfaceTypeRgy #(" % iftype.name)
        out.inc_ind()
        out.inc_ind()
        out.println("%s_t," % iftype.name)
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
        out.println("tblink_rpc::IInterfaceType iftype = ep.findInterfaceType(name());")
        out.println()
        out.println("if (iftype == null) begin")
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
    
    def _gen_mksvtype(self, t : TypeSpec):
        if t is None:
            return "void"
        elif t.kind == TypeKind.Bool:
            return "bit"
        elif t.kind == TypeKind.Int:
            ret = None
            
            if t.width <= 8:
                ret = "byte"
            elif t.width <= 16:
                ret = "short"
            elif t.width <= 32:
                ret = "int"
            elif t.width <= 64:
                ret = "longint"
            else:
                raise Exception("Wide integer")
            
            if not t.is_signed:
                ret += " unsigned"
                
            return ret
        elif t.kind == TypeKind.Map:
            return "iftype_b.mkTypeMap(%s, %s)" % (
                self._gen_mkptype(t.key_t),
                self._gen_mkptype(t.elem_t))
        elif t.kind == TypeKind.Str:
            return "string"
        elif t.kind == TypeKind.Vec:
            return "iftype_b.mkTypeVec(%s)" % (
                self._gen_mkptype(t.key_t))
        else:
            return "XX"
        
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
    
    def _gen_mkpval(self, base, t : TypeSpec, val):
        if t is None:
            return "null"
        elif t.kind == TypeKind.Bool:
            return "%s.mkValBool(%s)" % (base, val)
        elif t.kind == TypeKind.Int:
            if t.is_signed:
                return "%s.mkValIntS(%s, %d)" % (base, val, t.width)
            else:
                return "%s.mkValIntU(%s, %d)" % (base, val, t.width)
        elif t.kind == TypeKind.Map:
            return "%s.mkValMap()" % base
        elif t.kind == TypeKind.Str:
            return "%s.mkValStr(%s)" % (base, val)
        elif t.kind == TypeKind.Vec:
            return "%s.mkValVec()" % base
        else:
            return "XX"
        pass    
    
    def _gen_mkvtype(self, t : TypeSpec):
        if t is None:
            return "null"
        elif t.kind == TypeKind.Bool:
            return "tblink_rpc::IParamValBool"
        elif t.kind == TypeKind.Int:
            return "tblink_rpc::IParamValInt"
        elif t.kind == TypeKind.Map:
            return "tblink_rpc::IParamValMap"
        elif t.kind == TypeKind.Str:
            return "tblink_rpc::IParamValStr"
        elif t.kind == TypeKind.Vec:
            return "tblink_rpc::IParamValVec"
        else:
            return "XX"
        pass        
    
    def _gen_dfltval(self, t : TypeSpec):
        if t is None:
            return "null"
        elif t.kind == TypeKind.Bool:
            return "0"
        elif t.kind == TypeKind.Int:
            if t.is_signed:
                return "-1"
            else:
                return "0"
        elif t.kind == TypeKind.Map:
            return "{}"
        elif t.kind == TypeKind.Str:
            return "\"\""
        elif t.kind == TypeKind.Vec:
            return "{}"
        else:
            return "XX"
        
    