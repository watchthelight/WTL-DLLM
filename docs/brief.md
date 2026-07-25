---
title: "brief"
author: "<wtl>"
project: wtl-dllm
tags: [docs, product, brief]
---

# Brief

## The itch

Diffusion language models generate text by unmasking tokens over a series of refinement steps instead of writing left to right. That process is genuinely fun to watch — and almost nobody gets to watch it, because the open models that work (LLaDA, Dream) are 8B-parameter machines that need datacenter GPUs, and the demos that run anywhere are cloud toys. I want the whole loop on my own laptop: train it here, run it here, and see every denoising step render live. Math is the task because answers are checkable — no vibes-based eval, the answer is either 105 or it isn't.

## What exists

The 8B open models can't be trained or even comfortably fine-tuned on consumer hardware; their issue trackers are a catalog of OOMs and 30-hour eval runs. At the other end, tiny-diffusion (10.7M params, char-level Shakespeare) proves the minimal recipe works on small hardware, but it doesn't do math and doesn't ship a real UI. Nothing occupies the corner this project aims at: laptop-trained, math-focused, watchable.

## The bet

Two research results make the corner look reachable. First, the 2024 convergence (MDLM, MD4, RADD, and the time-agnostic proof, four groups independently) showed masked diffusion training is just BERT-style masked cross-entropy with a variable mask rate and a 1/t weight — a vanilla bidirectional transformer, about five changes off nanoGPT. Second, TinyStories showed that restricting the domain hard enough lets single-digit-million-parameter models do coherent work. Templated arithmetic is about as restricted as a domain gets, and the training data is free — a seeded generator can emit unlimited exact problems.

## The honest risk

Nobody has documented a from-scratch diffusion model trained on laptop-class compute that produces anything but gibberish. Both public attempts failed — one of them using exactly the recipe above. So coherent output is not an assumption here; it's gate number one, with an autoregressive twin trained on the same data as the control, and a fallback path (fine-tuning a small encoder) if the mainline stalls. The plan treats this as an experiment with instruments, not a product with a ship date.

## What done looks like

Three gates. G1: the model emits well-formed answers at all. G2: it actually solves level-1 arithmetic on perturbed held-out problems, with the real number reported whatever it is. G3: the live demo — server, browser, starfield, and a grid of tokens resolving from noise to `47+58=105` while you watch. Everything else (more levels, infilling demos, ordering experiments) builds on those three.
