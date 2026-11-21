// A 32-bit RV32-style ALU. Operation 7 selects shift left logical.
module alu(input [31:0] a, b, input [3:0] op, output reg [31:0] result);
    always @* begin
        case (op)
            0: result = a + b;
            1: result = a - b;
            2: result = a & b;
            3: result = a | b;
            4: result = a ^ b;
            5: result = $signed(a) < $signed(b);
            6: result = a < b;
            7: result = a << b[4:0];
            8: result = $signed(a) >>> b[4:0];
            9: result = a >> b[4:0];
            10: result = b;
            15: result = 0;
            default: result = 0;
        endcase
    end
endmodule
