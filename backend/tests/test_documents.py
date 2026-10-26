import pytest
from pydantic import TypeAdapter, ValidationError

from bank_credit.app.domain.documents import (
    Cnpj,
    Cpf,
    is_valid_cnpj,
    is_valid_cpf,
    normalize_cnpj,
    normalize_cpf,
    with_cnpj_check_digits,
    with_cpf_check_digits,
)

# Textbook synthetic documents, not real people or companies.
VALID_CPF = "12345678909"
VALID_CNPJ = "11222333000181"


def test_cpf_valid_and_formatted():
    assert is_valid_cpf(VALID_CPF)
    assert is_valid_cpf("123.456.789-09")
    assert normalize_cpf("123.456.789-09") == VALID_CPF


@pytest.mark.parametrize(
    "value",
    ["12345678900", "11111111111", "00000000000", "1234567890", "123456789012", "1234567890a", ""],
)
def test_cpf_invalid(value):
    assert not is_valid_cpf(value)


def test_cpf_check_digit_generation_round_trips():
    for base in ("000000001", "987654321", "529982247"):
        assert is_valid_cpf(with_cpf_check_digits(base))


def test_cnpj_numeric_valid_and_formatted():
    assert is_valid_cnpj(VALID_CNPJ)
    assert is_valid_cnpj("11.222.333/0001-81")
    assert normalize_cnpj("11.222.333/0001-81") == VALID_CNPJ


def test_cnpj_alphanumeric():
    cnpj = with_cnpj_check_digits("12ABC34501DE")
    assert cnpj == "12ABC34501DE35"  # the example in the Receita Federal's alphanumeric CNPJ spec
    assert cnpj.startswith("12ABC34501DE")
    assert cnpj[-2:].isdigit()
    assert is_valid_cnpj(cnpj)
    assert is_valid_cnpj("12.abc.345/01de-" + cnpj[-2:])  # formatted and lower case
    assert normalize_cnpj("12.abc.345/01de-" + cnpj[-2:]) == cnpj


def test_cnpj_character_value_is_ascii_minus_48():
    # Digits keep their own value, so numeric CNPJs are unaffected; letters weigh ASCII - 48.
    assert with_cnpj_check_digits("112223330001") == VALID_CNPJ
    assert with_cnpj_check_digits("12ABC34501DE") != with_cnpj_check_digits("12ABC34501DF")


@pytest.mark.parametrize(
    "value",
    ["11222333000180", "11111111111111", "1122233300018", "112223330001AB", "12ABC34501DE00", ""],
)
def test_cnpj_invalid(value):
    assert not is_valid_cnpj(value)


def test_pydantic_types_normalize_and_validate():
    assert TypeAdapter(Cpf).validate_python("123.456.789-09") == VALID_CPF
    assert TypeAdapter(Cnpj).validate_python("11.222.333/0001-81") == VALID_CNPJ
    with pytest.raises(ValidationError):
        TypeAdapter(Cpf).validate_python("123.456.789-00")
    with pytest.raises(ValidationError):
        TypeAdapter(Cnpj).validate_python("11.222.333/0001-80")
