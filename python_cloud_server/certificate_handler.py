"""Generate self-signed SSL certificate for local development."""

import ipaddress
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from python_cloud_server.config import load_config


class CertificateHandler:
    """Handles SSL certificate generation and management."""

    def __init__(self) -> None:
        """Initialize the CertificateHandler."""
        config = load_config()
        self.cert_file = config.certificate.ssl_cert_file_path
        self.key_file = config.certificate.ssl_key_file_path
        self.days_valid = config.certificate.days_valid

    @property
    def certificate_subject(self) -> x509.Name:
        """Define the subject for the self-signed certificate."""
        return x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "UK"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Development"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ]
        )

    @staticmethod
    def new_private_key() -> rsa.RSAPrivateKey:
        """Generate a new RSA private key."""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

    @staticmethod
    def _write_to_file(file_path: Path, data: bytes) -> None:
        """Write data to a file."""
        with file_path.open("wb") as f:
            f.write(data)

    def write_to_key_file(self, data: bytes) -> None:
        """Write data to the key file."""
        self._write_to_file(self.key_file, data)

    def write_to_cert_file(self, data: bytes) -> None:
        """Write data to the certificate file."""
        self._write_to_file(self.cert_file, data)

    def generate_self_signed_cert(self) -> None:
        """Generate a self-signed certificate and private key.

        :raise OSError: If certificate directory cannot be created or files cannot be written
        :raise PermissionError: If insufficient permissions to write certificate files
        """
        try:
            # Ensure certificate directory exists and is writable
            self.cert_file.parent.mkdir(parents=True, exist_ok=True)

            # Test write permissions
            if not self.cert_file.parent.exists():
                msg = f"Failed to create certificate directory: {self.cert_file.parent}"
                raise OSError(msg)  # noqa: TRY301

            # Generate private key
            private_key = self.new_private_key()

            # Create certificate subject and issuer (self-signed, so they're the same)
            subject = issuer = self.certificate_subject

            # Build certificate
            certificate = (
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
            self.write_to_key_file(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

            # Write certificate to file
            self.write_to_cert_file(certificate.public_bytes(serialization.Encoding.PEM))

            print("✓ Certificate generated successfully")
            print(f"  Key file: {self.key_file}")
            print(f"  Certificate file: {self.cert_file}")
            print(f"  Valid for: {self.days_valid} days")

        except PermissionError as e:
            print("ERROR: Permission denied when writing certificate files", file=sys.stderr)
            print(f"  Directory: {self.cert_file.parent}", file=sys.stderr)
            print(f"  Error: {e}", file=sys.stderr)
            raise
        except OSError as e:
            print("ERROR: Failed to generate certificate", file=sys.stderr)
            print(f"  Error: {e}", file=sys.stderr)
            raise


def generate_certificates() -> None:
    """Generate self-signed certificates for local development.

    :raise SystemExit: If certificate generation fails
    """
    try:
        handler = CertificateHandler()
        handler.generate_self_signed_cert()
    except (OSError, PermissionError) as e:
        print(f"\nFailed to generate certificates: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during certificate generation: {e}", file=sys.stderr)
        sys.exit(1)
