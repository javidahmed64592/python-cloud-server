"""Generate self-signed SSL certificate for local development."""

import ipaddress
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from python_cloud_server.config import ROOT_DIR

CERT_FILE = ROOT_DIR / "cert.pem"
KEY_FILE = ROOT_DIR / "key.pem"


class CertificateHandler:
    """Handles SSL certificate generation and management."""

    def __init__(self, cert_file: Path = CERT_FILE, key_file: Path = KEY_FILE, days_valid: int = 365) -> None:
        """Initialize the CertificateHandler."""
        self.cert_file = cert_file
        self.key_file = key_file
        self.days_valid = days_valid

    def generate_self_signed_cert(self) -> None:
        """Generate a self-signed certificate and private key."""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        # Create certificate subject and issuer (self-signed, so they're the same)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "UK"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Development"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ]
        )

        # Build certificate
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC))
            .not_valid_after(datetime.now(UTC) + timedelta(days=self.days_valid))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName("localhost"),
                        x509.DNSName("127.0.0.1"),
                        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    ]
                ),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Write private key to file
        key_path = Path(self.key_file)
        with key_path.open("wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        print(f"✓ Private key saved to {self.key_file}")

        # Write certificate to file
        cert_path = Path(self.cert_file)
        with cert_path.open("wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"✓ Certificate saved to {self.cert_file}")
        print(f"✓ Certificate valid for {self.days_valid} days")


def generate_certificates() -> None:
    """Generate self-signed certificates for local development."""
    handler = CertificateHandler()
    handler.generate_self_signed_cert()
