import os, struct, pathlib

def scan_binaries(root_dir):
    binary_exts = {'.dat', '.bin', '.big', '.db', '.ast', '.sbs', '.rx3', '.msh', '.skl', '.anm'}
    report = []
    for path in pathlib.Path(root_dir).rglob('*'):
        if path.is_file() and path.suffix.lower() in binary_exts:
            try:
                with open(path, 'rb') as f:
                    header = f.read(64)
                magic_ascii = ''.join(chr(b) if 32 <= b < 127 else '.' for b in header[:16])
                hex_preview = header[:32].hex(' ')
                report.append(f"FILE: {path.relative_to(root_dir)} | SIZE: {path.stat().st_size} bytes\n  MAGIC: {magic_ascii}\n  HEX32: {hex_preview}\n")
            except Exception as e:
                report.append(f"FILE: {path} | ERROR: {e}\n")
    out_file = pathlib.Path(root_dir) / "docs" / "binary_headers_raw.txt"
    out_file.write_text("\n".join(report), encoding="utf-8")
    print(f"Scanned {len(report)} binary files. Saved header dump to {out_file}")

if __name__ == "__main__":
    scan_binaries(r"C:\Users\junai\Desktop\legacy_sim_research")
