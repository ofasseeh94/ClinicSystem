import base64
import hashlib
import io
import logging
import os
import socket
import struct
import time
import warnings

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

from ..errors import Problem

MAX_BYTES = 10 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000
# Parser diagnostics may contain source content; never log them.
pdf_logger = logging.getLogger("pypdf")
pdf_logger.addHandler(logging.NullHandler())
pdf_logger.propagate = False
pdf_logger.disabled = True


def validate(content, mime):
    if not content or len(content) > MAX_BYTES:
        raise Problem(413, "file_size", "Attachments must contain 1 byte to 10 MiB.")
    if mime not in {"application/pdf", "image/png", "image/jpeg"}:
        raise Problem(415, "unsupported_file", "Upload a PDF, PNG or JPEG file.")
    try:
        if mime == "application/pdf":
            if not content.startswith(b"%PDF-") or not content.rstrip().endswith(b"%%EOF"):
                raise ValueError("Invalid PDF envelope")
            reader = PdfReader(io.BytesIO(content), strict=True)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 200:
                raise ValueError("Unsupported PDF")
            seen = set()
            nodes = 0
            prohibited = {
                "/JavaScript",
                "/JS",
                "/AA",
                "/OpenAction",
                "/Launch",
                "/EmbeddedFiles",
                "/EF",
                "/AcroForm",
                "/XFA",
                "/RichMedia",
                "/URI",
                "/SubmitForm",
                "/GoToR",
            }

            def walk(obj, depth=0):
                nonlocal nodes
                nodes += 1
                if nodes > 50000 or depth > 64:
                    raise ValueError("Complex PDF")
                if isinstance(obj, IndirectObject):
                    ident = (obj.idnum, obj.generation)
                    if ident in seen:
                        return
                    seen.add(ident)
                    walk(obj.get_object(), depth + 1)
                elif isinstance(obj, DictionaryObject):
                    if prohibited.intersection(obj.keys()) or str(obj.get("/S", "")) in prohibited:
                        raise ValueError("Active PDF")
                    if str(obj.get("/Subtype", "")) in {
                        "/FileAttachment",
                        "/RichMedia",
                        "/Movie",
                        "/Sound",
                        "/3D",
                    }:
                        raise ValueError("Active annotation")
                    for value in obj.values():
                        walk(value, depth + 1)
                elif isinstance(obj, ArrayObject):
                    for value in obj:
                        walk(value, depth + 1)

            walk(reader.trailer)
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as image:
                    if image.format != {"image/png": "PNG", "image/jpeg": "JPEG"}[mime]:
                        raise ValueError("File type mismatch")
                    image.verify()
                with Image.open(io.BytesIO(content)) as image:
                    image.load()
    except Exception:
        raise Problem(
            422, "invalid_file", "File validation failed. Use a static PDF or valid PNG/JPEG."
        ) from None


def key(settings):
    if not settings.document_key:
        raise Problem(503, "document_key_missing", "Private document storage is not configured.")
    return base64.b64decode(settings.document_key)


def encrypt(settings, content, clinic_id, document_id):
    nonce = os.urandom(12)
    return nonce + AESGCM(key(settings)).encrypt(
        nonce, content, f"{clinic_id}/{document_id}".encode()
    )


def decrypt(settings, ciphertext, clinic_id, document_id, expected_hash):
    try:
        result = AESGCM(key(settings)).decrypt(
            ciphertext[:12], ciphertext[12:], f"{clinic_id}/{document_id}".encode()
        )
        if hashlib.sha256(result).hexdigest() != expected_hash:
            raise ValueError("Hash mismatch")
        return result
    except Problem:
        raise
    except Exception:
        raise Problem(
            503, "document_integrity", "Document integrity could not be verified."
        ) from None


def scan(settings, content):
    if settings.document_scan_mode == "synthetic" and settings.environment in {
        "development",
        "test",
    }:
        return "synthetic_ready", "Development only: format validated; NOT malware scanned"
    if not settings.clamav_host:
        return "quarantined", "Malware scanner is not configured; retrieval blocked"
    try:
        deadline = time.monotonic() + 10
        with socket.create_connection(
            (settings.clamav_host, settings.clamav_port), timeout=10
        ) as scanner:

            def budget():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Scanner deadline reached")
                scanner.settimeout(remaining)

            budget()
            scanner.sendall(b"zINSTREAM\0")
            for offset in range(0, len(content), 65536):
                budget()
                part = content[offset : offset + 65536]
                scanner.sendall(struct.pack("!I", len(part)) + part)
            budget()
            scanner.sendall(struct.pack("!I", 0))
            response = b""
            while b"\0" not in response and len(response) < 4096:
                budget()
                part = scanner.recv(1024)
                if not part:
                    break
                response += part
            if b"\0" not in response:
                return "quarantined", "Malware scan incomplete; retrieval blocked"
            verdict = response.rstrip(b"\0\r\n")
            if verdict == b"stream: OK":
                return "ready", "ClamAV scan passed"
            if verdict.startswith(b"stream: ") and verdict.endswith(b" FOUND"):
                return "rejected", "Malware scanner rejected this attachment"
    except (OSError, TimeoutError):
        pass
    return "quarantined", "Malware scan unavailable or inconclusive; retrieval blocked"
