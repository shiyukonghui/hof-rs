//! Permission enforcement: content-addressed tree hashing plus the role tool
//! allow/deny matrix.
//!
//! "Prevention" (view isolation) and "detection" (hash assertions) are both
//! mandatory: a copy can never stop an agent from writing to the real project
//! through an absolute path, so the before/after hash assertions are the
//! enforcement point (`DESIGN-DETAIL.md` §4.4).

use sha2::{Digest, Sha256};

/// Lowercase hex sha256 of arbitrary bytes.
pub fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}
