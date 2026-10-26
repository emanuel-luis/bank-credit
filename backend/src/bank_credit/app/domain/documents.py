"""CPF and CNPJ normalization and check digits.

CNPJ accepts the alphanumeric format: 12 characters in [0-9A-Z] followed by 2 numeric check
digits. A character's value is its ASCII code minus 48, so digits keep their value and A is 17.
"""

import re
from typing import Annotated

from pydantic import AfterValidator

_PUNCTUATION = re.compile(r"[.\-/\s]")
_CPF_RE = re.compile(r"^[0-9]{11}$")
_CNPJ_RE = re.compile(r"^[0-9A-Z]{12}[0-9]{2}$")
_CNPJ_WEIGHTS = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def normalize_cpf(value: str) -> str:
    return _PUNCTUATION.sub("", value)


def normalize_cnpj(value: str) -> str:
    return _PUNCTUATION.sub("", value).upper()


def _cpf_digit(digits: str) -> str:
    total = sum(int(d) * w for d, w in zip(digits, range(len(digits) + 1, 1, -1), strict=True))
    return str((total * 10 % 11) % 10)


def _cnpj_digit(chars: str) -> str:
    weights = _CNPJ_WEIGHTS[-len(chars) :]
    total = sum((ord(c) - 48) * w for c, w in zip(chars, weights, strict=True))
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


def with_cpf_check_digits(base: str) -> str:
    """Complete 9 digits with their 2 check digits (used to build synthetic documents)."""
    base = base + _cpf_digit(base)
    return base + _cpf_digit(base)


def with_cnpj_check_digits(base: str) -> str:
    """Complete 12 characters ([0-9A-Z]) with their 2 check digits."""
    base = base.upper()
    base = base + _cnpj_digit(base)
    return base + _cnpj_digit(base)


def is_valid_cpf(value: str) -> bool:
    cpf = normalize_cpf(value)
    if not _CPF_RE.match(cpf) or len(set(cpf)) == 1:
        return False
    return cpf == with_cpf_check_digits(cpf[:9])


def is_valid_cnpj(value: str) -> bool:
    cnpj = normalize_cnpj(value)
    if not _CNPJ_RE.match(cnpj) or len(set(cnpj)) == 1:
        return False
    return cnpj == with_cnpj_check_digits(cnpj[:12])


def _validated_cpf(value: str) -> str:
    if not is_valid_cpf(value):
        raise ValueError("invalid CPF")
    return normalize_cpf(value)


def _validated_cnpj(value: str) -> str:
    if not is_valid_cnpj(value):
        raise ValueError("invalid CNPJ")
    return normalize_cnpj(value)


# Pydantic types: accept formatted input, validate the check digits, keep only the stored form.
Cpf = Annotated[str, AfterValidator(_validated_cpf)]
Cnpj = Annotated[str, AfterValidator(_validated_cnpj)]
