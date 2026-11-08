"""Build submission.zip from product/superagent/ and print SHA-256 hashes.

Mirrors the notebook's writer: the four FILES at the zip root, nothing else.
Fixed timestamps make the zip byte-reproducible across machines.
"""
import hashlib
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).parent / "superagent"
FILES = ["agent.yaml", "configs/sampling.yaml", "eval_config.yaml", "prompts/system.md"]
OUT = pathlib.Path("submission.zip")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            data = (ROOT / name).read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
            print(f"{sha(data)[:16]}  {name}")
    print(f"{sha(OUT.read_bytes())}  {OUT}")


if __name__ == "__main__":
    main()
