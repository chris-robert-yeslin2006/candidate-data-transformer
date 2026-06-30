"""Tests for normalization services (phone, email, name)."""

from app.normalizers.email import EmailNormalizer
from app.normalizers.name import NameNormalizer
from app.normalizers.normalization_service import NormalizationService
from app.normalizers.phone import PhoneNormalizer
from app.domain.models import CanonicalCandidate, ContactInformation, Email, Phone
from app.domain.models.person_name import PersonName


class TestPhoneNormalizer:
    """Tests for phone number normalization."""

    def setup_method(self) -> None:
        self.normalizer = PhoneNormalizer()

    def test_us_10_digit(self) -> None:
        assert self.normalizer.normalize("5551234567") == "+15551234567"

    def test_us_formatted(self) -> None:
        assert self.normalizer.normalize("(555) 123-4567") == "+15551234567"

    def test_us_dots(self) -> None:
        assert self.normalizer.normalize("555.123.4567") == "+15551234567"

    def test_international_with_plus(self) -> None:
        assert self.normalizer.normalize("+1-555-123-4567") == "+15551234567"

    def test_international_uk(self) -> None:
        assert self.normalizer.normalize("+44 20 7946 0958") == "+442079460958"

    def test_empty_string(self) -> None:
        assert self.normalizer.normalize("") == ""

    def test_whitespace_only(self) -> None:
        assert self.normalizer.normalize("   ") == ""

    def test_11_digit_with_country_code(self) -> None:
        assert self.normalizer.normalize("15551234567") == "+15551234567"


class TestEmailNormalizer:
    """Tests for email normalization."""

    def setup_method(self) -> None:
        self.normalizer = EmailNormalizer()

    def test_lowercase(self) -> None:
        assert self.normalizer.normalize("JOHN@EXAMPLE.COM") == "john@example.com"

    def test_strip_whitespace(self) -> None:
        assert self.normalizer.normalize("  john@example.com  ") == "john@example.com"

    def test_mixed_case(self) -> None:
        assert self.normalizer.normalize("John.Doe@Example.COM") == "john.doe@example.com"

    def test_empty_string(self) -> None:
        assert self.normalizer.normalize("") == ""

    def test_valid_email(self) -> None:
        assert self.normalizer.normalize("user@domain.co") == "user@domain.co"


class TestNameNormalizer:
    """Tests for name normalization."""

    def setup_method(self) -> None:
        self.normalizer = NameNormalizer()

    def test_title_case(self) -> None:
        assert self.normalizer.normalize("john doe") == "John Doe"

    def test_all_caps(self) -> None:
        assert self.normalizer.normalize("JOHN DOE") == "John Doe"

    def test_hyphenated_name(self) -> None:
        assert self.normalizer.normalize("mary-jane watson") == "Mary-Jane Watson"

    def test_extra_whitespace(self) -> None:
        assert self.normalizer.normalize("  john   doe  ") == "John Doe"

    def test_empty_string(self) -> None:
        assert self.normalizer.normalize("") == ""

    def test_single_name(self) -> None:
        assert self.normalizer.normalize("madonna") == "Madonna"


class TestNormalizationService:
    """Tests for the NormalizationService."""

    def setup_method(self) -> None:
        self.service = NormalizationService()

    def test_normalize_full_candidate(self) -> None:
        """Normalize all fields on a complete candidate."""
        candidate = CanonicalCandidate(
            name=PersonName(
                display_name="JOHN DOE",
                first="john",
                last="DOE",
            ),
            contact=ContactInformation(
                emails=[Email(value="JOHN@EXAMPLE.COM", type="", is_primary=True)],
                phones=[Phone(value="(555) 123-4567", type="", is_primary=True)],
            ),
        )

        result, warnings = self.service.normalize(candidate)

        assert result.name.display_name == "John Doe"
        assert result.name.first == "John"
        assert result.name.last == "Doe"
        assert result.contact is not None
        assert result.contact.emails[0].value == "john@example.com"
        assert result.contact.phones[0].value == "+15551234567"

    def test_normalize_no_contact(self) -> None:
        """Candidate without contact info normalizes without error."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="jane doe"),
        )

        result, warnings = self.service.normalize(candidate)

        assert result.name.display_name == "Jane Doe"
        assert len(warnings) == 0

    def test_normalize_empty_candidate(self) -> None:
        """Empty candidate normalizes without error."""
        candidate = CanonicalCandidate()
        result, warnings = self.service.normalize(candidate)

        assert len(warnings) == 0
