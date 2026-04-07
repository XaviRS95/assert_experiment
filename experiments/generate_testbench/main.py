from module_generator import generate_testbench
import pandas as pd
from update_assert_module import process_module_complete
from config import arguments
import requests, time, glob, os

def filter_dataset(filepath: str):
    '''

    :param filepath:
    :return:
    '''
    file_data = pd.read_csv(filepath)
    file_data = file_data[file_data['iverilog_output'] == 'OK']
    file_data = file_data.reset_index(drop=True)
    return file_data[['original_code','generated_code']]

def try_testbench(dut_module: str, assert_module:str, testbench_module:str, host:str = 'http://localhost:8002')-> dict:
    '''

    :param dut_module:
    :param assert_module:
    :param testbench_module:
    :param host:
    :return:
    '''
    url = f"{host}/api/testbench_testing"

    payload = {
        "dut": dut_module,
        "asserts": assert_module,
        "testbench": testbench_module
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()

    return data


# --- Assuming these helper functions exist in your environment ---
# from your_module import arguments, generate_testbench, try_testbench

def run_coverage_analysis(file_data):
    """
    Refactored version of your main() logic to process a specific DataFrame slice.
    """
    if file_data.empty:
        return 0.0

    TIMESCALE = '`timescale 1ns/1ns'
    CLK_HALF_PERIOD = 5
    RESET_DELAY = 30
    TIMEOUT_LIMIT = 20000
    COMB_TOTAL_TESTS = 100
    SEQ_TOTAL_TESTS = 100
    POST_COMPLETION_DELAY = 100

    average_coverage = 0

    for index, row in file_data.iterrows():
        # Using the logic from your provided main()
        #dut_module = row['original_code']
        #assert_module = row['generated_code']

        dut_module = '''module axi2apb_bridge (
    input  logic        clk,
    input  logic        rst_n,

    // AXI4-Lite Slave Interface
    input  logic [31:0] s_axi_awaddr,
    input  logic [2:0]  s_axi_awprot,
    input  logic        s_axi_awvalid,
    output logic        s_axi_awready,

    input  logic [31:0] s_axi_wdata,
    input  logic [3:0]  s_axi_wstrb,
    input  logic        s_axi_wvalid,
    output logic        s_axi_wready,

    output logic [1:0]  s_axi_bresp,
    output logic        s_axi_bvalid,
    input  logic        s_axi_bready,

    input  logic [31:0] s_axi_araddr,
    input  logic [2:0]  s_axi_arprot,
    input  logic        s_axi_arvalid,
    output logic        s_axi_arready,

    output logic [31:0] s_axi_rdata,
    output logic [1:0]  s_axi_rresp,
    output logic        s_axi_rvalid,
    input  logic        s_axi_rready,

    // APB Master Interface
    output logic [31:0] m_apb_paddr,
    output logic        m_apb_psel,
    output logic        m_apb_penable,
    output logic        m_apb_pwrite,
    output logic [31:0] m_apb_pwdata,
    input  logic [31:0] m_apb_prdata,
    input  logic        m_apb_pready,
    input  logic        m_apb_pslverr
);

	// State encoding
    typedef enum logic [1:0] {
        IDLE,
        SETUP,
        ACCESS,
        RESPONSE
    } state_t;

    // Signal declarations
    state_t current_state, next_state;
    logic [31:0] addr_reg;
    logic write_reg;
    logic is_write, is_read;
    logic aw_hsk, w_hsk, ar_hsk;

    // Block 1: State Machine Sequential Logic
    always_ff @(posedge clk or negedge rst_n) begin
        case (rst_n)
            1'b0: current_state <= IDLE;
            1'b1: current_state <= next_state;
        endcase
    end

    // Block 2: Address and Control Register
    always_ff @(posedge clk or negedge rst_n) begin
        case (rst_n)
            1'b0: begin
                addr_reg <= 32'b0;
                write_reg <= 1'b0;
            end
            1'b1: begin
                case (current_state)
                    IDLE: begin
                        case ({s_axi_awvalid, s_axi_arvalid})
                            2'b10, 2'b11: begin
                                addr_reg <= s_axi_awaddr;
                                write_reg <= 1'b1;
                            end
                            2'b01: begin
                                addr_reg <= s_axi_araddr;
                                write_reg <= 1'b0;
                            end
                            default: begin
                                addr_reg <= addr_reg;
                                write_reg <= write_reg;
                            end
                        endcase
                    end
                    default: begin
                        addr_reg <= addr_reg;
                        write_reg <= write_reg;
                    end
                endcase
            end
        endcase
    end

    // Block 3: Combinational Logic (All case statements, no assign)
    always_comb begin
        // Default values
        next_state = current_state;
        is_write = 1'b0;
        is_read = 1'b0;
        aw_hsk = 1'b0;
        w_hsk = 1'b0;
        ar_hsk = 1'b0;

        // Calculate handshake signals using case
        case ({s_axi_awvalid, s_axi_awready})
            2'b11: aw_hsk = 1'b1;
            default: aw_hsk = 1'b0;
        endcase

        case ({s_axi_wvalid, s_axi_wready})
            2'b11: w_hsk = 1'b1;
            default: w_hsk = 1'b0;
        endcase

        case ({s_axi_arvalid, s_axi_arready})
            2'b11: ar_hsk = 1'b1;
            default: ar_hsk = 1'b0;
        endcase

        // Calculate is_write and is_read
        case ({s_axi_awvalid, current_state == ACCESS})
            2'b10, 2'b11, 2'b01: is_write = 1'b1;
            default: is_write = 1'b0;
        endcase

        case ({s_axi_arvalid, current_state == ACCESS})
            2'b10, 2'b11, 2'b01: is_read = 1'b1;
            default: is_read = 1'b0;
        endcase

        // State transition logic
        case (current_state)
            IDLE: begin
                case ({s_axi_awvalid, s_axi_arvalid})
                    2'b10, 2'b11: next_state = SETUP;
                    2'b01:        next_state = SETUP;
                    default:      next_state = IDLE;
                endcase
            end

            SETUP: begin
                case (m_apb_pready)
                    1'b1: next_state = ACCESS;
                    default: next_state = SETUP;
                endcase
            end

            ACCESS: begin
                case (m_apb_pready)
                    1'b1: next_state = RESPONSE;
                    default: next_state = ACCESS;
                endcase
            end

            RESPONSE: begin
                case ({is_write && s_axi_bready, is_read && s_axi_rready})
                    2'b10, 2'b11, 2'b01: next_state = IDLE;
                    default: next_state = RESPONSE;
                endcase
            end
        endcase
    end

    // Block 4: APB Control Logic
    always_comb begin
        m_apb_paddr = 32'b0;
        m_apb_psel = 1'b0;
        m_apb_penable = 1'b0;
        m_apb_pwrite = 1'b0;
        m_apb_pwdata = 32'b0;

        case (current_state)
            SETUP, ACCESS: begin
                m_apb_psel = 1'b1;
                m_apb_paddr = addr_reg;
                m_apb_pwrite = write_reg;
                m_apb_pwdata = s_axi_wdata;
                case (current_state)
                    ACCESS: m_apb_penable = 1'b1;
                    default: m_apb_penable = 1'b0;
                endcase
            end
        endcase
    end

    // Block 5: AXI Handshake Logic
    always_comb begin
        s_axi_awready = 1'b0;
        s_axi_wready  = 1'b0;
        s_axi_arready = 1'b0;
        s_axi_bvalid  = 1'b0;
        s_axi_rvalid  = 1'b0;
        s_axi_bresp   = 2'b00;
        s_axi_rresp   = 2'b00;
        s_axi_rdata   = 32'b0;

        case (current_state)
            IDLE: begin
                s_axi_awready = 1'b1;
                s_axi_wready  = 1'b1;
                s_axi_arready = 1'b1;
            end

            RESPONSE: begin
                case (is_write)
                    1'b1: begin
                        s_axi_bvalid = 1'b1;
                        case (m_apb_pslverr)
                            1'b1: s_axi_bresp = 2'b10;
                            default: s_axi_bresp = 2'b00;
                        endcase
                    end
                    1'b0: begin
                        s_axi_rvalid = 1'b1;
                        s_axi_rdata  = m_apb_prdata;
                        case (m_apb_pslverr)
                            1'b1: s_axi_rresp = 2'b10;
                            default: s_axi_rresp = 2'b00;
                        endcase
                    end
                endcase
            end
        endcase
    end

endmodule'''
        assert_module = '''module axi2apb_bridge_asserts  (input logic clk,
input logic rst_n,
input logic [31:0] s_axi_awaddr,
input logic [2:0] s_axi_awprot,
input logic s_axi_awvalid,
input logic s_axi_awready,
input logic [31:0] s_axi_wdata,
input logic [3:0] s_axi_wstrb,
input logic s_axi_wvalid,
input logic s_axi_wready,
input logic [1:0] s_axi_bresp,
input logic s_axi_bvalid,
input logic s_axi_bready,
input logic [31:0] s_axi_araddr,
input logic [2:0] s_axi_arprot,
input logic s_axi_arvalid,
input logic s_axi_arready,
input logic [31:0] s_axi_rdata,
input logic [1:0] s_axi_rresp,
input logic s_axi_rvalid,
input logic s_axi_rready,
input logic [31:0] m_apb_paddr,
input logic m_apb_psel,
input logic m_apb_penable,
input logic m_apb_pwrite,
input logic [31:0] m_apb_pwdata,
input logic [31:0] m_apb_prdata,
input logic m_apb_pready,
input logic m_apb_pslverr);

    typedef enum logic [1:0] {
        IDLE,
        SETUP,
        ACCESS,
        RESPONSE
    } state_t;

        state_t current_state, next_state;
    logic [31:0] addr_reg;
    logic write_reg;
    logic is_write, is_read;
    logic aw_hsk, w_hsk, ar_hsk;

    

    dffdmdeaondckkicbmhjdakdkjdljdpa: assert property (@(s_axi_awvalid, current_state) {s_axi_awvalid && current_state == IDLE} |-> s_axi_awready == 1'b1) else $error("Error in immediate assert dffdmdeaondckkicbmhjdakdkjdljdpa");
abkjbiehpgggkbfgpihjldfghanbgbfj: assert property (@(current_state, s_axi_wvalid) {s_axi_wvalid && current_state == SETUP} |-> s_axi_wready == 1'b1) else $error("Error in immediate assert abkjbiehpgggkbfgpihjldfghanbgbfj");
fobofbnnlmjpkelfogaegieajjkjddbd: assert property (@(s_axi_arvalid, current_state) {s_axi_arvalid && current_state == IDLE} |-> s_axi_arready == 1'b1) else $error("Error in immediate assert fobofbnnlmjpkelfogaegieajjkjddbd");
elfppdconmiakhkfbfhkfcndmngihoic: assert property (@(s_axi_awvalid, current_state) {s_axi_awvalid && current_state == ACCESS} |-> is_write == 1'b1) else $error("Error in immediate assert elfppdconmiakhkfbfhkfcndmngihoic");
oocoidgbidoikalhagiafjhcbfopbdol: assert property (@(s_axi_arvalid, current_state) {s_axi_arvalid && current_state == ACCESS} |-> is_read == 1'b1) else $error("Error in immediate assert oocoidgbidoikalhagiafjhcbfopbdol");
jlgllciooeekkhnibkkgelpakpmbgnnf: assert property (@(m_apb_pready, current_state) {!m_apb_pready && current_state == ACCESS} |-> next_state == ACCESS) else $error("Error in immediate assert jlgllciooeekkhnibkkgelpakpmbgnnf");
lmlphmjocifgkokcpbhllppifolijbli: assert property (@(is_write, s_axi_rready, s_axi_bready, current_state, is_read) {is_write && s_axi_bready || is_read && s_axi_rready && current_state == RESPONSE} |-> next_state == IDLE) else $error("Error in immediate assert lmlphmjocifgkokcpbhllppifolijbli");

clidkjnmglldkfaibpcekcgkhcgbafmi: assert property (@(is_write, current_state) current_state == SETUP && is_write |-> s_axi_awready == 1'b1) else $error("Error in immediate assert clidkjnmglldkfaibpcekcgkhcgbafmi");
pmohjjnkkiddkmcfbglpfjpfkhfhcdik: assert property (@(is_write, current_state) current_state == ACCESS && is_write |-> s_axi_wready == 1'b1) else $error("Error in immediate assert pmohjjnkkiddkmcfbglpfjpfkhfhcdik");
mpfkldocidkakjmbpnjhlpfabbnknmlg: assert property (@(is_write, current_state) current_state == RESPONSE && is_write |-> s_axi_bresp == 2'b00) else $error("Error in immediate assert mpfkldocidkakjmbpnjhlpfabbnknmlg");
acgpjdkpgegbkfohbhimgfcddnfcigpa: assert property (@(is_write, current_state) current_state == RESPONSE && is_write |-> s_axi_bvalid == 1'b1) else $error("Error in immediate assert acgpjdkpgegbkfohbhimgfcddnfcigpa");
bnodigcjoaegkkceaefpaicldachjljn: assert property (@(is_read, current_state) current_state == SETUP && is_read |-> s_axi_arready == 1'b1) else $error("Error in immediate assert bnodigcjoaegkkceaefpaicldachjljn");
fkppapjjjojhkmbkplnibbhohjepofdk: assert property (@(is_read, current_state, m_apb_prdata) current_state == RESPONSE && is_read |-> s_axi_rdata == m_apb_prdata) else $error("Error in immediate assert fkppapjjjojhkmbkplnibbhohjepofdk");
lnielajpmamgkeobamlhdcggdhbpahpk: assert property (@(is_read, current_state) current_state == RESPONSE && is_read |-> s_axi_rresp == 2'b00) else $error("Error in immediate assert lnielajpmamgkeobamlhdcggdhbpahpk");
edgkjiagckfhkjnoblgkibgckkihojka: assert property (@(is_read, current_state) current_state == RESPONSE && is_read |-> s_axi_rvalid == 1'b1) else $error("Error in immediate assert edgkjiagckfhkjnoblgkibgckkihojka");

degjmdogdklekhbnoahdedkieagfplke: assert property (@(current_state) current_state == IDLE |-> s_axi_awready == 1'b1) else $error("Error in immediate assert degjmdogdklekhbnoahdedkieagfplke");
lpcjafccdcfiknemooaknbopnbfhbgah: assert property (@(current_state) current_state == IDLE |-> s_axi_wready == 1'b1) else $error("Error in immediate assert lpcjafccdcfiknemooaknbopnbfhbgah");
aehekdbmlckokplpocbmpgndkfinpdnl: assert property (@(current_state) current_state == IDLE |-> s_axi_arready == 1'b1) else $error("Error in immediate assert aehekdbmlckokplpocbmpgndkfinpdnl");
eifofbmalkfgkccdblkelobjbblcdakf: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b1 |-> s_axi_bvalid == 1'b1) else $error("Error in immediate assert eifofbmalkfgkccdblkelobjbblcdakf");
eececjfbckickgcjpifgbimblmikmooa: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b1 && m_apb_pslverr == 1'b1 |-> s_axi_bresp == 2'b10) else $error("Error in immediate assert eececjfbckickgcjpifgbimblmikmooa");
popdimiogjglkhhnpdbkcebljlibdfhf: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b1 && m_apb_pslverr != 1'b1 |-> s_axi_bresp == 2'b00) else $error("Error in immediate assert popdimiogjglkhhnpdbkcebljlibdfhf");
eaodanfohjilkhpoagaeockkkeofggmp: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b0 |-> s_axi_rvalid == 1'b1) else $error("Error in immediate assert eaodanfohjilkhpoagaeockkkeofggmp");
lcfplinlccnbkbepokphkaofifhjjkkf: assert property (@(is_write, current_state, m_apb_prdata) current_state == RESPONSE && is_write == 1'b0 |-> s_axi_rdata == m_apb_prdata) else $error("Error in immediate assert lcfplinlccnbkbepokphkaofifhjjkkf");
gbcojaombokbklmkacjlnjhpnmnkbgfo: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b0 && m_apb_pslverr == 1'b1 |-> s_axi_rresp == 2'b10) else $error("Error in immediate assert gbcojaombokbklmkacjlnjhpnmnkbgfo");
jahbjldheadakbafbgbjncfcbjgjdpdc: assert property (@(is_write, current_state) current_state == RESPONSE && is_write == 1'b0 && m_apb_pslverr != 1'b1 |-> s_axi_rresp == 2'b00) else $error("Error in immediate assert jahbjldheadakbafbgbjncfcbjgjdpdc");


    property hegddcpjibnakbmcapdfejgfapbohiae;
    @(posedge clk) disable iff(!rst_n) (current_state == IDLE) |=> (s_axi_awready == 1);
endproperty
assert property (hegddcpjibnakbmcapdfejgfapbohiae);

property fkhibdeimfhokgncamjgiefdknddgked;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (s_axi_awready == 0);
endproperty
assert property (fkhibdeimfhokgncamjgiefdknddgked);

property jcocllpmglcdkanoaijjjafhheepekge;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && is_write) |=> (s_axi_wready == 1);
endproperty
assert property (jcocllpmglcdkanoaijjjafhheepekge);

property chmfpickakhkkoiapgoikjdmogkpfkjg;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (s_axi_wready == 0);
endproperty
assert property (chmfpickakhkkoiapgoikjdmogkpfkjg);

property ebohcacjoompkapmaeocnjaagpmnpbon;
    @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_bresp == 2'b00);
endproperty
assert property (ebohcacjoompkapmaeocnjaagpmnpbon);

property chkomlgmgpbgkogeppeckobbcnlmfieo;
    @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_bvalid == 1);
endproperty
assert property (chkomlgmgpbgkogeppeckobbcnlmfieo);

property ppeejebknccckggiokkemhhegolmddib;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP && is_write) |=> (m_apb_paddr == addr_reg);
endproperty
assert property (ppeejebknccckggiokkemhhegolmddib);

property nkokpbpbhjcckjgebodicgjpdajokeep;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP && is_write) |=> (m_apb_psel == 1);
endproperty
assert property (nkokpbpbhjcckjgebodicgjpdajokeep);

property lbpmcmppmabfkcpooejifeohjicagpkb;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS) |=> (m_apb_penable == 1);
endproperty
assert property (lbpmcmppmabfkcpooejifeohjicagpkb);

property kecbkmokfmfckpgbbpdanbdjmcadhijb;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && is_write) |=> (m_apb_pwrite == 1);
endproperty
assert property (kecbkmokfmfckpgbbpdanbdjmcadhijb);

property kidhhagcbenjkddipigkdfpdbdfbeadm;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && is_write) |=> (m_apb_pwdata == s_axi_wdata);
endproperty
assert property (kidhhagcbenjkddipigkdfpdbdfbeadm);

property empffkjccnmnkhjebndhijbelknjkpok;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && !is_write) |=> (m_apb_prdata == s_axi_rdata);
endproperty
assert property (empffkjccnmnkhjebndhijbelknjkpok);

property jbfcpgoidhahkjiipjomgnggpdggmjbd;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS) |=> (m_apb_pready == 1);
endproperty
assert property (jbfcpgoidhahkjiipjomgnggpdggmjbd);

property jipboikcdlgnkpjbbbmdiflnaecfdnbo;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && !is_write) |=> (m_apb_pslverr == 0);
endproperty
assert property (jipboikcdlgnkpjbbbmdiflnaecfdnbo);

property nbfoihpikmagklhcpingkckahlfpbbfo;
    @(posedge clk) disable iff(!rst_n) (current_state == IDLE && is_read) |=> (s_axi_arready == 1);
endproperty
assert property (nbfoihpikmagklhcpingkckahlfpbbfo);

property bmbjnbjlkenjkfaiblllhhedmkncolne;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (s_axi_arready == 0);
endproperty
assert property (bmbjnbjlkenjkfaiblllhhedmkncolne);

property leknbomldfcekeaapmdemolfegiejioi;
    @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_rdata == m_apb_prdata);
endproperty
assert property (leknbomldfcekeaapmdemolfegiejioi);

property bkcfhpdgoglbkldpabphbhbgmgjpompm;
    @(posedge clk) disable iff(!rst_n) (current_state == RESPONSE) |=> (s_axi_rvalid == 1);
endproperty
assert property (bkcfhpdgoglbkldpabphbhbgmgjpompm);

property immhpjcjnpnpkapjoogjhjcddcklakdm;
    @(posedge clk) disable iff(!rst_n) (current_state == IDLE && s_axi_awvalid && s_axi_wvalid) |=> (next_state == SETUP);
endproperty
assert property (immhpjcjnpnpkapjoogjhjcddcklakdm);

property hedgbecpocgaklonbjiljfgmjikphdao;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP && !s_axi_bready) |=> (next_state == ACCESS);
endproperty
assert property (hedgbecpocgaklonbjiljfgmjikphdao);

property jjgamfckimbikehfafkiemifndnkmdob;
    @(posedge clk) disable iff(!rst_n) (current_state == ACCESS && m_apb_pready) |=> (next_state == RESPONSE);
endproperty
assert property (jjgamfckimbikehfafkiemifndnkmdob);

property miahaonlapcmkocjpdmjhmljmikobaal;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (addr_reg == s_axi_awaddr);
endproperty
assert property (miahaonlapcmkocjpdmjhmljmikobaal);

property dfefejigoofekpampffkojefjkicccon;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (write_reg == s_axi_wvalid);
endproperty
assert property (dfefejigoofekpampffkojefjkicccon);

property lommefckhlfdkgpcpibckdmbfdabnafp;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (is_write == (s_axi_awaddr[31:20] == 12'h0) ? s_axi_wvalid : 0);
endproperty
assert property (lommefckhlfdkgpcpibckdmbfdabnafp);

property jenciaidjhaekgcgaflblgajophclbgo;
    @(posedge clk) disable iff(!rst_n) (current_state == SETUP) |=> (is_read == !s_axi_wvalid);
endproperty
assert property (jenciaidjhaekgcgaflblgajophclbgo);



endmodule'''

        assert_module = process_module_complete(module_content=assert_module)

        testbench_module = generate_testbench(
            timescale=TIMESCALE,
            dut_module=dut_module,
            assert_module=assert_module,
            CLK_HALF_PERIOD=CLK_HALF_PERIOD,
            RESET_DELAY=RESET_DELAY,
            TIMEOUT_LIMIT=TIMEOUT_LIMIT,
            COMB_TOTAL_TESTS=COMB_TOTAL_TESTS,
            SEQ_TOTAL_TESTS=SEQ_TOTAL_TESTS,
            POST_COMPLETION_DELAY=POST_COMPLETION_DELAY
        )

        testbench_test_results = try_testbench(
            dut_module=dut_module,
            assert_module=assert_module,
            testbench_module=testbench_module
        )

        average_coverage += testbench_test_results.get('coverage_pct', 0)

    return average_coverage / len(file_data)


def process_directory(directory_path):
    # Search for all CSV files in the directory
    csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
    print(f'Found files: {csv_files}')
    for filepath in csv_files:
        llm_name = os.path.basename(filepath).replace(".csv", "")
        print(f"\n{'=' * 60}\nPROCESSING LLM: {llm_name}\n{'=' * 60}")

        try:
            data = pd.read_csv(filepath)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue

        # Define the subsections
        subsections = {
            "combinational_basic": data.iloc[0:80],
            "sequential_basic": data.iloc[80:160],
            "fsm": data.iloc[160:190],
            "industry": data.iloc[-10:]
        }

        for sub_name, df_slice in subsections.items():
            # Filter: only rows where iverilog_output is "OK"
            filtered_df = df_slice[df_slice['iverilog_output'] == "OK"].copy()

            if filtered_df.empty:
                print(f"[{sub_name}] No 'OK' results found. Skipping.")
                continue

            print(f"\n--- Subsection: {sub_name} (Rows: {len(filtered_df)}) ---")

            # Execute the core logic
            avg_pct = run_coverage_analysis(filtered_df)

            print(f"RESULT: {llm_name} | {sub_name} | Avg Coverage: {avg_pct:.2f}%")



# Update this path to your directory containing the CSVs
TARGET_DIR = "../../all_results/results_7/experiment3"
process_directory(TARGET_DIR)