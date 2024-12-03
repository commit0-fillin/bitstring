"""
The 8-bit float formats used here are from a proposal supported by Graphcore, AMD and Qualcomm.
See https://arxiv.org/abs/2206.02915

"""
import struct
import zlib
import array
import bitarray
from bitstring.luts import binary8_luts_compressed
import math

class Binary8Format:
    """8-bit floating point formats based on draft IEEE binary8"""

    def __init__(self, exp_bits: int, bias: int):
        self.exp_bits = exp_bits
        self.bias = bias
        self.pos_clamp_value = 127
        self.neg_clamp_value = 255

    def __str__(self):
        return f'Binary8Format(exp_bits={self.exp_bits}, bias={self.bias})'

    def float_to_int8(self, f: float) -> int:
        """Given a Python float convert to the best float8 (expressed as an integer in 0-255 range)."""
        if math.isnan(f):
            return 0xFF  # NaN representation
        if f == 0:
            return 0x00  # Positive zero
        if f < 0:
            sign_bit = 0x80
            f = -f
        else:
            sign_bit = 0x00
        
        if math.isinf(f):
            return sign_bit | 0x7F  # Infinity representation
        
        exponent = math.floor(math.log2(f))
        mantissa = int((f / (2**exponent) - 1) * (2**(8 - self.exp_bits)))
        
        biased_exponent = exponent + self.bias
        if biased_exponent < 0:
            # Subnormal numbers
            mantissa = int(f * (2**(7 - self.bias)))
            biased_exponent = 0
        elif biased_exponent >= (1 << self.exp_bits) - 1:
            # Clamp to max value
            return self.pos_clamp_value if sign_bit == 0 else self.neg_clamp_value
        
        exponent_bits = biased_exponent << (7 - self.exp_bits)
        return sign_bit | exponent_bits | (mantissa & ((1 << (7 - self.exp_bits)) - 1))

    def createLUT_for_binary8_to_float(self):
        """Create a LUT to convert an int in range 0-255 representing a float8 into a Python float"""
        lut = []
        for i in range(256):
            sign = -1 if i & 0x80 else 1
            exponent = (i >> (7 - self.exp_bits)) & ((1 << self.exp_bits) - 1)
            mantissa = i & ((1 << (7 - self.exp_bits)) - 1)
            
            if exponent == 0:
                if mantissa == 0:
                    value = 0.0
                else:
                    # Subnormal numbers
                    value = sign * (mantissa / (2**(7 - self.exp_bits))) * (2**(-self.bias + 1))
            elif exponent == (1 << self.exp_bits) - 1:
                if mantissa == 0:
                    value = float('inf') if sign == 1 else float('-inf')
                else:
                    value = float('nan')
            else:
                # Normal numbers
                value = sign * (1 + mantissa / (2**(7 - self.exp_bits))) * (2**(exponent - self.bias))
            
            lut.append(value)
        return lut
p4binary_fmt = Binary8Format(exp_bits=4, bias=8)
p3binary_fmt = Binary8Format(exp_bits=5, bias=16)
