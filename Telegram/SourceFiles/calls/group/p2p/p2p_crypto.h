/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#pragma once

#include <optional>
#include <string_view>
#include <vector>

namespace Calls::Group::P2P {

// Fixed-size byte buffers are used for all key material so a caller cannot
// accidentally pass a short buffer to a primitive that assumes 32 bytes.
using Bytes = std::vector<unsigned char>;

inline constexpr auto kKeySize = 32;
inline constexpr auto kNonceSize = 12;

/**
 * Long-term identity for one device.
 *
 * Two distinct keys, deliberately not derived from one another:
 *  - `signing` (Ed25519) signs the prekey bundle, proving the bundle belongs to
 *    the identity it advertises;
 *  - `dh` (X25519) contributes the initiator's static Diffie-Hellman share to
 *    the X3DH handshake.
 */
struct Identity {
	Bytes signingPublic;
	Bytes signingSecret;
	Bytes dhPublic;
	Bytes dhSecret;
};

/** Generate a fresh identity. Secret keys never leave the device. */
[[nodiscard]] Identity CreateIdentity();

/** Sign `data` with an Ed25519 identity key. */
[[nodiscard]] Bytes Sign(const Bytes &data, const Bytes &secretKey);

/**
 * Verify an Ed25519 signature.
 *
 * @returns false on any malformed input rather than throwing, so a caller
 *   feeding it attacker-controlled bytes cannot be made to abort.
 */
[[nodiscard]] bool Verify(
	const Bytes &data,
	const Bytes &signature,
	const Bytes &publicKey);

/**
 * X25519 Diffie-Hellman.
 *
 * @returns the 32-byte shared secret, or nullopt if the peer sent a
 *   low-order point (which would collapse the shared secret to a known value).
 */
[[nodiscard]] std::optional<Bytes> SharedSecret(
	const Bytes &secretKey,
	const Bytes &peerPublic);

/** HKDF-SHA256 extract-and-expand, used for every derivation in the protocol. */
[[nodiscard]] Bytes HKDF(
	const Bytes &secret,
	const Bytes &salt,
	std::string_view info,
	int length = kKeySize);

/**
 * Domain-separated one-step HMAC derivation, used by the ratchet chains.
 *
 * Each call takes a distinct label (chain, message, header, fingerprint) so no
 * derived key is ever reused across roles.
 */
[[nodiscard]] Bytes RootKeyFrom(const Bytes &secret);
[[nodiscard]] Bytes ChainKeyFrom(const Bytes &secret);
[[nodiscard]] Bytes MessageKeyFrom(const Bytes &secret);
[[nodiscard]] Bytes HeaderKeyFrom(const Bytes &secret);
[[nodiscard]] Bytes FingerprintFrom(const Bytes &secret);

/**
 * X3DH mixed-input KDF over DH shares plus both identity keys.
 *
 * Both identities are mixed in so the result is bound to *which* pair of
 * devices agreed on it, not merely to the DH shares.
 */
[[nodiscard]] Bytes DeriveX3dh(
	const std::vector<Bytes> &shares,
	const Bytes &identityA,
	const Bytes &identityB);

/**
 * ChaCha20-Poly1305 seal.
 *
 * @param additionalData is authenticated but not encrypted — the message header
 *   and both user ids go here so ciphertext cannot be moved between sessions.
 * @returns ciphertext, or nullopt if the cipher rejects the inputs.
 */
[[nodiscard]] std::optional<Bytes> Seal(
	const Bytes &plaintext,
	const Bytes &key,
	const Bytes &nonce,
	const Bytes &additionalData);

/**
 * ChaCha20-Poly1305 open.
 *
 * @returns nullopt when authentication fails — wrong key, tampered ciphertext,
 *   or a swapped header. Never returns unauthenticated plaintext.
 */
[[nodiscard]] std::optional<Bytes> Open(
	const Bytes &ciphertext,
	const Bytes &key,
	const Bytes &nonce,
	const Bytes &additionalData);

/** Cryptographically strong random bytes. */
[[nodiscard]] Bytes RandomBytes(int length);

} // namespace Calls::Group::P2P