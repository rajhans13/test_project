from __future__ import annotations

from pathlib import Path


LINE_HEIGHT = 16
START_X = 72
START_Y = 770
PAGE_WIDTH = 612
PAGE_HEIGHT = 792


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(text: str) -> bytes:
    lines = text.splitlines()
    content_lines = ["BT", "/F1 12 Tf", f"{START_X} {START_Y} Td"]

    for line in lines:
        if line.strip() == "":
            content_lines.append(f"0 -{LINE_HEIGHT} Td")
            continue
        escaped = pdf_escape(line)
        content_lines.append(f"({escaped}) Tj")
        content_lines.append(f"0 -{LINE_HEIGHT} Td")

    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("utf-8")
    stream_object = (
        f"<< /Length {len(content_stream)} >>\nstream\n".encode("utf-8")
        + content_stream
        + b"\nendstream"
    )

    def obj(num: int, data: bytes) -> bytes:
        return b"%d 0 obj\n" % num + data + b"\nendobj\n"

    objs = [
        obj(1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        obj(
            3,
            (
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 "
                + str(PAGE_WIDTH).encode("ascii")
                + b" "
                + str(PAGE_HEIGHT).encode("ascii")
                + b"] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>"
            ),
        ),
        obj(4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
        obj(5, stream_object),
    ]

    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = []
    for object_bytes in objs:
        offsets.append(len(pdf))
        pdf += object_bytes

    xref_offset = len(pdf)
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    for offset in offsets:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF"
    )

    return pdf + b"".join(xref) + trailer


def main() -> None:
    input_path = Path("docs/soe2025_migration_plan.md")
    output_path = Path("docs/soe2025_migration_plan.pdf")
    text = input_path.read_text(encoding="utf-8")
    pdf_bytes = build_pdf(text)
    output_path.write_bytes(pdf_bytes)


if __name__ == "__main__":
    main()
