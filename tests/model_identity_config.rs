//! DR-14 — model identity is **configuration driven** (C9/C10/C11).
//!
//! Nothing here hard-codes a vendor model name: the shipped configuration
//! declares `wire_model_name`, and the assertion only checks generic
//! invariants.  Swapping models must be a configuration-only change.

use hof_rs::config::assert_model_identity;
use hof_rs::errors::{as_hof_error, HofError};
use serde_json::{json, Value};

fn generic_model() -> Value {
    json!({
        "model_name": "vendor-agnostic-model",
        "provider": "openai_compatible",
        "wire_model_name": "vendor-agnostic-model"
    })
}

/// Reading the shipped YAML through mini's own loader keeps this test honest:
/// it observes the file the runtime actually consumes.
fn shipped_model_section() -> Value {
    let merged = mini_swe_agent::get_config_from_spec("config/hoh.yaml").expect("config file");
    merged.get("model").cloned().unwrap_or(Value::Null)
}

#[test]
fn shipped_config_declares_a_wire_model_name_and_no_api_key() {
    let model = shipped_model_section();
    let wire = model
        .get("wire_model_name")
        .and_then(Value::as_str)
        .unwrap_or("");
    assert!(
        !wire.is_empty(),
        "config/hoh.yaml must declare a non-empty model.wire_model_name (DR-14); got {model}"
    );
    assert!(
        !model
            .get("model_name")
            .and_then(Value::as_str)
            .unwrap_or("")
            .is_empty(),
        "config/hoh.yaml must declare a non-empty model.model_name (DR-14)"
    );
    assert_eq!(
        model.get("provider").and_then(Value::as_str),
        Some("openai_compatible"),
        "model.provider must be explicit (C10)"
    );
    let key = model.get("api_key");
    assert!(
        key.is_none_or(|value| value.is_null() || value.as_str() == Some("")),
        "model.api_key must be empty; keys come from the environment (C11/DR-16); got {key:?}"
    );
}

#[test]
fn identity_assertion_rejects_a_non_empty_config_api_key() {
    let mut model = generic_model();
    model["api_key"] = json!("leaky-config-secret");
    let error = assert_model_identity(&model).expect_err("a config api_key must be rejected (C11)");
    assert!(matches!(error, HofError::ModelIdentityViolation { .. }));
    let text = error.to_string();
    assert!(text.contains("C11"), "reason must cite C11: {text}");
    assert!(
        !text.contains("leaky-config-secret"),
        "the violation must never echo key material: {text}"
    );
}

#[test]
fn identity_assertion_rejects_a_blank_wire_model_name() {
    let mut model = generic_model();
    model["wire_model_name"] = json!("");
    assert!(
        assert_model_identity(&model).is_err(),
        "an empty wire_model_name must be rejected (DR-14)"
    );
    let mut model = generic_model();
    model.as_object_mut().unwrap().remove("wire_model_name");
    assert!(
        assert_model_identity(&model).is_err(),
        "a missing wire_model_name must be rejected (DR-14)"
    );
}

#[test]
fn identity_assertion_rejects_a_blank_model_name() {
    let mut model = generic_model();
    model["model_name"] = json!("   ");
    assert!(
        assert_model_identity(&model).is_err(),
        "a blank model_name must be rejected (DR-14)"
    );
}

#[test]
fn identity_assertion_accepts_a_generic_openai_compatible_identity() {
    assert_model_identity(&generic_model()).expect("generic identity must pass");
}

#[test]
fn violation_message_carries_config_values_and_no_model_name() {
    let specs = vec![
        "config/hoh.yaml".to_string(),
        "model.provider=aliyun".to_string(),
    ];
    let error = hof_rs::config::load_config(&specs).expect_err("bad provider must be rejected");
    let hof = as_hof_error(&error).expect("typed error");
    assert!(matches!(hof, HofError::ModelIdentityViolation { .. }));
    let text = error.to_string();
    assert!(
        text.contains("aliyun"),
        "the message must carry the actual configuration value: {text}"
    );
    assert!(
        !text.contains("qwen"),
        "the violation must not know any concrete model name (DR-14): {text}"
    );
}
