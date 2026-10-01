use std::process::ExitCode;

#[tokio::main]
async fn main() -> ExitCode {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .with_target(false)
        .init();
    let code = hof_rs::cli::main_entry().await;
    // DR-73 ③(b) / D280(b): the round directory must carry the **process** exit
    // code too.  The other two readings (`runs/<id>/exit_code`,
    // `meta.json.exit_code`) are written by `finalize_run`; the third one used to
    // live only in whatever wrapper launched `hoh`, which is exactly the evidence
    // hole `TASK-SMOKE-T10-ACCEPTANCE.md` T10A-4 measured.  `ExitCode` does not
    // expose its number, so the code is recorded where it is computed — inside
    // `cli_impl::run`, next to the two artifacts it has to agree with — against
    // the run directory the runtime exported for exactly this purpose.
    hof_rs::cli_impl::record_process_exit_code_from_env();
    code
}
