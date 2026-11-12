/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "calls/group/p2p/p2p_crypto.h"

#include <openssl/evp.h>
#include <openssl/kdf.h>
#include <openssl/rand.h>
#include <openssl/core_names.h>
#include <openssl/params.h>

#include <algorithm>
#include <string_view>

namespace Calls::Group::P2P {
namespace {

// Domain-separation labels. Every derived value in the protocol comes from a
// distinct label so no key is ever reused across roles.
constexpr std::string_view kLabelChain = "telegram-p2p/ratchet/chain";
constexpr std::string_view kLabelMessage = "telegram-p2p/ratchet/message";
constexpr std::string_view kLabelHeader = "telegram-p2p/ratchet/header";
constexpr std::string_view kLabelRoot = "telegram-p2p/ratchet/root";
constexpr std::string_view kLabelFingerprint
	= "telegram-p2p/ratchet/fingerprint";
constexpr std::string_view kLabelX3dhSalt = "telegram-p2p/x3dh/salt";
constexpr std::string_view kLabelX3dhInfo
	= "telegram-p2p/x3dh/shared-secret/v1";

/**
 * RAII wrapper so every early return releases its OpenSSL object.
 *
 * Takes a plain function pointer rather than a `free` overload, because
 * EVP_MD_CTX's deleter is a distinct type from EVP_PKEY's and overload
 * resolution would otherwise select the wrong one.
 */
template <typename T, void (*Free)(T *)>
class Unique {
public:
	explicit Unique(T *value = nullptr) : _value(value) {
	}
	~Unique() {
		if (_value) {
			Free(_value);
		}
	}
	Unique(const Unique &) = delete;
	Unique &operator=(const Unique &) = delete;
	Unique(Unique &&other) noexcept : _value(other._value) {
		other._value = nullptr;
	}

	T *get() const {
		return _value;
	}
	explicit operator bool() const {
		return _value != nullptr;
	}

private:
	T *_value;
};

using PkeyPtr = Unique<EVP_PKEY, EVP_PKEY_free>;
using PkeyCtxPtr = Unique<EVP_PKEY_CTX, EVP_PKEY_CTX_free>;
using MdCtxPtr = Unique<EVP_MD_CTX, EVP_MD_CTX_free>;
using CipherCtxPtr = Unique<EVP_CIPHER_CTX, EVP_CIPHER_CTX_free>;
using MacPtr = Unique<EVP_MAC, EVP_MAC_free>;
using MacCtxPtr = Unique<EVP_MAC_CTX, EVP_MAC_CTX_free>;

/** Wrap a raw 32-byte private key (X25519 or Ed25519) as an EVP_PKEY. */
[[nodiscard]] PkeyPtr ImportPrivateKey(int type, const Bytes &raw) {
	if (raw.size() != kKeySize) {
		return PkeyPtr(nullptr);
	}
	return PkeyPtr(EVP_PKEY_new_raw_private_key(
		type,
		nullptr,
		raw.data(),
		raw.size()));
}

/** Wrap a raw 32-byte public key as an EVP_PKEY. */
[[nodiscard]] PkeyPtr ImportPublicKey(int type, const Bytes &raw) {
	if (raw.size() != kKeySize) {
		return PkeyPtr(nullptr);
	}
	return PkeyPtr(EVP_PKEY_new_raw_public_key(
		type,
		nullptr,
		raw.data(),
		raw.size()));
}

/**
 * Generate a fresh raw keypair of the given type.
 *
 * @returns (secret, public) both 32 bytes, or nullopt on failure.
 */
[[nodiscard]] std::optional<std::pair<Bytes, Bytes>> GenerateKeyPair(int type) {
	PkeyPtr pkey(EVP_PKEY_Q_keygen(
		nullptr,
		nullptr,
		(type == EVP_PKEY_X25519) ? "X25519" : "ED25519"));
	if (!pkey) {
		return std::nullopt;
	}
	Bytes secret(kKeySize);
	Bytes publicKey(kKeySize);
	size_t secretSize = secret.size();
	size_t publicSize = publicKey.size();
	if (!EVP_PKEY_get_raw_private_key(
			pkey.get(),
			secret.data(),
			&secretSize)) {
		return std::nullopt;
	}
	if (!EVP_PKEY_get_raw_public_key(
			pkey.get(),
			publicKey.data(),
			&publicSize)) {
		return std::nullopt;
	}
	secret.resize(secretSize);
	publicKey.resize(publicSize);
	return std::make_pair(secret, publicKey);
}

/**
 * Domain-separated one-step HMAC-SHA256 derivation.
 *
 * Mirrors the reference TypeScript `derive`: the label plus a version byte is
 * the message, and the input secret is the HMAC key. Kept internal so the
 * ratchet can use it without exposing a second public primitive.
 */
[[nodiscard]] Bytes Derive(const Bytes &secret, std::string_view info) {
	Bytes message(info.begin(), info.end());
	message.push_back(1); // version byte, as in the reference implementation

	MacPtr mac(EVP_MAC_fetch(nullptr, "HMAC", nullptr));
	if (!mac) {
		return {};
	}
	MacCtxPtr ctx(EVP_MAC_CTX_new(mac.get()));
	if (!ctx) {
		return {};
	}
	// HMAC is a generic wrapper: the digest has to be named explicitly at init
	// time, and passing nullptr here fails rather than defaulting.
	char digest[] = "SHA256";
	OSSL_PARAM params[] = {
		OSSL_PARAM_construct_utf8_string(
			OSSL_MAC_PARAM_DIGEST,
			digest,
			0),
		OSSL_PARAM_construct_end(),
	};
	if (!EVP_MAC_init(
			ctx.get(),
			secret.data(),
			secret.size(),
			params)) {
		return {};
	}
	if (!EVP_MAC_update(ctx.get(), message.data(), message.size())) {
		return {};
	}
	Bytes out(EVP_MAX_MD_SIZE);
	size_t outLen = 0;
	if (!EVP_MAC_final(ctx.get(), out.data(), &outLen, out.size())) {
		return {};
	}
	out.resize(outLen);
	return out;
}

} // namespace

Bytes RootKeyFrom(const Bytes &secret) {
	return Derive(secret, kLabelRoot);
}

Bytes ChainKeyFrom(const Bytes &secret) {
	return Derive(secret, kLabelChain);
}

Bytes MessageKeyFrom(const Bytes &secret) {
	return Derive(secret, kLabelMessage);
}

Bytes HeaderKeyFrom(const Bytes &secret) {
	return Derive(secret, kLabelHeader);
}

Bytes FingerprintFrom(const Bytes &secret) {
	auto out = Derive(secret, kLabelFingerprint);
	if (out.size() > 8) {
		out.resize(8);
	}
	return out;
}

Bytes RandomBytes(int length) {
	Bytes out(static_cast<size_t>(std::max(0, length)));
	if (!out.empty()) {
		RAND_bytes(out.data(), static_cast<int>(out.size()));
	}
	return out;
}

Identity CreateIdentity() {
	const auto signing = GenerateKeyPair(EVP_PKEY_ED25519);
	const auto dh = GenerateKeyPair(EVP_PKEY_X25519);
	return Identity{
		.signingPublic = signing ? signing->second : Bytes{},
		.signingSecret = signing ? signing->first : Bytes{},
		.dhPublic = dh ? dh->second : Bytes{},
		.dhSecret = dh ? dh->first : Bytes{},
	};
}

Bytes Sign(const Bytes &data, const Bytes &secretKey) {
	auto pkey = ImportPrivateKey(EVP_PKEY_ED25519, secretKey);
	if (!pkey) {
		return {};
	}
	MdCtxPtr ctx(EVP_MD_CTX_new());
	if (!ctx) {
		return {};
	}
	if (!EVP_DigestSignInit(ctx.get(), nullptr, nullptr, nullptr, pkey.get())) {
		return {};
	}
	size_t sigLen = 0;
	if (!EVP_DigestSign(ctx.get(), nullptr, &sigLen, data.data(), data.size())) {
		return {};
	}
	Bytes signature(sigLen);
	if (!EVP_DigestSign(
			ctx.get(),
			signature.data(),
			&sigLen,
			data.data(),
			data.size())) {
		return {};
	}
	signature.resize(sigLen);
	return signature;
}

bool Verify(const Bytes &data, const Bytes &signature, const Bytes &publicKey) {
	if (signature.empty()) {
		return false;
	}
	auto pkey = ImportPublicKey(EVP_PKEY_ED25519, publicKey);
	if (!pkey) {
		return false;
	}
	MdCtxPtr ctx(EVP_MD_CTX_new());
	if (!ctx) {
		return false;
	}
	if (!EVP_DigestVerifyInit(ctx.get(), nullptr, nullptr, nullptr, pkey.get())) {
		return false;
	}
	return EVP_DigestVerify(
		ctx.get(),
		signature.data(),
		signature.size(),
		data.data(),
		data.size()) == 1;
}

std::optional<Bytes> SharedSecret(const Bytes &secretKey, const Bytes &peerPublic) {
	auto pkey = ImportPrivateKey(EVP_PKEY_X25519, secretKey);
	if (!pkey) {
		return std::nullopt;
	}
	auto peer = ImportPublicKey(EVP_PKEY_X25519, peerPublic);
	if (!peer) {
		return std::nullopt;
	}
	PkeyCtxPtr ctx(EVP_PKEY_CTX_new(pkey.get(), nullptr));
	if (!ctx) {
		return std::nullopt;
	}
	if (EVP_PKEY_derive_init(ctx.get()) <= 0) {
		return std::nullopt;
	}
	if (EVP_PKEY_derive_set_peer(ctx.get(), peer.get()) <= 0) {
		return std::nullopt;
	}
	Bytes secret(kKeySize);
	size_t len = secret.size();
	if (EVP_PKEY_derive(ctx.get(), secret.data(), &len) <= 0) {
		return std::nullopt;
	}
	secret.resize(len);
	// Reject an all-zero result: that is what a small-order point yields, and
	// accepting it would hand both peers a publicly known shared secret.
	static const Bytes kZero(kKeySize, 0);
	if (secret == kZero) {
		return std::nullopt;
	}
	return secret;
}

Bytes HKDF(const Bytes &secret, const Bytes &salt, std::string_view info, int length) {
	if (length <= 0) {
		return {};
	}
	Bytes out(static_cast<size_t>(length));
	PkeyCtxPtr ctx(EVP_PKEY_CTX_new_id(EVP_PKEY_HKDF, nullptr));
	if (!ctx) {
		return {};
	}
	if (EVP_PKEY_derive_init(ctx.get()) <= 0) {
		return {};
	}
	if (EVP_PKEY_CTX_set_hkdf_md(ctx.get(), EVP_sha256()) <= 0) {
		return {};
	}
	if (EVP_PKEY_CTX_set1_hkdf_salt(
			ctx.get(),
			salt.data(),
			static_cast<int>(salt.size())) <= 0) {
		return {};
	}
	Bytes infoBytes(info.begin(), info.end());
	if (EVP_PKEY_CTX_add1_hkdf_info(
			ctx.get(),
			infoBytes.data(),
			static_cast<int>(infoBytes.size())) <= 0) {
		return {};
	}
	// HKDF takes its input keying material through set1_hkdf_key. Passing a
	// peer key instead makes every derive call fail.
	if (EVP_PKEY_CTX_set1_hkdf_key(
			ctx.get(),
			secret.data(),
			static_cast<int>(secret.size())) <= 0) {
		return {};
	}
	size_t outLen = out.size();
	if (EVP_PKEY_derive(ctx.get(), out.data(), &outLen) <= 0) {
		return {};
	}
	out.resize(outLen);
	return out;
}

/**
 * X3DH mixed-input KDF over the concatenated DH shares and both identities.
 *
 * Both identities are mixed in so the secret is bound to *which* pair of
 * devices agreed on it, not merely to the DH shares.
 */
Bytes DeriveX3dh(
	const std::vector<Bytes> &shares,
	const Bytes &identityA,
	const Bytes &identityB) {
	Bytes input;
	for (const auto &share : shares) {
		input.insert(input.end(), share.begin(), share.end());
	}
	input.insert(input.end(), identityA.begin(), identityA.end());
	input.insert(input.end(), identityB.begin(), identityB.end());
	return HKDF(
		input,
		Bytes(kLabelX3dhSalt.begin(), kLabelX3dhSalt.end()),
		kLabelX3dhInfo);
}

std::optional<Bytes> Seal(
	const Bytes &plaintext,
	const Bytes &key,
	const Bytes &nonce,
	const Bytes &additionalData) {
	if (key.size() != kKeySize || nonce.size() != kNonceSize) {
		return std::nullopt;
	}
	CipherCtxPtr ctx(EVP_CIPHER_CTX_new());
	if (!ctx) {
		return std::nullopt;
	}
	if (!EVP_EncryptInit_ex(
			ctx.get(),
			EVP_chacha20_poly1305(),
			nullptr,
			key.data(),
			nonce.data())) {
		return std::nullopt;
	}
	// `len` is a single out-parameter that every EVP_EncryptUpdate overwrites,
	// including the AAD pass that writes no output at all. Keeping the AAD
	// length in a separate variable stops it from displacing the running
	// ciphertext length.
	int aadLen = 0;
	if (!additionalData.empty()
		&& !EVP_EncryptUpdate(
			ctx.get(),
			nullptr,
			&aadLen,
			additionalData.data(),
			static_cast<int>(additionalData.size()))) {
		return std::nullopt;
	}
	// +16 for the Poly1305 tag. In OpenSSL 3 the tag is emitted by
	// EVP_EncryptFinal_ex, not EVP_EncryptUpdate.
	Bytes out(plaintext.size() + 16);
	int len = 0;
	if (!EVP_EncryptUpdate(
			ctx.get(),
			out.data(),
			&len,
			plaintext.data(),
			static_cast<int>(plaintext.size()))) {
		return std::nullopt;
	}
	const auto total = len;
	int finalLen = 0;
	if (!EVP_EncryptFinal_ex(ctx.get(), out.data() + total, &finalLen)) {
		return std::nullopt;
	}
	out.resize(static_cast<size_t>(total + finalLen));
	return out;
}

std::optional<Bytes> Open(
	const Bytes &ciphertext,
	const Bytes &key,
	const Bytes &nonce,
	const Bytes &additionalData) {
	if (key.size() != kKeySize
		|| nonce.size() != kNonceSize
		|| ciphertext.size() < 16) {
		return std::nullopt;
	}
	CipherCtxPtr ctx(EVP_CIPHER_CTX_new());
	if (!ctx) {
		return std::nullopt;
	}
	if (!EVP_DecryptInit_ex(
			ctx.get(),
			EVP_chacha20_poly1305(),
			nullptr,
			key.data(),
			nonce.data())) {
		return std::nullopt;
	}
	// Same single-out-param hazard as Seal: keep the AAD length separate.
	int aadLen = 0;
	if (!additionalData.empty()
		&& !EVP_DecryptUpdate(
			ctx.get(),
			nullptr,
			&aadLen,
			additionalData.data(),
			static_cast<int>(additionalData.size()))) {
		return std::nullopt;
	}
	Bytes out(ciphertext.size());
	int len = 0;
	if (!EVP_DecryptUpdate(
			ctx.get(),
			out.data(),
			&len,
			ciphertext.data(),
			static_cast<int>(ciphertext.size()))) {
		return std::nullopt;
	}
	int finalLen = 0;
	if (!EVP_DecryptFinal_ex(ctx.get(), out.data() + len, &finalLen)) {
		// Authentication failed: wrong key, tampered ciphertext, or an
		// additional-data mismatch. Discard rather than return anything.
		return std::nullopt;
	}
	out.resize(static_cast<size_t>(len + finalLen));
	return out;
}

} // namespace Calls::Group::P2P
