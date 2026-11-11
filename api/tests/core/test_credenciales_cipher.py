import pytest

from app.core.security.credenciales_cipher import (
    CredencialCifradaInvalidaError,
    cifrar,
    descifrar,
)


def test_cifrar_y_descifrar_recupera_el_texto_original():
    texto_plano = "token-de-acceso-de-meta-super-secreto"
    cifrado = cifrar(texto_plano)
    assert cifrado != texto_plano
    assert descifrar(cifrado) == texto_plano


def test_token_cifrado_corrupto_lanza_error_explicito():
    with pytest.raises(CredencialCifradaInvalidaError):
        descifrar("esto-no-es-un-token-fernet-valido")
