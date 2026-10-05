//! Round-4 repair — the BRP client's connection pool must not cross a process
//! boundary, and this file reproduces the failure it caused.
//!
//! Round 3's passes 2 and 3 both failed their **first** battery call at the
//! transport layer (`BRP transport failure to http://127.0.0.1:15702/: transport
//! failure`, call `0001-bevy_grounded.json` in each pass) while pass 1 — the only
//! pass whose client had never talked to anything — did not.  The mechanism is
//! the one this file pins with real loopback sockets:
//!
//! 1. a BRP client pools a keep-alive connection after a successful call;
//! 2. the server it was talking to goes away (a game process is stopped, and the
//!    next launch is a different process);
//! 3. the next call through the **same** client reuses the pooled socket and
//!    fails at the transport layer, having reached nothing;
//! 4. a client rebuilt for the new process succeeds on its first call.
//!
//! The fix is [`hof_rs::adapter::bevy::BevyAdapter::client_generation`]: a launch
//! is a process boundary, and `start` rebuilds the observing client.  This file
//! pins the transport behaviour; the adapter's own test pins that `start` really
//! rebuilds.

use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use hof_rs::adapter::bevy::brp::BrpClient;

/// A BRP-shaped HTTP server that answers every request with a **keep-alive**
/// reply and then closes the connection.
///
/// It is deliberately the misbehaving peer a stopped process is: the client
/// cannot tell the socket is dead until it tries to use it, which is exactly the
/// state a pooled connection is in after its process exits.
struct KeepAliveThenClose {
    addr: std::net::SocketAddr,
    stop: Arc<AtomicBool>,
    served: Arc<std::sync::atomic::AtomicUsize>,
    handle: Option<thread::JoinHandle<()>>,
}

impl KeepAliveThenClose {
    fn spawn() -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").expect("a free loopback port");
        listener
            .set_nonblocking(true)
            .expect("the listener is nonblocking");
        let addr = listener.local_addr().expect("a bound address");
        let stop = Arc::new(AtomicBool::new(false));
        let served = Arc::new(std::sync::atomic::AtomicUsize::new(0));
        let handle = {
            let stop = Arc::clone(&stop);
            let served = Arc::clone(&served);
            thread::spawn(move || {
                while !stop.load(Ordering::SeqCst) {
                    match listener.accept() {
                        Ok((stream, _)) => {
                            let _ = stream.set_nonblocking(false);
                            let _ = stream.set_read_timeout(Some(Duration::from_millis(500)));
                            served.fetch_add(1, Ordering::SeqCst);
                            answer_and_close(stream);
                        }
                        Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                            thread::sleep(Duration::from_millis(2));
                        }
                        Err(_) => break,
                    }
                }
            })
        };
        Self {
            addr,
            stop,
            served,
            handle: Some(handle),
        }
    }

    fn endpoint(&self) -> String {
        format!("http://{}/", self.addr)
    }

    fn connections(&self) -> usize {
        self.served.load(Ordering::SeqCst)
    }
}

impl Drop for KeepAliveThenClose {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::SeqCst);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

/// Read one HTTP request, answer it, and **abort** the socket — a reset, not a
/// graceful close.
///
/// The abort matters and was measured: a socket closed with a FIN is detected by
/// the client's pool (or retried) and the next call silently opens a new
/// connection, while a socket reset while the pooled entry is live is what a
/// killed game leaves behind — and that is the failure round 3 recorded.  The
/// real-game corroboration is `tests/brp_real_handover.rs`.
fn answer_and_close(mut stream: TcpStream) {
    let mut buffer = Vec::new();
    let mut chunk = [0u8; 4096];
    let header_end = loop {
        match stream.read(&mut chunk) {
            Ok(0) => return,
            Ok(read) => buffer.extend_from_slice(&chunk[..read]),
            Err(_) => return,
        }
        if let Some(position) = find(&buffer, b"\r\n\r\n") {
            break position;
        }
    };
    let headers = String::from_utf8_lossy(&buffer[..header_end]).to_string();
    let length = headers
        .lines()
        .find_map(|line| {
            let (name, value) = line.split_once(':')?;
            name.eq_ignore_ascii_case("content-length")
                .then(|| value.trim().parse::<usize>().ok())
                .flatten()
        })
        .unwrap_or(0);
    while buffer.len() < header_end + 4 + length {
        match stream.read(&mut chunk) {
            Ok(0) => break,
            Ok(read) => buffer.extend_from_slice(&chunk[..read]),
            Err(_) => break,
        }
    }
    let body = String::from_utf8_lossy(&buffer[header_end + 4..]).to_string();
    let id = serde_json::from_str::<serde_json::Value>(&body)
        .ok()
        .and_then(|value| value.get("id").cloned())
        .unwrap_or(serde_json::Value::from(1));
    let reply = serde_json::json!({
        "jsonrpc": "2.0",
        "id": id,
        "result": {"value": {"frames": 1}},
    })
    .to_string();
    let response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\
         Connection: keep-alive\r\n\r\n{}",
        reply.len(),
        reply
    );
    let _ = stream.write_all(response.as_bytes());
    let _ = stream.flush();
    // SO_LINGER 0: the socket dies with a reset, like a killed process's, instead
    // of a FIN that a pool can notice.  The failure this reproduces is the one
    // round 3 recorded.
    reset_on_close(&stream);
}

/// Put the socket back to abortive close, so the peer sees a reset.
///
/// `TcpStream::set_linger` is not stable, so the one `setsockopt` it wraps is
/// declared here — the same way `tools::endpoint` declares the one `kernel32`
/// call it needs rather than taking a dependency for a single boolean.  Off
/// Windows the helper is a no-op and the test says it measured nothing.
#[cfg(windows)]
fn reset_on_close(stream: &TcpStream) {
    use std::os::windows::io::AsRawSocket;

    #[repr(C)]
    struct Linger {
        onoff: u16,
        linger: u16,
    }

    #[link(name = "ws2_32")]
    extern "system" {
        fn setsockopt(socket: usize, level: i32, name: i32, value: *const u8, length: i32) -> i32;
    }

    const SOL_SOCKET: i32 = 0xFFFF;
    const SO_LINGER: i32 = 0x0080;
    let linger = Linger {
        onoff: 1,
        linger: 0,
    };
    unsafe {
        setsockopt(
            stream.as_raw_socket() as usize,
            SOL_SOCKET,
            SO_LINGER,
            &linger as *const Linger as *const u8,
            std::mem::size_of::<Linger>() as i32,
        );
    }
}

#[cfg(not(windows))]
fn reset_on_close(_stream: &TcpStream) {}

fn find(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack
        .windows(needle.len())
        .position(|window| window == needle)
}

fn read_frames(client: &BrpClient) -> Result<u64, String> {
    client
        .call(
            "world.get_resources",
            Some(serde_json::json!({"resource": "hof_game::contract::FrameCounter"})),
        )
        .map(|value| {
            value
                .get("value")
                .and_then(|inner| inner.get("frames"))
                .and_then(serde_json::Value::as_u64)
                .unwrap_or(0)
        })
        .map_err(|error| error.to_string())
}

/// The defect, reproduced: one client, two processes' worth of server — the
/// second call goes out on the pooled socket and fails at the transport layer.
#[test]
fn a_pooled_connection_to_a_closed_peer_fails_the_next_call() {
    if !cfg!(windows) {
        println!("abortive close (SO_LINGER 0) is only set on Windows; nothing was measured");
        return;
    }
    let server = KeepAliveThenClose::spawn();
    let client = BrpClient::new(server.endpoint(), Duration::from_secs(5));
    let first = read_frames(&client);
    assert_eq!(
        first,
        Ok(1),
        "the first call opens the connection: {first:?}"
    );
    assert_eq!(server.connections(), 1, "one connection was opened");
    let second = read_frames(&client);
    assert!(
        second.is_err(),
        "the pooled socket is dead, so the next call must fail at the transport layer: {second:?}"
    );
    assert!(
        second.as_ref().unwrap_err().contains("transport"),
        "the failure is the transport class round 3 recorded: {second:?}"
    );
    assert_eq!(
        server.connections(),
        1,
        "the failure came from reusing the pooled socket, not from opening a new one"
    );
}

/// The repair, pinned at the client level: a client built for the new process
/// succeeds on its first call, because its pool holds nothing from the old one.
#[test]
fn a_client_rebuilt_for_the_new_process_succeeds_on_its_first_call() {
    let server = KeepAliveThenClose::spawn();
    let stale = BrpClient::new(server.endpoint(), Duration::from_secs(5));
    assert_eq!(read_frames(&stale), Ok(1));
    assert!(
        read_frames(&stale).is_err(),
        "the stale client is now poisoned"
    );
    let fresh = BrpClient::new(server.endpoint(), Duration::from_secs(5));
    assert_eq!(
        read_frames(&fresh),
        Ok(1),
        "the client for the new process must not inherit the dead socket"
    );
    assert_eq!(server.connections(), 2, "the fresh client opened its own");
}
