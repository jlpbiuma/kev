"""Entrypoint KEV con host configurable (Docker necesita 0.0.0.0).

Replica ``kev.serve:main`` pero permite ``--host``.
"""
from __future__ import annotations

import argparse
import os
from dataclasses import replace

import torch
import uvicorn

from kev.checkpoint import Checkpoint, LoadOptions, is_hub_id
from kev.device import default_device
from kev.serve import Server, app


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/kev")
    ap.add_argument("--fallback", default="runs/smoke")
    ap.add_argument("--port", type=int, default=8009)
    ap.add_argument("--host", default=os.environ.get("KEV_HOST", "0.0.0.0"))
    a = ap.parse_args()

    run = a.run if is_hub_id(a.run) or os.path.exists(f"{a.run}/head.pt") else a.fallback
    if run != a.run:
        print(f"{a.run} not found, falling back to {run}")

    dev = default_device()
    opts = LoadOptions.from_env()
    if dev == "mps" and opts.attn is None:
        opts = replace(opts, attn="sdpa")
    if dev != "cpu" and opts.dtype is None:
        opts = replace(opts, dtype=torch.bfloat16)
    if dev == "cuda" and opts.cuda_graphs is None:
        opts = replace(opts, cuda_graphs=True)
    if opts.backend is None:
        opts = replace(opts, backend="auto")

    ck = Checkpoint(run)
    tok, model = ck.load(dev, opts)
    app.state.server = Server(ck, tok, model, dev)
    print(
        f"serving {ck.requested} ({ck.path}) on {dev} via {model.backend} "
        f"({model.dtype}) {a.host}:{a.port}"
    )
    uvicorn.run(app, host=a.host, port=a.port)


if __name__ == "__main__":
    main()
