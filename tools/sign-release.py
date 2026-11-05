
import base64
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


def main():
    version = os.environ["AVTOOL_VERSION"]
    private_key = os.environ["AVTOOL_SIGNING_PRIVATE_KEY"]

    parts = version.split(".")

    if len(parts) != 3 or any(
        not part.isascii() or not part.isdecimal()
        for part in parts
    ):
        raise RuntimeError("Invalid AVTool version")

    package_name = f"AVTool-{version}.zip"
    package_path = Path("dist") / package_name

    if not package_path.is_file():
        raise RuntimeError(f"Package not found: {package_path}")

    if not private_key.startswith("-----BEGIN EC PRIVATE KEY-----"):
        raise RuntimeError("Signing key is missing or invalid")

    package_hash = hashlib.sha256(
        package_path.read_bytes()
    ).hexdigest().upper()

    payload = {
        "schemaVersion": 1,
        "product": "AVTool",
        "version": version,
        "packageFile": package_name,
        "sha256": package_hash,
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)

        key_path = work / "private.pem"
        payload_path = work / "payload.bin"
        signature_path = work / "signature.bin"

        key_path.write_text(private_key, encoding="utf-8")
        payload_path.write_bytes(payload_bytes)

        subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-sign",
                str(key_path),
                "-out",
                str(signature_path),
                str(payload_path),
            ],
            check=True,
            capture_output=True,
        )

        signature_bytes = signature_path.read_bytes()

    manifest = {
        "payload": base64.b64encode(
            payload_bytes
        ).decode("ascii"),
        "signature": base64.b64encode(
            signature_bytes
        ).decode("ascii"),
    }

    manifest_path = Path("dist") / (
        package_name + ".release.json"
    )

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print("AVTOOL RELEASE SIGNED")
    print("Version:", version)
    print("SHA256:", package_hash)
    print("Manifest:", manifest_path)


if __name__ == "__main__":
    main()
