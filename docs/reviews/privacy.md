# Offline privacy review

**Release criterion, not a test result.** An offline run must finish using staged local resources, or stop with a local error. It must not contact another machine, even to resolve a name or check whether a service exists. A failed connection can still disclose information. This review covers network disclosure; it does not certify local storage security.

## Threat model and enforcement

Protect prompts, files, model inputs and outputs, credentials, and identifying metadata such as hostnames and request timing. Treat models, plugins, tools, subprocesses and their inputs as untrusted. Include model startup, telemetry, updates, crash reporting and deferred work. Trust the host kernel, isolation configuration and observer; a compromised administrator or kernel is outside this claim.

Enforce default-deny at the OS isolation boundary **before launching any application code**. Cover the launcher, embedded inference runtime, shell, native executables, grandchildren and detached workers until teardown. A language-level socket guard or environment flag is not the boundary. Do not grant workloads privileges to change policy. Permit only documented local OS pipes; loopback network traffic is not an exception. Do not expose host services, shared folders or IPC brokers that can forward requests or queue uploads. If containment or local artifacts are unavailable, stop. There is no prompt, flag, retry, remote fallback or child-process exception that may relax this policy.

## Packet-level acceptance gates

Use an isolated, disposable test environment, synthetic inputs and a controlled local network with no Internet route. Run each gate on every supported OS/backend. Keep the production deny policy in force throughout candidate runs.

| Gate | Procedure | Required evidence |
| --- | --- | --- |
| Observer validity | Inventory physical, virtual, tunnel and loopback interfaces. Begin full-packet capture before launch at the workload boundary and independently on the test network. From a separate calibration workload on the same observed path, send a labeled packet to the test receiver; verify both observers see it. | Interface and capture configuration, timestamps and calibration packet. Missing coverage, capture drops or a failed control invalidate the run. |
| Normal operation | Exercise cold start, local inference, tool execution and clean shutdown. Repeat with missing model files and a failing tool. Continue observation through worker teardown; check for queued retries or surviving workers. | Expected local output or explicit local error. Zero workload-originated non-loopback packets of any protocol, zero loopback flows and zero attempted network connections in OS audit events. |
| Child containment | In a separate negative-control run, have the parent, a native child and a grandchild each attempt controlled IPv4 and IPv6 TCP, UDP and name resolution against test-only destinations. Include a detached worker if launch is supported. | OS process and deny events identify each probe; no probe packet reaches the external boundary or receiver. No system resolver or host broker emits traffic on the workload's behalf. Success, unexplained silence or a surviving worker fails the gate. |
| No bypass or downgrade | Request a remote provider while offline, configure a test proxy, and simulate unavailable enforcement before startup. | Configuration is rejected or remains contained; unavailable enforcement prevents workload launch. No remote attempt or deferred upload occurs. |

Record build and policy identifiers, fixture, process tree, capture interval, packet counts, deny events and verdict per gate. Use a dedicated quiet test boundary; never subtract unexplained traffic as background. Correlate captures with OS events because packets alone cannot identify a process or reveal an attempt blocked before transmission. Any unexplained packet, missing evidence or untested supported backend blocks sign-off. Store captures locally with restricted access; never use real prompts or credentials as fixtures.
