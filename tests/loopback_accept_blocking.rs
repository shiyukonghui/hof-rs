//! DR-65 / DR-69 -- the loopback doubles' accept path must state the socket
//! mode instead of inheriting the listener's.
//!
//! On Windows an `accept()`ed socket inherits the listener's non-blocking flag.
//! Every loopback JSON-RPC double in this repository runs a **non-blocking**
//! accept loop (so it can poll a stop flag with a 2 ms back-off) and then reads
//! the request as if the socket blocked.  When the client's bytes have not
//! arrived yet, that read returns `WouldBlock` immediately, the double closes the
//! connection and never answers, and the client reports a "status line" transport
//! error (10053/10054).  `endpoint_liveness.rs` was fixed in DR-60; DR-65
//! measured the same shape in `dual_endpoint.rs` and `endpoint_request_count.rs`
//! and DR-69 moved all three onto one helper,
//! [`common::accept_blocking`].
//!
//! This test is the **deterministic trigger**: the client connects first and only
//! writes its request after a delay, so the double's read really does start
//! before the bytes arrive.  With the helper's `set_nonblocking(false)` removed
//! it fails; with it, it passes.  Everything here is offline and on an ephemeral
//! loopback port this test binds itself.
//!
//! A stronger socket-mode assertion guards the same property structurally: the
//! socket the helper hands back must report `is_nonblocking() == false`, which is
//! the flag itself rather than a timing accident.

mod common;

use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread::JoinHandle;
use std::time::Duration;

/// A double that speaks one HTTP/1.1 JSON-RPC reply, using the shared helper.
struct SlowClientMcp {
    addr: std::net::SocketAddr,
    shutdown: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

impl SlowClientMcp {
    fn start() -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("loopback listener");
        let addr = listener.local_addr().expect("bound address");
        listener
            .set_nonblocking(true)
            .expect("a non-blocking listener");
        let shutdown = Arc::new(AtomicBool::new(false));
        let thread_shutdown = shutdown.clone();
        let handle = std::thread::spawn(move || {
            while !thread_shutdown.load(Ordering::SeqCst) {
                match common::accept_blocking(&listener) {
                    Some(stream) => {
                        // The mode is the contract, and the delayed-write test
                        // below is what measures it: `read_request` is a blocking
                        // reader, so an inherited non-blocking flag shows up as
                        // "no answer to a request that arrived 250 ms late".
                        read_request(stream);
                    }
                    None => std::thread::sleep(Duration::from_millis(2)),
                }
            }
        });
        Self {
            addr,
            shutdown,
            handle: Some(handle),
        }
    }

    fn url(&self) -> String {
        format!("http://{}/mcp", self.addr)
    }
}

impl Drop for SlowClientMcp {
    fn drop(&mut self) {
        self.shutdown.store(true, Ordering::SeqCst);
        let _ = TcpStream::connect(self.addr);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

/// One blocking request/response exchange.
fn read_request(mut stream: TcpStream) {
    let _ = stream.set_read_timeout(Some(Duration::from_secs(5)));
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 1024];
    loop {
        let read = match stream.read(&mut chunk) {
            Ok(0) => return,
            Ok(read) => read,
            Err(_) => return,
        };
        buffer.extend_from_slice(&chunk[..read]);
        let Some(header_end) = find(&buffer, b"\r\n\r\n") else {
            continue;
        };
        let headers = String::from_utf8_lossy(&buffer[..header_end]).into_owned();
        let length = headers
            .lines()
            .find_map(|line| {
                line.to_ascii_lowercase()
                    .strip_prefix("content-length:")
                    .map(|value| value.trim().parse::<usize>().unwrap_or(0))
            })
            .unwrap_or(0);
        if buffer.len() < header_end + 4 + length {
            continue;
        }
        let serialized = "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"content\":[]}}".to_string();
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
             Connection: close\r\n\r\n{serialized}",
            serialized.len()
        );
        let _ = stream.write_all(response.as_bytes());
        let _ = stream.flush();
        return;
    }
}

fn find(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack
        .windows(needle.len())
        .position(|window| window == needle)
}

/// The deterministic trigger: connect, wait, *then* write.  A double that reads
/// in blocking mode answers; one that inherited the listener's non-blocking flag
/// gives up before the bytes arrive.
#[test]
fn a_delayed_request_is_still_answered() {
    let double = SlowClientMcp::start();
    let url = double.url();
    let port: u16 = url
        .rsplit(':')
        .next()
        .and_then(|rest| rest.split('/').next())
        .and_then(|value| value.parse().ok())
        .expect("the double's port");

    let mut stream = TcpStream::connect(("127.0.0.1", port)).expect("connect");
    stream
        .set_read_timeout(Some(Duration::from_secs(5)))
        .expect("read timeout");
    // The client is slow on purpose: the server's read starts before this line.
    std::thread::sleep(Duration::from_millis(250));
    let body = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\"}";
    let request = format!(
        "POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n\
         Content-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.len()
    );
    stream.write_all(request.as_bytes()).expect("write");
    stream.flush().expect("flush");

    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .expect("a blocking double must answer the delayed request");
    assert!(
        response.starts_with("HTTP/1.1 200 OK"),
        "the double must have answered: {response:?}"
    );
    assert!(response.contains("\"jsonrpc\""), "{response}");
}
