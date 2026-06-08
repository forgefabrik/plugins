#!/usr/bin/env python3
"""Normalize a generated PNG into a 64x64 black-background pixel sprite."""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path


def read_png(path: Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")

    pos = 8
    width = height = color_type = None
    raw = b""

    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        pos += 4
        chunk_type = data[pos : pos + 4]
        pos += 4
        chunk = data[pos : pos + length]
        pos += length + 4

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
            if bit_depth != 8 or interlace != 0 or color_type not in (2, 6):
                raise ValueError(
                    f"unsupported PNG format: bit={bit_depth} type={color_type} interlace={interlace}"
                )
        elif chunk_type == b"IDAT":
            raw += chunk
        elif chunk_type == b"IEND":
            break

    bpp = 4 if color_type == 6 else 3
    scan = zlib.decompress(raw)
    stride = width * bpp
    rows = []
    offset = 0
    previous = bytearray(stride)

    for _ in range(height):
        filter_type = scan[offset]
        offset += 1
        current = bytearray(scan[offset : offset + stride])
        offset += stride

        for x in range(stride):
            left = current[x - bpp] if x >= bpp else 0
            up = previous[x]
            up_left = previous[x - bpp] if x >= bpp else 0

            if filter_type == 1:
                current[x] = (current[x] + left) & 255
            elif filter_type == 2:
                current[x] = (current[x] + up) & 255
            elif filter_type == 3:
                current[x] = (current[x] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                prediction = left + up - up_left
                pa = abs(prediction - left)
                pb = abs(prediction - up)
                pc = abs(prediction - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                current[x] = (current[x] + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")

        rows.append(current)
        previous = current

    pixels = []
    for row in rows:
        out = []
        for x in range(width):
            index = x * bpp
            if bpp == 4:
                red, green, blue, alpha = row[index : index + 4]
                out.append((0, 0, 0) if alpha == 0 else (red, green, blue))
            else:
                out.append(tuple(row[index : index + 3]))
        pixels.append(out)

    return width, height, pixels


def write_png(path: Path, width: int, height: int, pixels):
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for red, green, blue in row:
            raw.extend((red, green, blue))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def background_like(color):
    red, green, blue = color
    black = red < 8 and green < 8 and blue < 8
    magenta_key = red > 180 and blue > 180 and green < 80
    return black or magenta_key


def normalize(source: Path, target: Path, kind: str):
    width, height, pixels = read_png(source)
    clean = [
        [(0, 0, 0) if background_like(pixel) else pixel for pixel in row]
        for row in pixels
    ]
    points = [
        (x, y)
        for y, row in enumerate(clean)
        for x, pixel in enumerate(row)
        if pixel != (0, 0, 0)
    ]
    if not points:
        write_png(target, 64, 64, [[(0, 0, 0)] * 64 for _ in range(64)])
        return

    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    box_width = max_x - min_x + 1
    box_height = max_y - min_y + 1

    sizes = {
        "infant": (34, 30, "center"),
        "sphere": (44, 44, "center"),
        "agent": (40, 46, "feet"),
        "tile": (56, 56, "center"),
    }
    target_width, target_height, placement = sizes[kind]
    scale = min(target_width / box_width, target_height / box_height)
    new_width = max(1, round(box_width * scale))
    new_height = max(1, round(box_height * scale))

    output = [[(0, 0, 0)] * 64 for _ in range(64)]
    offset_x = (64 - new_width) // 2
    offset_y = 31 - new_height // 2 if placement == "center" else 48 - new_height

    for yy in range(new_height):
        source_y = min_y + min(box_height - 1, int(yy / scale))
        for xx in range(new_width):
            source_x = min_x + min(box_width - 1, int(xx / scale))
            pixel = clean[source_y][source_x]
            if pixel == (0, 0, 0):
                continue
            x = offset_x + xx
            y = offset_y + yy
            if 0 <= x < 64 and 0 <= y < 64:
                output[y][x] = pixel

    write_png(target, 64, 64, output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument(
        "--kind", choices=["infant", "sphere", "agent", "tile"], default="agent"
    )
    args = parser.parse_args()

    normalize(args.source, args.target, args.kind)


if __name__ == "__main__":
    main()
