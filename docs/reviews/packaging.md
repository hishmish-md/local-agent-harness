# Packaging release review

**Status: not evaluated.** Use this checklist for each release candidate. A pass applies only to the bundle digest, target OS/architecture, and upgrade path tested. Record those identifiers, the reviewer, date, and evidence location. An untested gate is not a pass.

## Offline installation

- List host prerequisites separately from bundled files. Include the installer, runtime, dependencies, local assets, and operator instructions needed for the advertised offline features. Identify optional model packs by version and digest; do not silently download a missing pack.
- Start with a clean supported host, empty caches, and only the declared prerequisites. Block external network access before copying the candidate from removable media. Keep local loopback available.
- Follow the shipped instructions: verify the bundle, install, start the harness, and complete one representative local task with the advertised offline configuration. Restart and repeat. Remove one required asset in a separate test: installation or startup must name the missing item without trying an online fallback.
- **Pass:** both runs return the expected result with no external connection attempts. Attach the prerequisite inventory, task input and expected output, installer logs, and network observations.

## Signed bundles

- Provision the verifier and trusted release key through an independent channel. A key or checksum supplied only by the candidate does not establish trust.
- Before executing bundled code, verify the signature over a manifest binding the release version, platform, and each payload path, size, and digest. Check the actual payload against it, including scripts and optional packs. Reject missing, extra, or modified files.
- Test the intact release, then separately test a changed payload, an unsigned manifest, and a manifest signed by an untrusted key. Use the documented offline trust policy for key rotation and revocation; record which trust snapshot was used.
- **Pass:** only the intact, authorized release installs. Every rejected case exits before running install hooks or changing the active installation. Retain the manifest digest, signer fingerprint, verifier results, and unchanged-state checks.

## Licensing review

- Generate an inventory from the final payload, not just the source dependency list. Cover transitive libraries, bundled runtimes and tools, model weights, tokenizers, datasets, and other assets actually shipped.
- For each item, record version or digest, provenance, applicable terms, intended use and distribution, required notices or accompanying materials, and their paths in the bundle. Review model terms separately from the license for the code that loads the model.
- **Pass:** the licensing reviewer reconciles the inventory to the signed manifest and signs off on the exact distribution. Unknown terms, unresolved redistribution rights, or missing required materials block shipment. Remove or replace the item, or obtain documented clearance; rebuild and review the resulting bundle.

## Upgrade and rollback acceptance

1. For each supported upgrade path, install the signed prior release offline. Seed representative configuration and persistent data, capture their logical contents and permissions, and record a successful local task. Keep the verified prior installer available offline.
2. Stop writes and take a restorable backup before migration. Upgrade using the candidate; check the reported version, configuration, data readability, permissions, and baseline task. Record the handling of writes made after upgrade; do not silently discard them.
3. Exercise the documented rollback with network access still blocked. If the old release cannot read migrated data, restore the matching pre-upgrade snapshot rather than opening the new schema with the old binary. Confirm the old version starts, the task succeeds, and restored data matches the baseline.
4. On disposable copies, interrupt the upgrade during staging and during migration. Follow the shipped recovery procedure. Verify that exactly one complete release becomes active and that no partially migrated state is served.

**Pass:** each path demonstrates successful upgrade, rollback, and interrupted-upgrade recovery. Attach before/after version and data checks, backup/restore logs, observed downtime, and any documented data-loss window accepted by the release owner. Block release if rollback depends on an online download, unverified media, or an untested backup.

## Decision record

| Gate | Result (pass / fail / not run) | Evidence and reviewer |
| --- | --- | --- |
| Offline installation | Not run | — |
| Signed bundles | Not run | — |
| Licensing review | Not run | — |
| Upgrade and rollback | Not run | — |

Release only when every applicable gate passes. If no prior release exists, record that fact and scope the first release to fresh installs rather than claiming upgrade support.
