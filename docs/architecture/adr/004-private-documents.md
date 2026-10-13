# ADR-004 — bounded encrypted attachments and attributed investigation results

Accepted for synthetic development, 2026-10-13.

Store bounded attachment ciphertext in PostgreSQL alongside metadata, rather than provision a
public or local static file directory. A 10 MiB limit keeps this initial implementation manageable.
AES-256-GCM uses a random nonce and clinic/document identity as associated data; SHA-256 records
the exact original bytes. Upload, lifecycle/scan evidence and audit commit in one transaction.
The baseline's private object bucket remains a future storage backend behind the same API;
large-volume use requires quotas, operational review and tested restore before real data.

Metadata is recorded first (`pending_upload`), then a bounded raw byte stream is validated and
encrypted. The API accepts static PDF, PNG and JPEG, rejects MIME mismatches and active/encrypted
PDFs, and caps page count/image pixels. Structural validation is not a malware scan or a universal
file-safety guarantee. Parser process isolation and resource controls are a production prerequisite.

ClamAV INSTREAM sends original bytes to a configured trusted daemon. Only the expected clean
response releases a file; positive detection rejects it; missing/failed/incomplete scanning keeps
it quarantined. Ten-second scanner deadlines bound failure. Dev/test may explicitly select
`synthetic`: resulting files carry `synthetic_ready`, never a malware-clean claim. Production
configuration rejects that mode, and retrieval refuses historical `synthetic_ready` records there.
Protocol source: [official ClamAV daemon manual](https://raw.githubusercontent.com/Cisco-Talos/clamav/main/docs/man/clamd.8.in).

Downloads require the current staff bearer plus a 60-second HMAC-signed ticket bound to actor,
clinic, patient, document and hash. The ticket stays in a POST body, not a URL. Each retrieval
rechecks permissions and lifecycle, authenticates ciphertext and verifies its hash, then appends
an access audit. The viewer holds an object URL in memory and revokes it on closure/unmount.
PDF views are sandboxed; downloads use generated filenames and no-store/nosniff controls.
There are no permanent public document URLs or parent links.

Document identity/content and investigation request identity cannot be overwritten. Withdrawal
retains the encrypted historical file with a reason and blocks further retrieval; already downloaded
copies cannot be recalled. Investigation results are immutable, with attributed corrections linked
to the previous result. Branching corrections are rejected. Orders have a separate versioned
status and require a recorded result to complete. Nothing generates reference ranges, diagnoses,
clinical interpretations, orders to external labs, or notifications.

Consequences: the database backup must include ciphertext and the separate encryption key must
be backed up securely. Losing/changing it prevents retrieval; there is no automatic key rotation.
Final deployment needs key management, restricted DB roles, scanner signature-update monitoring,
private scanner transport, parser isolation, storage quotas/retention and tested restore. Protocol
fixtures are tested; an actual ClamAV installation/signature database has not been exercised locally.
