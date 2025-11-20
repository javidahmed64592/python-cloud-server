"""Generate self-signed SSL certificate for local development."""

import ipaddress
from datetime import UTC, datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from python_cloud_server.config import ROOT_DIR, load_config


class CertificateHandler:
    """Handles SSL certificate generation and management."""

    def __init__(self) -> None:
        """Initialize the CertificateHandler."""
        config = load_config()
        self.cert_file = ROOT_DIR / config.ssl_certfile
        self.key_file = ROOT_DIR / config.ssl_keyfile
        self.days_valid = config.days_valid

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
        with self.key_file.open("wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        print(f"✓ Private key saved to {self.key_file}")

        # Write certificate to file
        with self.cert_file.open("wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"✓ Certificate saved to {self.cert_file}")
        print(f"✓ Certificate valid for {self.days_valid} days")


def generate_certificates() -> None:
    """Generate self-signed certificates for local development."""
    handler = CertificateHandler()
    handler.generate_self_signed_cert()
