"""Recompute the chain from the files on disk and compare it to ``PROVENANCE.json``.

This is the executable proof, not a claim. It exits non-zero if any sealed byte
changed, and localises the drift to a stage and to the individual files.

The environment fingerprint is compared as CONTEXT only: ``artifact_root`` is
environment-independent by construction, so a different interpreter cannot
invalidate the seal.

Usage: python scripts/verify_chain.py   # exit 0 = intact, exit 1 = tampered
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from build_chain import compute_provenance
from hash_utils import environment_fingerprint, sha256_hex

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    """Return 0 when the recomputed chain matches the sealed one, else 1."""
    sealed_path = ROOT / "PROVENANCE.json"
    if not sealed_path.exists():
        print("[FAIL] PROVENANCE.json missing -- run scripts/build_chain.py first")
        return 1
    sealed = json.loads(sealed_path.read_text(encoding="utf-8"))
    now = compute_provenance()
    ok = now["artifact_root"] == sealed["artifact_root"]

    if ok:
        print(f"[PASS] artifact_root matches ({now['artifact_root'][:16]}...)")
    else:
        print("[FAIL] artifact_root MISMATCH -- a sealed file changed")
        print(f"       sealed:     {sealed['artifact_root']}")
        print(f"       recomputed: {now['artifact_root']}")
        for s_now, s_old in zip(now["stages"], sealed["stages"], strict=False):
            if s_now["hash"] == s_old["hash"]:
                continue
            print(f"       -> stage '{s_now['name']}' differs")
            for rel, h in s_now["leaves"].items():
                was = s_old["leaves"].get(rel)
                if was is None:
                    print(f"          + added:   {rel}")
                elif was != h:
                    print(f"          ~ changed: {rel}")
            for rel in s_old["leaves"]:
                if rel not in s_now["leaves"]:
                    print(f"          - removed: {rel}")

    env_hash = sha256_hex(
        json.dumps(environment_fingerprint(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    )
    same = env_hash == sealed.get("sealed_by_interpreter", {}).get("sha256")
    print(
        "[INFO] "
        + (
            "same interpreter that signed the seal"
            if same
            else "different interpreter than the signer -- expected; the root is portable"
        )
    )
    print("\n" + "=" * 56)
    print("CHAIN INTACT" if ok else "CHAIN VIOLATED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
