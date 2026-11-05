
import base64
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PRIVATE_KEY = os.environ["AVTOOL_SIGNING_PRIVATE_KEY"]
ENABLED_TEXT = os.environ["AVTOOL_ACCESS_ENABLED"]

if ENABLED_TEXT not in ("true", "false"):
    raise RuntimeError("Invalid AVTOOL_ACCESS_ENABLED value")

enabled = ENABLED_TEXT == "true"

issued = datetime.now(timezone.utc)
expires = issued + timedelta(hours=168)

payload = {
    "schemaVersion": 1,
    "product": "AVTool",
    "enabled": enabled,
    "issuedAtUtc": issued.isoformat().replace("+00:00", "Z"),
    "expiresAtUtc": expires.isoformat().replace("+00:00", "Z"),
}

payload_bytes = json.dumps(
    payload,
    separators=(",", ":"),
    ensure_ascii=False
).encode("utf-8")

with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(temp_dir)

    private_path = temp / "private.pem"
    payload_path = temp / "payload.bin"
    signature_path = temp / "signature.bin"

    private_path.write_text(PRIVATE_KEY, encoding="utf-8")
    payload_path.write_bytes(payload_bytes)

    subprocess.run(
        [
            "openssl", "dgst", "-sha256",
            "-sign", str(private_path),
            "-out", str(signature_path),
            str(payload_path)
        ],
        check=True,
        capture_output=True
    )

    signature = signature_path.read_bytes()

token = {
    "payload": base64.b64encode(payload_bytes).decode("ascii"),
    "signature": base64.b64encode(signature).decode("ascii"),
}

output_path = Path("access-token.json")

output_path.write_text(
    json.dumps(token, indent=2),
    encoding="utf-8"
)

print("AVTOOL TOKEN GENERATED")
print("ENABLED:", enabled)
print("ISSUED UTC:", issued.isoformat())
print("EXPIRES UTC:", expires.isoformat())
print("OUTPUT:", output_path)
