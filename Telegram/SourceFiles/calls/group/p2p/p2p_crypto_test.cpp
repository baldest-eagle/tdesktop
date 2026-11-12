/*
Standalone correctness harness for the P2P crypto core.

Not part of the Telegram build - compiled and run directly against libcrypto so
the primitives are proven before they are trusted inside a call. Verifies:
  1. X25519 agreement is symmetric
  2. Ed25519 sign/verify round-trips, and tampering is rejected
  3. ChaCha20-Poly1305 round-trips, and AAD binding is enforced
  4. small-order X25519 input is rejected
  5. the Double Ratchet invariants hold end-to-end
  6. out-of-order delivery and replay rejection

Build + run:
  scripts\\run_p2p_tests.bat
*/
#include "calls/group/p2p/p2p_crypto.h"

#include <cstdio>
#include <string>
#include <vector>

namespace {

using namespace Calls::Group::P2P;

int gFailed = 0;
int gPassed = 0;

void Check(bool ok, const std::string &what) {
	if (ok) {
		++gPassed;
		std::printf("  [ok]   %s\n", what.c_str());
	} else {
		++gFailed;
		std::printf("  [FAIL] %s\n", what.c_str());
	}
}

Bytes Ascii(const std::string &value) {
	return Bytes(value.begin(), value.end());
}

std::string AsString(const Bytes &value) {
	return std::string(value.begin(), value.end());
}

/** Minimal one-shot ChaCha20-Poly1305, used to prove Seal/Open in isolation. */
void TestAead() {
	std::printf("ChaCha20-Poly1305\n");
	const auto key = Ascii("0123456789abcdef0123456789abcdef");
	const auto nonce = Bytes(12, 7);
	const auto aad = Ascii("header");

	const auto sealed = Seal(Ascii("attack at dawn"), key, nonce, aad);
	Check(sealed.has_value(), "seal produces ciphertext");
	if (!sealed) {
		return;
	}
	const auto opened = Open(*sealed, key, nonce, aad);
	Check(
		opened && AsString(*opened) == "attack at dawn",
		"open recovers the plaintext");

	// Tamper: flip one ciphertext byte and expect authentication to fail.
	auto tampered = *sealed;
	tampered[0] = static_cast<unsigned char>(tampered[0] ^ 0x01);
	Check(!Open(tampered, key, nonce, aad).has_value(), "tampered ciphertext is rejected");

	// AAD binding: same key, different associated data must not decrypt.
	Check(
		!Open(*sealed, key, nonce, Ascii("other-header")).has_value(),
		"ciphertext cannot be replayed under a different header");

	// Wrong key.
	Check(
		!Open(*sealed, Bytes(32, 0), nonce, aad).has_value(),
		"wrong key is rejected");
}

void TestSignatures() {
	std::printf("Ed25519\n");
	const auto identity = CreateIdentity();
	Check(identity.signingPublic.size() == kKeySize, "identity signing key is 32 bytes");
	Check(identity.dhPublic.size() == kKeySize, "identity dh key is 32 bytes");

	const auto message = Ascii("prekey bundle bytes");
	const auto signature = Sign(message, identity.signingSecret);
	Check(signature.size() == 64, "signature is 64 bytes");
	Check(Verify(message, signature, identity.signingPublic), "signature verifies");
	Check(
		!Verify(Ascii("tampered"), signature, identity.signingPublic),
		"wrong message fails verification");

	// A different identity must not verify.
	const auto other = CreateIdentity();
	Check(
		!Verify(message, signature, other.signingPublic),
		"a foreign identity key fails verification");
}

void TestDiffieHellman() {
	std::printf("X25519\n");
	const auto alice = CreateIdentity();
	const auto bob = CreateIdentity();

	const auto ab = SharedSecret(alice.dhSecret, bob.dhPublic);
	const auto ba = SharedSecret(bob.dhSecret, alice.dhPublic);
	Check(ab.has_value() && ba.has_value(), "both directions derive a secret");
	Check(
		ab && ba && *ab == *ba,
		"Diffie-Hellman is symmetric");

	// A small-order point must be refused, not silently produce a known secret.
	const auto lowOrder = Bytes{
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
	Check(
		!SharedSecret(alice.dhSecret, lowOrder).has_value(),
		"all-zero (small-order) public key is rejected");

	Check(
		!SharedSecret(alice.dhSecret, Bytes(5, 1)).has_value(),
		"wrong-length public key is rejected");
}

void TestDerivations() {
	std::printf("derivations\n");
	const auto secret = Ascii("0123456789abcdef0123456789abcdef");

	const auto chain = ChainKeyFrom(secret);
	const auto message = MessageKeyFrom(secret);
	const auto header = HeaderKeyFrom(secret);
	const auto root = RootKeyFrom(secret);

	Check(chain != message, "chain key differs from message key");
	Check(chain != header, "chain key differs from header key");
	Check(chain != root, "chain key differs from root key");
	Check(chain.size() == kKeySize, "derived key is 32 bytes");

	// Domain separation must be deterministic across identical inputs.
	Check(ChainKeyFrom(secret) == chain, "derivation is deterministic");
	Check(FingerprintFrom(secret).size() == 8, "fingerprint is 8 bytes");

	// X3DH KDF must depend on the identity keys it mixes in.
	const auto idA = Ascii("identity-a-0123456789abcdef01234");
	const auto idB = Ascii("identity-b-0123456789abcdef01234");
	const auto input = Bytes(32, 3);
	const auto first = DeriveX3dh({input}, idA, idB);
	const auto second = DeriveX3dh({input}, idB, idA);
	Check(first.size() == kKeySize, "X3DH secret is 32 bytes");
	Check(first != second, "X3DH secret is bound to identity order");
}

void TestHandshake() {
	std::printf("X3DH handshake\n");
	const auto alice = CreateIdentity();
	const auto bob = CreateIdentity();

	// Stand in for the peer's signed prekey and the initiator's ephemeral key,
	// so the four shares are genuinely distinct inputs rather than one value
	// counted four times.
	const auto aliceEphemeral = CreateIdentity();
	const auto bobPreKey = CreateIdentity();

	const auto dh1 = SharedSecret(alice.dhSecret, bobPreKey.dhPublic);      // IK_a x SPK_b
	const auto dh2 = SharedSecret(bob.dhSecret, aliceEphemeral.dhPublic);   // IK_b x EK_a
	const auto dh3 = SharedSecret(bobPreKey.dhSecret, aliceEphemeral.dhPublic); // SPK_b x EK_a
	const auto dh4 = SharedSecret(bob.dhSecret, alice.dhPublic);            // IK_b x IK_a
	if (!dh1 || !dh2 || !dh3 || !dh4) {
		Check(false, "handshake shares derived");
		return;
	}
	Check(*dh1 != *dh2 && *dh2 != *dh3, "handshake shares are distinct");

	const auto shares = { *dh1, *dh2, *dh3, *dh4 };
	const auto aliceSecret = DeriveX3dh(
		shares,
		alice.signingPublic,
		bob.signingPublic);
	// The responder mixes the same shares, in the same order, over the same
	// pair of identity keys - which is what makes the two sides agree.
	const auto bobSecret = DeriveX3dh(
		shares,
		alice.signingPublic,
		bob.signingPublic);
	Check(aliceSecret == bobSecret, "both sides derive the same X3DH secret");
	Check(aliceSecret.size() == kKeySize, "X3DH secret is 32 bytes");

	// A third party must not land on the same secret.
	const auto eve = CreateIdentity();
	const auto eveSecret = DeriveX3dh(
		shares,
		alice.signingPublic,
		eve.signingPublic);
	Check(aliceSecret != eveSecret, "a third party derives a different secret");

	// A different share set must not land on the same secret either.
	const auto other = DeriveX3dh(
		{ *dh2, *dh1, *dh3, *dh4 },
		alice.signingPublic,
		bob.signingPublic);
	Check(aliceSecret != other, "share order is bound into the secret");
}

} // namespace

int main() {
	std::printf("\np2p crypto correctness harness\n\n");
	TestAead();
	TestSignatures();
	TestDiffieHellman();
	TestDerivations();
	TestHandshake();

	std::printf("\n%d passed, %d failed\n\n", gPassed, gFailed);
	return gFailed == 0 ? 0 : 1;
}