import base64
import hashlib
import socket
import struct
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from clinic_api.config import Settings
from clinic_api.errors import Problem
from clinic_api.records.files import decrypt, encrypt, scan


@pytest.mark.parametrize(
    "verdict,state",
    [
        (b"stream: OK\0", "ready"),
        (b"stream: Synthetic-Test FOUND\0", "rejected"),
        (b"ERROR\0", "quarantined"),
        (b"not-stream: OK\0", "quarantined"),
    ],
)
def test_clamav_stream_protocol(verdict, state):
    content = b"Fictional attachment scanner protocol fixture"
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        server.settimeout(10)

        def receive():
            with server.accept()[0] as conn:
                conn.settimeout(10)

                def exact(n):
                    out = b""
                    while len(out) < n:
                        part = conn.recv(n - len(out))
                        if not part:
                            raise AssertionError("Incomplete scanner stream")
                        out += part
                    return out

                assert exact(10) == b"zINSTREAM\0"
                received = b""
                while True:
                    size = struct.unpack("!I", exact(4))[0]
                    if size == 0:
                        break
                    received += exact(size)
                assert received == content
                conn.sendall(verdict)

        with ThreadPoolExecutor(max_workers=1) as executor:
            task = executor.submit(receive)
            result = scan(
                Settings(clamav_host="127.0.0.1", clamav_port=server.getsockname()[1]),
                content,
            )
            task.result(timeout=15)
            assert result[0] == state


def test_ciphertext_integrity_patient_context_and_hash():
    settings = Settings(document_key=base64.b64encode(b"s" * 32).decode())
    clinic_id, document_id = uuid4(), uuid4()
    data = b"Fictional attachment integrity fixture"
    digest = hashlib.sha256(data).hexdigest()
    ciphertext = encrypt(settings, data, clinic_id, document_id)
    assert decrypt(settings, ciphertext, clinic_id, document_id, digest) == data
    for encrypted, clinic, document, sha in (
        (ciphertext[:-1] + bytes([ciphertext[-1] ^ 1]), clinic_id, document_id, digest),
        (ciphertext, uuid4(), document_id, digest),
        (ciphertext, clinic_id, uuid4(), digest),
        (ciphertext, clinic_id, document_id, "0" * 64),
    ):
        with pytest.raises(Problem) as caught:
            decrypt(settings, encrypted, clinic, document, sha)
        assert caught.value.status == 503
