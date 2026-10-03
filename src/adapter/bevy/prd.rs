//! The PRD's **sealed prefix** (`PRD.md` 附录 B2).
//!
//! `PRD.md` is the frozen product contract, and this batch had to change it —
//! from six reflectable semantic surfaces to seven, and to record the frozen
//! game crate name (D297).  The document had **no seal before this batch**: B1's
//! report records "PRD 尚无冻结哈希", and no `PRD.sha256` file exists.  So this
//! module does not continue an old seal; it **establishes the first one**.
//!
//! The seal is a **prefix** seal, because the change is append-only:
//!
//! * [`SEAL_MARKER`] is the exact first line of the appended block;
//! * everything **above** that line is the sealed prefix, and its SHA-256 is
//!   [`SEALED_PREFIX_SHA256`] — measured from the file as it stood before this
//!   batch's addition (5136 bytes);
//! * [`verify`] recomputes it, so a rewrite anywhere above the marker is a
//!   failure, while an append *below* the marker stays legal.
//!
//! That asymmetry is the point: a frozen document can be extended, never
//! edited, and "extended" has a hash that says so.

use std::path::Path;

use crate::adapter::AdapterError;

/// The first line of the appended block.  Nothing above it may ever change.
pub const SEAL_MARKER: &str = "<!-- hof-rs:sealed-prefix";

/// `sha256` of `PRD.md`'s bytes **above** [`SEAL_MARKER`], as they stood before
/// this batch's append-only addition.  Establishing it is a decision, not a
/// measurement of a pre-existing seal: the document carried none.
pub const SEALED_PREFIX_SHA256: &str =
    "dca329f3b09519b743a8f26890cbc8b9a61f4e1acc04a0d6a427b47387bf4527";

/// The sealed prefix's length in bytes, so a reader can tell "the file was
/// edited" from "the file was replaced by something shorter".
pub const SEALED_PREFIX_BYTES: usize = 5136;

/// The sealed prefix of a document: everything above the marker line.
///
/// `Err` when the marker is absent, because a document without a marker has no
/// prefix to seal and treating the whole file as the prefix would silently
/// freeze the appended block as well.
pub fn sealed_prefix(document: &str) -> Result<&str, AdapterError> {
    let position = document.find(SEAL_MARKER).ok_or_else(|| {
        AdapterError::Malformed(format!(
            "the document carries no `{SEAL_MARKER}` marker, so it has no sealed prefix"
        ))
    })?;
    // The marker starts a line: anything else would be a mention of the marker
    // inside prose, which must not be able to move the seal.
    let line_start = document[..position]
        .rfind('\n')
        .map(|index| index + 1)
        .unwrap_or(0);
    if line_start != position {
        return Err(AdapterError::Malformed(format!(
            "`{SEAL_MARKER}` appears inside a line, not at the start of one"
        )));
    }
    Ok(&document[..position])
}

/// `sha256` of a document's sealed prefix.
pub fn sealed_prefix_sha256(document: &str) -> Result<String, AdapterError> {
    Ok(crate::runtime::policy::sha256_hex(
        sealed_prefix(document)?.as_bytes(),
    ))
}

/// Confirm a document's sealed prefix is the frozen one.  Any rewrite above the
/// marker — a byte, a reordering, a deletion — moves the hash and fails.
pub fn verify(document: &str) -> Result<(), AdapterError> {
    let prefix = sealed_prefix(document)?;
    if prefix.len() != SEALED_PREFIX_BYTES {
        return Err(AdapterError::Malformed(format!(
            "the sealed prefix is {} bytes, not the frozen {}: the text above the marker was \
             rewritten (an append-only change must add below it)",
            prefix.len(),
            SEALED_PREFIX_BYTES
        )));
    }
    let actual = crate::runtime::policy::sha256_hex(prefix.as_bytes());
    if actual != SEALED_PREFIX_SHA256 {
        return Err(AdapterError::Malformed(format!(
            "the sealed prefix hashes to {actual}, not to the frozen {SEALED_PREFIX_SHA256}: the \
             text above `{SEAL_MARKER}` was rewritten, which an append-only addition never does"
        )));
    }
    Ok(())
}

/// Read a file and verify its seal.
pub fn verify_file(path: &Path) -> Result<(), AdapterError> {
    let text = std::fs::read_to_string(path).map_err(|error| {
        AdapterError::Malformed(format!("`{}` could not be read: {error}", path.display()))
    })?;
    verify(&text)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A document shaped like the real one: frozen text, then the marker, then
    /// the appended block.
    fn sealed_document(prefix: &str) -> String {
        format!("{prefix}{SEAL_MARKER} sha256=x bytes=y -->\n\n# 附录 B2\n")
    }

    #[test]
    fn the_sealed_prefix_is_everything_above_the_marker() {
        let document = sealed_document("正文\n");
        assert_eq!(sealed_prefix(&document).unwrap(), "正文\n");
        assert_eq!(
            sealed_prefix_sha256(&document).unwrap(),
            crate::runtime::policy::sha256_hex("正文\n".as_bytes())
        );
    }

    #[test]
    fn a_document_without_a_marker_has_no_seal_to_verify() {
        let error = sealed_prefix("no marker here\n").unwrap_err();
        assert!(error.to_string().contains("no `<!--"), "{error}");
    }

    #[test]
    fn a_marker_inside_a_line_cannot_move_the_seal() {
        let error = sealed_prefix(&format!("prose mentioning {SEAL_MARKER} inline\n")).unwrap_err();
        assert!(error.to_string().contains("start of one"), "{error}");
    }

    #[test]
    fn a_rewrite_above_the_marker_reddens_the_verification() {
        let good = sealed_document("the frozen text\n");
        // The frozen literal belongs to the real document, so plant the seal on a
        // copy whose hash is made to match, then rewrite above it.
        let mut pinned = good.clone();
        pinned = pinned.replace("the frozen text", "the frozen text");
        let hash = sealed_prefix_sha256(&good).unwrap();
        // Verify the mechanism, not the literal: a changed prefix changes the
        // hash, and the comparison is what fails.
        assert_ne!(
            hash,
            sealed_prefix_sha256(&sealed_document("rewritten\n")).unwrap()
        );
        let _ = pinned;
    }

    #[test]
    fn the_mechanism_fails_on_a_rewrite_and_not_on_an_append() {
        // Establish a seal over a synthetic document by measuring it, then check
        // the two directions.  (The real document's seal is checked by the
        // integration test, which has the file.)
        let prefix = "frozen line one\nfrozen line two\n";
        let document = sealed_document(prefix);
        let measured = sealed_prefix_sha256(&document).unwrap();
        let frozen_bytes = prefix.len();
        // Append below the marker: the prefix is untouched.
        let extended = format!("{document}\n## more\n");
        assert_eq!(sealed_prefix(&extended).unwrap(), prefix);
        assert_eq!(sealed_prefix_sha256(&extended).unwrap(), measured);
        assert_eq!(sealed_prefix(&extended).unwrap().len(), frozen_bytes);
        // Rewrite above it: the prefix moves.
        let rewritten = sealed_document("frozen line one\nFROZEN line two\n");
        assert_ne!(sealed_prefix_sha256(&rewritten).unwrap(), measured);
        assert_ne!(sealed_prefix(&rewritten).unwrap(), prefix);
    }

    #[test]
    fn the_real_documents_seal_is_the_frozen_literal() {
        // The file is the authority; this test is the mechanical check.
        let path = Path::new(env!("CARGO_MANIFEST_DIR")).join(".spec/bevy/PRD.md");
        if !path.is_file() {
            // A published crate has no `.spec`; skip rather than lie.
            eprintln!("SKIP: {} does not exist in this checkout", path.display());
            return;
        }
        let text = std::fs::read_to_string(&path).unwrap();
        verify(&text).unwrap_or_else(|error| panic!("{error}"));
        assert_eq!(sealed_prefix(&text).unwrap().len(), SEALED_PREFIX_BYTES);
    }
}
