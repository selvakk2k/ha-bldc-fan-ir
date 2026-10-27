import base64
from struct import unpack
import pytest

from custom_components.superfan_ir.ir import (
    SuperfanNEC,
    SUPERFAN_ADDRESS,
    ATOMBERG_ADDRESS,
    ACTIVA_ADDRESS,
    ORIENT_ADDRESS,
    GOLDMEDAL_ADDRESS,
    NEC_HDR_MARK,
    NEC_HDR_SPACE,
)
from custom_components.superfan_ir.const import (
    MODEL_ACTIVA,
    MODEL_ATOMBERG,
    MODEL_GOLDMEDAL,
    MODEL_ORIENT,
    MODEL_T10,
)


def test_command_byte_lookups():
    # Superfan
    assert SuperfanNEC.get_command_byte("Power", MODEL_T10) == 0x98
    assert SuperfanNEC.get_command_byte("Low", MODEL_T10) == 0x94

    # Atomberg
    assert SuperfanNEC.get_command_byte("Power", MODEL_ATOMBERG) == 0x6E
    assert SuperfanNEC.get_command_byte("Boost", MODEL_ATOMBERG) == 0x70

    # Activa
    assert SuperfanNEC.get_command_byte("Power", MODEL_ACTIVA) == 0xEA
    assert SuperfanNEC.get_command_byte("1", MODEL_ACTIVA) == 0x4A
    assert SuperfanNEC.get_command_byte("Nature Mode", MODEL_ACTIVA) == 0x98

    # Orient
    assert SuperfanNEC.get_command_byte("Power Off", MODEL_ORIENT) == 0x52
    assert SuperfanNEC.get_command_byte("Power On", MODEL_ORIENT) == 0xAA
    assert SuperfanNEC.get_command_byte("Boost", MODEL_ORIENT) == 0xF2

    # Goldmedal
    assert SuperfanNEC.get_command_byte("Power", MODEL_GOLDMEDAL) == 0x33
    assert SuperfanNEC.get_command_byte("1", MODEL_GOLDMEDAL) == 0xB3
    assert SuperfanNEC.get_command_byte("Boost", MODEL_GOLDMEDAL) == 0x4B


def test_nec_addresses():
    assert SuperfanNEC.get_address(MODEL_T10) == 0x00DF
    assert SuperfanNEC.get_address(MODEL_ATOMBERG) == 0x00F3
    assert SuperfanNEC.get_address(MODEL_ACTIVA) == 0x5AA5
    assert SuperfanNEC.get_address(MODEL_ORIENT) == 0x6B94
    assert SuperfanNEC.get_address(MODEL_GOLDMEDAL) == 0x5A95


def test_raw_timings_structure():
    for m in [MODEL_T10, MODEL_ATOMBERG, MODEL_ACTIVA, MODEL_ORIENT, MODEL_GOLDMEDAL]:
        timings = SuperfanNEC.get_raw_timings("Power", m)
        assert len(timings) == 140  # 2 full 32-bit frames (68*2) + repeat frame (4)
        assert timings[0] == NEC_HDR_MARK
        assert timings[1] == NEC_HDR_SPACE


def test_tuya_and_broadlink_encoding():
    b64_tuya = SuperfanNEC.get_tuya_base64("Power", MODEL_GOLDMEDAL)
    assert b64_tuya.startswith("b64:")

    b64_broadlink = SuperfanNEC.get_broadlink_base64("Power", MODEL_ORIENT)
    raw = base64.b64decode(b64_broadlink)
    assert raw[0] == 0x26

    # Verify Broadlink Atomberg packet
    b64_atomberg = SuperfanNEC.get_broadlink_base64("Power", MODEL_ATOMBERG)
    raw_atomberg = base64.b64decode(b64_atomberg)
    assert raw_atomberg[0] == 0x26


def test_pronto_and_tasmota():
    pronto = SuperfanNEC.get_pronto_hex("Power", MODEL_ACTIVA)
    assert pronto.startswith("0000 006D")

    # Known vector regression test (LG TV Power [0x04, 0xFB, 0x08, 0xF7] -> 0x20DF10EF)
    known_vector = [0x04, 0xFB, 0x08, 0xF7]
    reversed_hex = f"0x{''.join(f'{SuperfanNEC.reverse_byte_bits(b):02X}' for b in known_vector)}"
    assert reversed_hex == "0x20DF10EF"

    # Superfan Power (wire: 0x00DF9867 -> Tasmota MSB: 0x00FB19E6)
    tasmota_superfan = SuperfanNEC.get_tasmota_payload("Power", MODEL_T10)
    assert tasmota_superfan["Data"] == "0x00FB19E6"

    # Atomberg Power (wire: 0x00F3916E -> Tasmota MSB: 0x00CF8976)
    tasmota_atomberg = SuperfanNEC.get_tasmota_payload("Power", MODEL_ATOMBERG)
    assert tasmota_atomberg["Data"] == "0x00CF8976"

    # Activa Power (wire: 0x5AA5EA15 -> Tasmota MSB: 0x5AA557A8)
    tasmota_activa = SuperfanNEC.get_tasmota_payload("Power", MODEL_ACTIVA)
    assert tasmota_activa["Data"] == "0x5AA557A8"

    # Orient Power On (wire: 0x6B94AA55 -> Tasmota MSB: 0xD62955AA)
    tasmota_orient = SuperfanNEC.get_tasmota_payload("Power On", MODEL_ORIENT)
    assert tasmota_orient["Data"] == "0xD62955AA"

    # Goldmedal Power (wire: 0x5A9533CC -> Tasmota MSB: 0x5AA9CC33)
    tasmota_gm = SuperfanNEC.get_tasmota_payload("Power", MODEL_GOLDMEDAL)
    assert tasmota_gm["Data"] == "0x5AA9CC33"


def test_nec_decoding():
    assert SuperfanNEC.decode_nec(SUPERFAN_ADDRESS, 0x98) == "Power"
    assert SuperfanNEC.decode_nec(ATOMBERG_ADDRESS, 0x6E) == "Power"
    assert SuperfanNEC.decode_nec(ACTIVA_ADDRESS, 0xEA) == "Power"
    assert SuperfanNEC.decode_nec(ORIENT_ADDRESS, 0xAA) == "Power On"
    assert SuperfanNEC.decode_nec(GOLDMEDAL_ADDRESS, 0x33) == "Power"


def test_atomberg_command_bytes_no_collision():
    from custom_components.superfan_ir.ir import ATOMBERG_COMMAND_BYTES

    command_bytes = set(ATOMBERG_COMMAND_BYTES.values())
    for cmd in command_bytes:
        inv = (~cmd) & 0xFF
        assert inv not in command_bytes, f"Collision detected: cmd 0x{cmd:02X} inverse 0x{inv:02X} is also a command"
