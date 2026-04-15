import re

import re


def extract_internal_variables(module_content, typedef_names):
    types = r'\b(?:bit|byte|shortint|int|longint|reg|logic|integer|' + '|'.join(typedef_names) + r')\b'
    pattern = r'(?:^|\n)\s*(' + types + r')\s+(?:signed\s+)?(?:unsigned\s+)?([^;]+);'

    matches = re.findall(pattern, module_content, flags=re.DOTALL)

    variables = []
    for data_type, vars_line in matches:
        parts = re.split(r',\s*', vars_line)
        for part in parts:
            part = part.strip()
            if '=' in part:
                part = part.split('=')[0].strip()

            var_name = re.sub(r'\[\s*[^\]]*\s*\]', '', part).strip()

            if var_name and not var_name.startswith('//'):
                variables.append(f"{data_type} {var_name}")

    return variables


def extract_typedef_name(module_content):
    pattern = r'typedef\s+enum\s+logic\s*\[\d+:\d+\]\s*\{[^}]*\}\s*(\w+)\s*;'
    matches = re.findall(pattern, module_content, flags=re.DOTALL)
    return matches


def obtain_internal_variables(module_content):
    pattern1 = r'[a-z]{32}:\s*assert property\s*\(.*?\)\s*else\s*\$error\(".*"\)\s*;?\s*\n?'
    pattern2 = r'property\s+([a-z]{32})\s*;.*?endproperty\s+assert\s+property\s*\(\s*\1\s*\)\s*;'
    pattern3 = r'function\s+\S+\s+(\w+)\s*\([^)]*\)\s*;.*?endfunction'
    pattern4 = r'^\s*module\s+\w+\s*(?:#\s*\([^)]*\)\s*)?(?:\([^)]*\)\s*)?;'

    module_content = re.sub(pattern1, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = re.sub(pattern2, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = re.sub(pattern3, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = re.sub(pattern4, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = module_content.strip()

    typedef_names = extract_typedef_name(module_content)
    internal_variables = extract_internal_variables(module_content=module_content, typedef_names=typedef_names)

    return internal_variables

def extract_ports_and_merge(module_content, internal_variables):
    port_pattern = r'module\s+\w+\s*(?:#\s*\([^)]*\)\s*)?\s*\(\s*(.*?)\s*\)\s*;'

    match = re.search(port_pattern, module_content, flags=re.DOTALL)
    if not match:
        return []

    ports_section = match.group(1)

    port_pattern_detail = r'(input|output|inout)\s+([^,;]+)'
    ports = re.findall(port_pattern_detail, ports_section)

    port_list = []
    for direction, port_decl in ports:
        port_decl = port_decl.strip()
        port_list.append(f"{direction} {port_decl}")

    for var in internal_variables:
        port_list.append(f"input {var}")

    port_arguments = ',\n'.join(port_list)
    return port_arguments


def update_module_header(module_content, port_arguments):
    header_pattern = r'(module\s+\w+\s*(?:#\s*\([^)]*\)\s*)?)\s*\(\s*.*?\s*\)\s*;'
    new_header = f'\\1(\n{port_arguments}\n);'
    updated_content = re.sub(header_pattern, new_header, module_content, flags=re.DOTALL)
    return updated_content


def remove_original_internal_variables(module_content, internal_variables):
    for var in internal_variables:
        data_type, var_name = var.split(' ', 1)

        pattern = r'^\s*' + re.escape(data_type) + r'\s+(?:.*?\b' + re.escape(
            var_name) + r'\b\s*(?:\[[^\]]*\]\s*)?(?:,\s*[^;]*)?\s*;)'
        module_content = re.sub(pattern, '', module_content, flags=re.MULTILINE)

    return module_content


def remove_typedef_declaration(module_content):
    pattern = r'typedef\s+enum\s+logic\s*\[\d+:\d+\]\s*\{[^}]*\}\s*\w+\s*;'
    module_content = re.sub(pattern, '', module_content, flags=re.DOTALL)
    return module_content


def process_module_complete(module_content):
    internal_vars = obtain_internal_variables(module_content)
    port_args = extract_ports_and_merge(module_content, internal_vars)

    updated_module = update_module_header(module_content, port_args)
    updated_module = remove_original_internal_variables(updated_module, internal_vars)
    updated_module = remove_typedef_declaration(updated_module)

    lines = updated_module.split('\n')
    cleaned_lines = [line for line in lines if line.strip()]

    return '\n'.join(cleaned_lines)


# # Test with the provided module (assuming it's in a variable called 'module_text')
# module_text = '''module axi2apb_bridge_asserts  (input logic clk,
# input logic rst_n,
# input logic [31:0] s_axi_awaddr,
# input logic [2:0] s_axi_awprot,
# input logic s_axi_awvalid,
# input logic s_axi_awready,
# input logic [31:0] s_axi_wdata,
# input logic [3:0] s_axi_wstrb,
# input logic s_axi_wvalid,
# input logic s_axi_wready,
# input logic [1:0] s_axi_bresp,
# input logic s_axi_bvalid,
# input logic s_axi_bready,
# input logic [31:0] s_axi_araddr,
# input logic [2:0] s_axi_arprot,
# input logic s_axi_arvalid,
# input logic s_axi_arready,
# input logic [31:0] s_axi_rdata,
# input logic [1:0] s_axi_rresp,
# input logic s_axi_rvalid,
# input logic s_axi_rready,
# input logic [31:0] m_apb_paddr,
# input logic m_apb_psel,
# input logic m_apb_penable,
# input logic m_apb_pwrite,
# input logic [31:0] m_apb_pwdata,
# input logic [31:0] m_apb_prdata,
# input logic m_apb_pready,
# input logic m_apb_pslverr);
#
#     typedef enum logic [1:0] {
#         IDLE,
#         SETUP,
#         ACCESS,
#         RESPONSE
#     } state_t;
#
#     state_t current_state, next_state;
#     logic [31:0] addr_reg;
#     logic write_reg;
#     logic is_write, is_read;
#     logic aw_hsk, w_hsk, ar_hsk;
#
#
#
# dffdmdeaondckkicbmhjdakdkjdljdpa: assert property (@(s_axi_awvalid, current_state) {s_axi_awvalid && current_state == IDLE} |-> s_axi_awready == 1'b1) else $error("Error in immediate assert dffdmdeaondckkicbmhjdakdkjdljdpa");
# abkjbiehpgggkbfgpihjldfghanbgbfj: assert property (@(current_state, s_axi_wvalid) {s_axi_wvalid && current_state == SETUP} |-> s_axi_wready == 1'b1) else $error("Error in immediate assert abkjbiehpgggkbfgpihjldfghanbgbfj");
# fobofbnnlmjpkelfogaegieajjkjddbd: assert property (@(s_axi_arvalid, current_state) {s_axi_arvalid && current_state == IDLE} |-> s_axi_arready == 1'b1) else $error("Error in immediate assert fobofbnnlmjpkelfogaegieajjkjddbd");
# elfppdconmiakhkfbfhkfcndmngihoic: assert property (@(s_axi_awvalid, current_state) {s_axi_awvalid && current_state == ACCESS} |-> is_write == 1'b1) else $error("Error in immediate assert elfppdconmiakhkfbfhkfcndmngihoic");
# oocoidgbidoikalhagiafjhcbfopbdol: assert property (@(s_axi_arvalid, current_state) {s_axi_arvalid && current_state == ACCESS} |-> is_read == 1'b1) else $error("Error in immediate assert oocoidgbidoikalhagiafjhcbfopbdol");
# jlgllciooeekkhnibkkgelpakpmbgnnf: assert property (@(m_apb_pready, current_state) {!m_apb_pready && current_state == ACCESS} |-> next_state == ACCESS) else $error("Error in immediate assert jlgllciooeekkhnibkkgelpakpmbgnnf");
# lmlphmjocifgkokcpbhllppifolijbli: assert property (@(is_write, s_axi_rready, s_axi_bready, current_state, is_read) {is_write && s_axi_bready || is_read && s_axi_rready && current_state == RESPONSE} |-> next_state == IDLE) else $error("Error in immediate assert lmlphmjocifgkokcpbhllppifolijbli");
#
# clidkjnmglldkfaibpcekcgkhcgbafmi: assert property (@(is_write, current_state) current_state == SETUP && is_write |-> s_axi_awready == 1'b1) else $error("Error in immediate assert clidkjnmglldkfaibpcekcgkhcgbafmi");
# pmohjjnkkiddkmcfbglpfjpfkhfhcdik: assert property (@(is_write, current_state) current_state == ACCESS && is_write |-> s_axi_wready == 1'b1) else $error("Error in immediate assert pmohjjnkkiddkmcfbglpfjpfkhfhcdik");
# mpfkldocidkakjmbpnjhlpfabbnknmlg: assert property (@(is_write, current_state) current_state == RESPONSE && is_write |-> s_axi_bresp == 2'b00) else $error("Error in immediate assert mpfkldocidkakjmbpnjhlpfabbnknmlg");
# acgpjdkpgegbkfohbhimgfcddnfcigpa: assert property (@(is_write, current_state) current_state == RESPONSE && is_write |-> s_axi_bvalid == 1'b1) else $error("Error in immediate assert acgpjdkpgegbkfohbhimgfcddnfcigpa");
# bnodigcjoaegkkceaefpaicldachjljn: assert property (@(is_read, current_state) current_state == SETUP && is_read |-> s_axi_arready == 1'b1) else $error("Error in immediate assert bnodigcjoaegkkceaefpaicldachjljn");
# fkppapjjjojhkmbkplnibbhohjepofdk: assert property (@(is_read, current_state, m_apb_prdata) current_state == RESPONSE && is_read |-> s_axi_rdata == m_apb_prdata) else $error("Error in immediate assert fkppapjjjojhkmbkplnibbhohjepofdk");
# lnielajpmamgkeobamlhdcggdhbpahpk: assert property (@(is_read, current_state) current_state == RESPONSE && is_read |-> s_axi_rresp == 2'b00) else $error("Error in immediate assert lnielajpmamgkeobamlhdcggdhbpahpk");
# edgkjiagckfhkjnoblgkibgckkihojka: assert property (@(is_read, current_state) current_state == RESPONSE && is_read |-> s_axi_rvalid == 1'b1) else $error("Error in immediate assert edgkjiagckfhkjnoblgkibgckkihojka");
#
# degjmdogdklekhbnoahdedkieagfplke: assert property (@(current_state) current_state == IDLE |-> s_axi_awready == 1'b1) else $error("Error in immediate assert degjmdogdklekhbnoahdedkieagfplke");
# lpcjafccdcfiknemooaknbopnbfhbgah: assert property (@(current_state) current_state == IDLE |-> s_axi_wready == 1'b1) else $error("Error in immediate assert lpcjafccdcfiknemooaknbopnbfhbgah");
# aehekdbmlckokplpocbmpgndkfinpdnl: assert property (@(current_state) current_state == IDLE |-> s_axi_arready == 1'b1) else $error("Error in immediate assert aehekdbmlckokplpocbmpgndkfinpdnl");
# eifofbmalkfgkccdblkelobjbblcdakf: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b1 |-> s_axi_bvalid == 1'b1) else $error("Error in immediate assert eifofbmalkfgkccdblkelobjbblcdakf");
# eececjfbckickgcjpifgbimblmikmooa: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b1 && m_apb_pslverr == 1'b1 |-> s_axi_bresp == 2'b10) else $error("Error in immediate assert eececjfbckickgcjpifgbimblmikmooa");
# popdimiogjglkhhnpdbkcebljlibdfhf: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b1 && m_apb_pslverr != 1'b1 |-> s_axi_bresp == 2'b00) else $error("Error in immediate assert popdimiogjglkhhnpdbkcebljlibdfhf");
# eaodanfohjilkhpoagaeockkkeofggmp: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b0 |-> s_axi_rvalid == 1'b1) else $error("Error in immediate assert eaodanfohjilkhpoagaeockkkeofggmp");
# lcfplinlccnbkbepokphkaofifhjjkkf: assert property (@(is_write, current_state, m_apb_prdata) current_state == RESPONSE && is_write == 1'b0 |-> s_axi_rdata == m_apb_prdata) else $error("Error in immediate assert lcfplinlccnbkbepokphkaofifhjjkkf");
# gbcojaombokbklmkacjlnjhpnmnkbgfo: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b0 && m_apb_pslverr == 1'b1 |-> s_axi_rresp == 2'b10) else $error("Error in immediate assert gbcojaombokbklmkacjlnjhpnmnkbgfo");
# jahbjldheadakbafbgbjncfcbjgjdpdc: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b0 && m_apb_pslverr != 1'b1 |-> s_axi_rresp == 2'b00) else $error("Error in immediate assert jahbjldheadakbafbgbjncfcbjgjdpdc");
#
#
#     property hegddcpjibnakbmcapdfejgfapbohiae;
#     @(posedge clk) disable iff(!rst_n) (current_state == IDLE) |=> (s_axi_awready == 1);
# endproperty
# assert property (hegddcpjibnakbmcapdfejgfapbohiae);
#
# property fkhibdeimfhokgncamjgiefdknddgked;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (s_axi_awready == 0);
# endproperty
# assert property (fkhibdeimfhokgncamjgiefdknddgked);
#
# property jcocllpmglcdkanoaijjjafhheepekge;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && is_write) |=> (s_axi_wready == 1);
# endproperty
# assert property (jcocllpmglcdkanoaijjjafhheepekge);
#
# property chmfpickakhkkoiapgoikjdmogkpfkjg;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (s_axi_wready == 0);
# endproperty
# assert property (chmfpickakhkkoiapgoikjdmogkpfkjg);
#
# property ebohcacjoompkapmaeocnjaagpmnpbon;
#     @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_bresp == 2'b00);
# endproperty
# assert property (ebohcacjoompkapmaeocnjaagpmnpbon);
#
# property chkomlgmgpbgkogeppeckobbcnlmfieo;
#     @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_bvalid == 1);
# endproperty
# assert property (chkomlgmgpbgkogeppeckobbcnlmfieo);
#
# property ppeejebknccckggiokkemhhegolmddib;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP && is_write) |=> (m_apb_paddr == addr_reg);
# endproperty
# assert property (ppeejebknccckggiokkemhhegolmddib);
#
# property nkokpbpbhjcckjgebodicgjpdajokeep;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP && is_write) |=> (m_apb_psel == 1);
# endproperty
# assert property (nkokpbpbhjcckjgebodicgjpdajokeep);
#
# property lbpmcmppmabfkcpooejifeohjicagpkb;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS) |=> (m_apb_penable == 1);
# endproperty
# assert property (lbpmcmppmabfkcpooejifeohjicagpkb);
#
# property kecbkmokfmfckpgbbpdanbdjmcadhijb;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && is_write) |=> (m_apb_pwrite == 1);
# endproperty
# assert property (kecbkmokfmfckpgbbpdanbdjmcadhijb);
#
# property kidhhagcbenjkddipigkdfpdbdfbeadm;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && is_write) |=> (m_apb_pwdata == s_axi_wdata);
# endproperty
# assert property (kidhhagcbenjkddipigkdfpdbdfbeadm);
#
# property empffkjccnmnkhjebndhijbelknjkpok;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && !is_write) |=> (m_apb_prdata == s_axi_rdata);
# endproperty
# assert property (empffkjccnmnkhjebndhijbelknjkpok);
#
# property jbfcpgoidhahkjiipjomgnggpdggmjbd;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS) |=> (m_apb_pready == 1);
# endproperty
# assert property (jbfcpgoidhahkjiipjomgnggpdggmjbd);
#
# property jipboikcdlgnkpjbbbmdiflnaecfdnbo;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && !is_write) |=> (m_apb_pslverr == 0);
# endproperty
# assert property (jipboikcdlgnkpjbbbmdiflnaecfdnbo);
#
# property nbfoihpikmagklhcpingkckahlfpbbfo;
#     @(posedge clk) disable iff(!rst_n) (current_state == IDLE && is_read) |=> (s_axi_arready == 1);
# endproperty
# assert property (nbfoihpikmagklhcpingkckahlfpbbfo);
#
# property bmbjnbjlkenjkfaiblllhhedmkncolne;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (s_axi_arready == 0);
# endproperty
# assert property (bmbjnbjlkenjkfaiblllhhedmkncolne);
#
# property leknbomldfcekeaapmdemolfegiejioi;
#     @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_rdata == m_apb_prdata);
# endproperty
# assert property (leknbomldfcekeaapmdemolfegiejioi);
#
# property bkcfhpdgoglbkldpabphbhbgmgjpompm;
#     @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_rvalid == 1);
# endproperty
# assert property (bkcfhpdgoglbkldpabphbhbgmgjpompm);
#
# property immhpjcjnpnpkapjoogjhjcddcklakdm;
#     @(posedge clk) disable iff(!rst_n) (current_state == IDLE && s_axi_awvalid && s_axi_wvalid) |=> (next_state == SETUP);
# endproperty
# assert property (immhpjcjnpnpkapjoogjhjcddcklakdm);
#
# property hedgbecpocgaklonbjiljfgmjikphdao;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP && !s_axi_bready) |=> (next_state == ACCESS);
# endproperty
# assert property (hedgbecpocgaklonbjiljfgmjikphdao);
#
# property jjgamfckimbikehfafkiemifndnkmdob;
#     @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && m_apb_pready) |=> (next_state == RESPONSE);
# endproperty
# assert property (jjgamfckimbikehfafkiemifndnkmdob);
#
# property miahaonlapcmkocjpdmjhmljmikobaal;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (addr_reg == s_axi_awaddr);
# endproperty
# assert property (miahaonlapcmkocjpdmjhmljmikobaal);
#
# property dfefejigoofekpampffkojefjkicccon;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (write_reg == s_axi_wvalid);
# endproperty
# assert property (dfefejigoofekpampffkojefjkicccon);
#
# property lommefckhlfdkgpcpibckdmbfdabnafp;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (is_write == (s_axi_awaddr[31:20] == 12'h0) ? s_axi_wvalid : 0);
# endproperty
# assert property (lommefckhlfdkgpcpibckdmbfdabnafp);
#
# property jenciaidjhaekgcgaflblgajophclbgo;
#     @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (is_read == !s_axi_wvalid);
# endproperty
# assert property (jenciaidjhaekgcgaflblgajophclbgo);
#
#
#
# endmodule'''
#
# print(process_module_complete(module_content=module_text))
# # new_ports = extract_ports_and_merge(module_content=module_text, internal_variables=obtain_internal_variables(module_text))
# # new_module = update_module_header(module_content=module_text, port_arguments=new_ports)
# # print(new_module)