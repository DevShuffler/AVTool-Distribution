
import os
import sys
import subprocess
import tempfile
from pathlib import Path

def main():
    private_key = os.environ.get("AVTOOL_SIGNING_PRIVATE_KEY", "")

    if not private_key.startswith("-----BEGIN EC PRIVATE KEY-----"):
        raise RuntimeError("Signing secret is missing or invalid")

    public_key_path = Path("avtool-signing-public.pem")

    if not public_key_path.is_file():
        raise RuntimeError("Public key not found")

    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)

        private_path = work / "private.pem"
        message_path = work / "message.bin"
        signature_path = work / "signature.bin"

        private_path.write_text(private_key, encoding="utf-8")
        message_path.write_bytes(b"AVTool signing test")

        subprocess.run(
            [
                "openssl", "dgst", "-sha256",
                "-sign", str(private_path),
                "-out", str(signature_path),
                str(message_path)
            ],
            check=True,
            capture_output=True
        )

        subprocess.run(
            [
                "openssl", "dgst", "-sha256",
                "-verify", str(public_key_path),
                "-signature", str(signature_path),
                str(message_path)
            ],
            check=True,
            capture_output=True
        )

    print("ECDSA SIGNATURE VERIFIED")
    print("PUBLIC AND PRIVATE KEYS MATCH")

if __name__ == "__main__":
    main()
