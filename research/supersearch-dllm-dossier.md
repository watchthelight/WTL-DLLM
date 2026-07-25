# Building a Local Diffusion Language Model for Math: Supersearch Research Dossier

> Generated: 2026-07-25
> Mode: Exhaustive
> Quality Gate: PASS
> Sources Included: ~85 unique URLs (317 raw findings across 16 aspects)
> S/A-Tier Sources: ~30 (defensible tier assignments after audit correction)
> Raw data: `research/raw/` (full workflow result, per-aspect findings, claims digest, sources appendix)

## Executive Summary

Discrete diffusion language modeling went from a theoretical curiosity (D3PM, 2021) to a commercially contested architecture (Mercury 2, Gemini Diffusion, DiffusionGemma, Nemotron tri-mode) in five years, and along the way the field did something unusual: every major theoretical advance *removed* machinery instead of adding it. The 2024 convergence — MDLM (Cornell), MD4 (DeepMind), RADD (ML-GSAI), and Zheng et al., arriving from four directions — proved that absorbing-state masked diffusion reduces exactly to a BERT-style masked cross-entropy loss with a random mask rate t ~ U[0,1] and a 1/t weighting, and that time conditioning is unnecessary. The entire model is: a vanilla bidirectional transformer, one reserved [MASK] token, and an iterative unmasking loop at inference. This simplicity is the single most important fact for a from-scratch build: the diff from a nanoGPT-style codebase is roughly five changes.

The build target — a from-scratch diffusion LM trained and run on a laptop, solving math, with a real-time denoising UI — sits in an *unsampled corner* of the evidence space. Capability evidence (MGDM's 91.5% Countdown at 85M params; Diffusion-of-Thought's 100% on 4×4/5×5 multiplication) comes from datacenter training budgets. Feasibility evidence (tiny-diffusion: 10.7M params, 365 lines, ~20 A100-minutes) comes from char-level Shakespeare with no math. The only two documented laptop from-scratch attempts (Goedecke's 5-minute M4 run; boesch.dev's 2-hour M2 Air run — the latter already using the recommended masked-diffusion recipe) both produced gibberish. No laptop-trained from-scratch diffusion model with nontrivial math accuracy exists anywhere in the record. The project is therefore an evidence-guided experiment with a real gibberish-output risk, not a validated recipe — and must be planned with milestone gates, an autoregressive twin baseline for every claim, and coherent output treated as the first success criterion rather than an assumption.

Math is simultaneously diffusion's best showcase and its worst case. Small diffusion models genuinely crush same-size AR models on templated constraint/search tasks (Countdown, Sudoku, fixed-format multiplication) when trained in-task, and masked diffusion structurally solves infilling (14% recovery vs ~0% for AR at 288M params) and the reversal curse. But sequential chain-of-thought arithmetic is the documented worst case for parallel decoding: theory says whole-answer correctness needs denoising steps scaling linearly with length, GSM8K accuracy collapses at even 2 tokens/step, and confidence-ordered decoding trends left-to-right on math anyway — "The Flexibility Trap" (ICML 2026) found best math accuracy by *forcing* left-to-right decoding. The honest product story is the mechanism and the visualization, never speed, and the honest demo portfolio leans on infilling and constraint tasks where bidirectionality genuinely differs from AR.

The visualization itself is the lowest-risk component: at least five independent implementations exist (LLaDA's Gradio app, multimodalart's Space with a complete copyable per-step token/color state recipe, llama.cpp's `--diffusion-visual`, simonw's curses port, tiny-diffusion's visualize.py). Small model size is not just a training constraint but a UI requirement — only a model in the tens-of-millions class can denoise fast enough on laptop hardware to animate in real time.

## Bottom Line

Build it as a gated experiment, not a promised product. The validated skeleton: a 5–30M-parameter bidirectional transformer (nanoGPT-class), char-level or digit-atomic tokenizer, absorbing-state masked diffusion objective per LLaDA's GUIDELINES.md pseudocode (p_mask = (1−ε)t + ε, cross-entropy on masked positions only, divided by p_mask), MDLM-informed defaults with EMA decay rescaled to run length, a procedurally generated templated math corpus, a MaskGIT-lineage confidence sampler with a small ordering ablation, fixed short canvases (defer block diffusion), an external answer-checker instead of promised self-correction, and an AR twin of identical size/data/compute trained alongside as the control. The UI renders committed tokens as frozen (which is the truth) and adds an infilling mode — the one capability where the mechanism advantage is real and measured at small scale. Expected outcome per the evidence: a model that trains in hours-to-days, does modest templated arithmetic at best, and decodes near-left-to-right — with the gibberish risk front-loaded into milestone 1.

## Key Insights

1. **The objective is settled and simple.** Masked diffusion training = weighted masked cross-entropy; no time conditioning needed (scoped to absorbing-state diffusion — it does not hold for uniform/hybrid noise variants). Verified by MDLM, MD4, RADD, Zheng et al.; seeded by D3PM's "BERT is a one-step diffusion model" (2021). Implement LLaDA/MDLM masked-CE directly; read SEDD for theory only. *(High confidence)*

2. **The architecture delta is ~5 changes to nanoGPT.** Remove the causal mask, add a [MASK] token, train on masked positions with variable mask rate, weight by 1/p_mask, decode by iterative confidence-based unmasking. LLaDA's config.json is a vanilla LLaMA-style block. Caveat: the *code* delta is tiny; the *behavioral* delta (gradient variance, sampler subsystem, LR sensitivity) is where the risk lives. *(High confidence)*

3. **Encoder fine-tuning is the guaranteed-ish demo path; from-scratch is the main quest.** BERT/RoBERTa/DistilBERT + variable mask rate yields a working text diffusion generator cheaply (nathan-barry, gumran, ZHZisZZ/dllm, DiffusionBERT — noting these are one Karpathy-amplified recipe cascade, validated for fluent text only, *not* for arithmetic; WordPiece digit-chunking may actively hurt math). *(High for text; unvalidated for math)*

4. **The laptop feasibility envelope (1–50M params) is a hypothesis, not a demonstrated fact.** It triangulates AR evidence (TinyStories, nanoGPT, Chinchilla, Cramming's 1-GPU-day BERT) that has never been multiplied by the diffusion training tax. Both documented laptop attempts failed at minutes-to-hours budgets. Plan hours-to-days, treat coherence as milestone 1, and keep the AR twin as the sanity reference. *(Medium confidence — the central uncertainty of the whole project)*

5. **A diffusion training tax is directionally certain, magnitude uncertain.** One unreplicated scaling study (SMDM) measured ~16× compute to match AR validation loss; Dieleman's mechanism (signal only at masked positions, one noise level per pass) explains why. The tax is partially offset in the many-epoch small-corpus regime — but see insight 6. Budget roughly an order of magnitude more wall-clock than the AR twin. *(Medium)*

6. **The "diffusion wins when data-constrained" argument is real but weaker than it looks for this build.** CMU's crossover result (AR saturates ~4 epochs, diffusion keeps gaining to ~100+) fits a fixed math corpus re-epoched heavily — but a follow-up reproduces much of the gain in AR with dropout + weight decay, the original concedes AR wins below a compute threshold a laptop may sit under, and with a procedural generator the data constraint is self-imposed (fresh sampling is always available). Mandatory controls: a regularized AR baseline on the identical frozen corpus, plus a fresh-data AR arm. *(Medium; disputed attribution)*

7. **Math is the worst case for parallel-decoding speed.** Steps must scale ~linearly with length for whole-answer correctness (Feng et al.); GSM8K drops 76.95%→62.31% at fixed 2 tokens/step; the one CPU GGUF datapoint ran math prompts at ~0.6× llama.cpp AR speed (4 steps sufficed for a trivial arithmetic prompt; 16 for a code prompt — single-prompt community benchmark). At 5–30M scale the whole speed question is nearly moot: even steps=length is milliseconds. Sell the mechanism, never the speed. *(High)*

8. **Vanilla absorbing-state sampling has no self-correction — committed tokens are frozen.** Formalized by ReMDM; observed by Dream users ("does not change a word after it's been placed"); at 288M the hr-diffuse-1-nano builder reports six self-correction methods failing while a 300k-param external critic head detected errors well above chance (one builder, exotic Mamba-distilled architecture — treat as indicative). The UI must render frozen commits honestly; error-detection belongs to an external checker/verifier. *(High for the mechanism; medium for the small-scale specifics)*

9. **Small-model math wins are real but task-shaped and datacenter-trained.** MGDM 85M: 91.5% Countdown / 100% Sudoku vs 45.8%/20.7% same-size AR — after ~500k in-task problems on datacenter GPUs. DoT: 100% on fixed-format 4×4/5×5 multiplication. The same literature shows the advantage *not* transferring: DoT's GSM8K (32.6%) loses to fine-tuned GPT-2-small CoT (40.7%); general-purpose Dream 7B scores 16.0 on Countdown. Scope the build to templated symbolic tasks; do not promise word-problem competence; do not claim these numbers pre-validate laptop budgets. *(High, with the scope caveat)*

10. **Every published dLLM math benchmark number is an upper bound.** GSM-Symbolic shows small-model scores collapsing under trivial perturbation; the corpus's highest open-dLLM figure (MMaDA "GSM8K 86.1") is actually a POPE multimodal score with the released checkpoint independently measuring ~48%; LLaDA's GSM8K appears as 69.4–79.3 depending on eval config; early "diffusion beats GPT-2 perplexity" claims were partly a float32 Gumbel sampling artifact. Local eval hygiene: exact-match on held-out *perturbed* templates, eval-config annotations on every number. *(High)*

11. **The denoising UI is solved; the drama is the risk.** Five independent reference implementations exist; multimodalart's app.py gives the full recipe (per-step (token, color) states, confidence-binned coloring, streamed with an adjustable delay). But math-optimal decoding (left-to-right tendency, frozen commits, temperature 0, small blocks) can look indistinguishable from slow AR streaming. Design the UI around block refinement (not token streaming), add an infilling demo mode (the true mechanism showcase), and optionally a deliberately non-optimal "showcase" decoding mode labeled as such. *(High)*

12. **The sampler design space is well charted at 7–8B and unvalidated at tiny scale.** Canonical loop: MaskGIT confidence-based parallel unmasking with a cosine schedule; LLaDA's generate.py is the reference (Gumbel temperature, per-step top-k commits, low-confidence remasking, semi-AR block mode, CFG); Dream enumerates orderings (random / top-1 / margin / entropy; temperature 0 for math). Tiny-model confidence calibration is the open question — plan an ordering ablation (random vs confidence vs margin vs entropy), not an import. *(High for the map; open at build scale)*

13. **Training stability has named risks and cheap mitigations — one of which is a trap at laptop scale.** Adopt: antithetic/low-discrepancy t-sampling, ε floor on p_mask (LLaDA's 0.001), conservative LR (LLaDA's pretraining crashed at 1.2T tokens and resumed at LR/4). Trap: MDLM's EMA 0.9999 has a ~10k-step time constant — on a few-thousand-step run the EMA checkpoint is mostly initialization; rescale to ~0.99–0.999 or skip EMA. *(High on mitigations; the risk profile at 10M scale is honestly unknown)*

14. **Running/adapting existing 8B dLLMs locally is a dead end for training and serious eval; viable as a slow side-exhibit.** LLaDA SFT OOMs on 24GB; VRAM grows with prompt length; GSM8K eval ~31 hours on an A100; ~1s per denoising step at 8B Q8 on a 3090. This constraint independently forces the correct decision: a tiny model is the only route to real-time denoising animation. An optional canned/slow 8B GGUF comparison ("here's a real one, slowly; here's ours, live") is cheap narrative value. *(High)*

15. **Synthetic templated data is the highest-leverage axis, with one trap.** TinyStories proves domain restriction substitutes for scale. TinyGSM's headline (125M → 63.1% GSM8K) rides an external Python interpreter executing generated code — pure-text targets must expect materially less, or the build adds an executor (architecture change). Grokking gives sub-1M arithmetic but is a hyperparameter lottery with unbounded wall-clock. Recipe: procedural generator, fixed answer formats, curriculum from single-op arithmetic upward, external checker. *(High on the recipe; the cited accuracy anchors do not transfer as numbers)*

16. **Fixed-length canvases are the mechanism's most user-visible handicap; fixed short per-task canvases are the pragmatic answer.** Block diffusion (BD3-LM) restores variable length and KV caching but adds training complexity the gibberish-risk phase doesn't need — demote to a later milestone. For templated math with fixed answer formats, short canvases plus learned EOS/PAD termination suffice. *(High)*

## Research Map

Sixteen aspects were researched in parallel: discrete diffusion theory; the DLLM model landscape; training objectives and recipes; reference codebases and minimal implementations; laptop-scale training feasibility; sampling/inference algorithms; math and reasoning specialization; architecture internals; math datasets and data strategy; real-time visualization UI; hardware envelope; failure modes; the AR-vs-diffusion debate; 2025–2026 advances; practitioner/community reality; and the from-scratch build curriculum. Each aspect ran primary-source, recent, adversarial, practitioner, and failure-mode queries. Post-research: source audit, contradiction hunt, timeline/change detection, practitioner-reality sweep, synthesis, devil's-advocate attack, and a quality gate (PASS).

## Main Findings

### Theory: five years of removing machinery
D3PM (2021) founded discrete diffusion with categorical transition matrices and named the absorbing-[MASK] variant; ARDM (2021) already showed masked diffusion ≈ any-order autoregression; Campbell et al. (2022) gave the continuous-time backbone; SEDD (ICML 2024 Best Paper) made diffusion competitive with GPT-2 via concrete-score matching; then MDLM/MD4/RADD (mid-2024) collapsed everything into weighted masked cross-entropy and proved time conditioning removable. Zheng et al. sharpened the reduction — masked diffusion models are "secretly time-agnostic masked models" — and exposed the float32 Gumbel bug that had inflated earlier diffusion-vs-AR sampling comparisons. The 2021 papers already contained the build's conceptual core; the 2024–2025 wave made it implementable in a few hundred lines.

### The recipe (as the executor should implement it)
From LLaDA's GUIDELINES.md and MDLM's configs: sample t ~ U[0,1] per sequence; mask each token independently with p_mask = (1−ε)t + ε (ε = 0.001); compute cross-entropy only on masked positions; divide by p_mask (the 1/t weighting); optionally use a log-linear schedule and antithetic t-sampling (MDLM); SUBS parameterization details: [MASK] logit forced to −∞, unmasked tokens carried over. Optimizer defaults from MDLM at 110M: AdamW lr 3e-4 (scale down for tiny models and small batches), warmup, cosine or constant decay. EMA rescaled to run length (~0.99–0.999) or omitted. 1% of training sequences at random lengths (LLaDA) to help variable-length behavior. SFT variant: never noise the prompt, only the response.

### Sampling: the decoder is a new subsystem
The canonical loop (MaskGIT lineage): start fully masked; each step, predict all masked positions, commit the top-k by confidence (cosine schedule: few early, many late), keep the rest masked; repeat for N steps. LLaDA's generate.py adds Gumbel-noise temperature, low-confidence remasking *within* a step (this defers commitment; it does not revise committed tokens), semi-autoregressive block mode, and classifier-free guidance. Dream's practical ordering menu: random, top-1 confidence, top1−top2 margin, entropy — temperature 0 recommended for math. Fast-dLLM contributes confidence-thresholded parallel commits with an approximate-caching toolkit (validated at 7–8B). For a tiny model: implement random + confidence + margin + entropy ordering behind one interface and ablate — calibration at 10M scale is unknown, and confidence ordering can lose to random when calibration is bad.

### Math capability: mechanism-shaped, not general
Where diffusion wins at small scale, it wins big — but always in-task-trained and templated: MGDM (85M, ICLR 2025) 91.5% Countdown / 100% Sudoku vs 45.8%/20.7% AR; DoT 100% fixed-format multiplication. Where it must generalize, it loses: DoT GSM8K 32.6% < GPT-2-small CoT 40.7%; Dream 7B Countdown 16.0. Bidirectionality delivers two durable, honest advantages: infilling (hr-diffuse-1-nano: 14% recovery vs ~0% AR) and reversal robustness (SMDM 92% vs 0% reversal tasks; independent mechanistic confirmation). Arithmetic length generalization beyond trained operand lengths is an open problem whose known fixes (Abacus embeddings, position coupling) are AR-developed and unvalidated for bidirectional masked diffusion — do not promise the model adds longer numbers than it trained on.

### Speed: the marketing story inverts locally
Vendor numbers (Mercury 1,109 tok/s; Mercury 2 >1,000; Seed 2,146; Gemini Diffusion 1,479 claimed / 857 independently measured) are H100/Blackwell batch-1 artifacts benchmarked against speed-tier baselines; serving analyses show the advantage evaporates as batch grows, and a laptop GPU is compute-bound from step one. Vanilla 8B dLLM decoding measured ~10× slower than same-size AR locally (6.7–6.95 tok/s on A100/4090 vs ~90–140 tok/s AR). The build's speed story is exactly one sentence: "per-step inference is real-time for a sufficiently small model."

### Feasibility: the honest envelope
Positive anchors: Cramming (BERT-class MLM ≈ BERT quality in 24 consumer-GPU-hours; peer-reviewed); tiny-diffusion (10.7M chars, 20 A100-minutes, coherent Shakespeare-ish output, ships an AR twin and visualizer); TinyStories (<10M fluent under domain restriction); modded-nanogpt's efficiency stack (Muon etc. — AR-validated only). Negative anchors: 0-for-2 laptop from-scratch diffusion attempts, one already on-recipe; a pre-speedrun practitioner estimating "multiple weeks" for 70M from scratch on consumer hardware. Windows toolchain: flash-attn does not build reliably natively (use PyTorch SDPA; consider WSL2), bf16 needs Ampere+, MDLM's repo needs dependency-stripping (Mamba CUDA extensions). Model size is doubly bounded: training budget (small) and UI frame budget (small). The 5–30M range with a char/digit-atomic tokenizer on templated math is the best-evidence bet — as a hypothesis to test through gates, not a plan-line fact.

### The UI: reference recipe
multimodalart's LLaDA Space (app.py): capture a list of (token, color) states after every denoising step; color scheme — #444444 masked; confidence-binned reveals (<0.3 red, 0.3–0.7 orange, >0.7 green); previously-committed blue; stream states with an adjustable delay; expose generation length, steps, temperature, CFG, block length, remasking strategy. llama.cpp's `--diffusion-visual` and simonw's curses port prove the terminal variant. For this build: WebSocket/SSE streaming of per-step state from a local inference server to a web front-end is architecturally identical and leaves full frame budget for the aesthetic layer, because the model itself is tiny.

## Timeline (condensed)

- **2021** — Multinomial diffusion (Feb); D3PM founds discrete diffusion, frames BERT as one-step diffusion (Jul); ARDM proves the any-order-AR equivalence (Oct).
- **2022** — MaskGIT's confidence-based parallel unmasking (Feb — ancestor of every dLLM decoder); Campbell's CTMC formulation (May); Cramming: 1-GPU-day BERT (Dec).
- **2023** — Dieleman's "too early" diagnosis (Jan — later overturned); TinyStories (May); Plaid measures 64× tax for the *continuous* route (May — category error if quoted for masked diffusion); SEDD posted (Oct); TinyGSM (Dec).
- **2024** — DoT (Feb); RADD + MD4 + MDLM within five days of each other (Jun) — the simplification convergence; SEDD wins ICML Best Paper (Jul); time-agnostic proof + float32 Gumbel bug exposed (Sep); MGDM constraint-task wins, DiffuGPT/DiffuLLaMA AR-to-diffusion conversion, SMDM ~16× scaling study (Oct); UDLM uniform-noise fork (Dec).
- **2025** — LLaDA 8B: first from-scratch dLLM competitive with LLaMA3-8B (Feb); Mercury announced (Feb); Feng et al. steps-scale-with-length theorem (Feb); BD3-LM block diffusion + ReMDM remasking + GIDD hybrid noise (Mar); Dream 7B (Apr); Gemini Diffusion demo (May); Fast-dLLM caching (May); CMU data-constrained crossover (Jul); Seed Diffusion 2,146 tok/s claim (Jul); TraceRL/TraDo dLLM-RL math SOTA (Sep); LLaDA-MoE (Sep); RND1 30B conversion (Oct); attribution dispute — masking as generic regularization (Oct); Inception's $50M raise (Nov); tiny-diffusion, the build's closest artifact (Nov); LLaDA2.0 100B (Dec).
- **2026** — Mercury 2, first diffusion reasoning LLM (Feb); Nemotron-Labs-Diffusion tri-mode open weights (May–Jul); DiffusionGemma — Google's open-weight dLLM, candidly ranked below Gemma 4 (Jun); iLLaDA re-validates from-scratch at 12T tokens (Jun); The Flexibility Trap: forcing left-to-right decoding gives best math accuracy (ICML, Jul); survey v3 declares masked discrete diffusion the winner over continuous approaches (Jun).

## Evidence Table

| Claim | Confidence | Best Sources | Notes |
|---|---|---|---|
| Masked diffusion = weighted masked CE; no time conditioning (absorbing-state) | High | MDLM 2406.07524; MD4 2406.04329; RADD 2406.03736; Zheng 2409.02908 | 4 groups, genuinely convergent algebra |
| Architecture delta from AR transformer ≈ 5 changes | High | LLaDA GUIDELINES.md; LLaDA config.json; tiny-diffusion | Code delta tiny; behavioral delta is the risk |
| Steps must scale ~linearly with length for whole-answer math | High | Feng 2502.09622; LLaDA 2502.09992; 2510.19990 (2-tok/step collapse) | Theory + empirical agreement |
| No self-correction in vanilla absorbing sampling | High | ReMDM 2503.00307; r/LocalLLaMA Dream thread; HN 48792131 | Small-scale critic-head result is N=1 |
| Laptop from-scratch diffusion: 0 successes, 2 documented failures | High | seangoedecke.com; boesch.dev | Central risk; one failure was on-recipe |
| ~16× diffusion-vs-AR compute gap at matched loss | Low-Medium | SMDM 2410.18514 | Single unreplicated study; cite as "one estimate" |
| Data-constrained multi-epoch diffusion advantage | Medium | CMU 2507.15857; disputed by 2510.04071 | Mandatory AR + fresh-data controls |
| Small-model constraint-task wins (Countdown/Sudoku) | High | MGDM 2410.14157; scoped by Dream 2508.15487 | In-task-trained, datacenter budgets |
| MMaDA "GSM8K 86.1" is wrong (POPE score; checkpoint ≈48%) | High | 2510.02880; NeurIPS camera-ready | Retracted from all planning numbers |
| Infilling advantage at small scale (14% vs ~0%) | Medium | HN 48792131 (hr-diffuse-1-nano) | One builder; mechanism-plausible |
| Denoising visualization: solved pattern, ≥5 implementations | High | multimodalart app.py; llama.cpp PR 14644; tiny-diffusion | Copyable recipe with exact colors/controls |
| 8B dLLMs locally: inference-only at best, math slowest | High | LLaDA/Dream issue trackers; diffuse-cpp GGUF card | Multi-user issue-tracker evidence |
| Encoder fine-tune → working text diffusion cheaply | High (text) | nathan.rs; gumran; ZHZisZZ/dllm; HN 45644328 | One recipe cascade; unvalidated for math |
| Cramming: 1-GPU-day BERT-class MLM works | High | 2212.14034 | Strongest peer-reviewed feasibility anchor |

## Tradeoffs & Alternatives

**From-scratch vs encoder fine-tune vs AR-conversion.** Industry consensus moved decisively to AR-to-diffusion conversion (DiffuGPT → Dream → RND1 → LLaDA2.0) because it is far cheaper; the hobbyist equivalent is BERT-family fine-tuning. For this project, from-scratch is the pedagogical point and the only path to a digit-atomic tokenizer sized for real-time animation — but the encoder fine-tune should exist as the fallback demo (fluent text within an hour of fine-tuning) so the project never has zero working artifacts.

**Absorbing vs uniform/hybrid noise.** Absorbing dominates every mature result and all reference code; uniform (UDLM) closes the gap on small vocabularies and enables visible token *editing*; GIDD's hybrid unlocks self-correction at compute-matched quality (validated ~100M+, OpenWebText). The small-vocab analogy to arithmetic is unproven (molecules/DNA lack carry structure). Default absorbing; hybrid noise is a stretch goal only if the mainline lands early — it would make the UI visibly edit rather than only reveal.

**Fixed canvas vs block diffusion.** BD3-LM fixes length, caching, and quality but adds per-block schedules and new failure modes during the phase where the main risk is producing any coherent output. Fixed short per-task canvases suffice for templated math. Block mode is a later milestone.

**Pure text vs code-executor.** TinyGSM-class accuracy requires an interpreter executing generated Python. A sandboxed evaluator changes the architecture and dilutes the "model solves math" claim; the honest pure-text alternative accepts lower accuracy on harder problems. Recommended: pure text for the model, external checker for *verification* (grading), executor optional later.

**Sampler orderings.** Confidence-based unmasking is canonical but calibration-dependent; at tiny scale random order may compete. Ship all four orderings behind a flag; ablate; let the UI expose the choice (it is also the most interesting interactive control).

## Practitioner Reality

The community record is unusually rich. 8B open dLLMs generated heavy engagement (Dream thread: 893 points) and consistent complaints: slow (33–180s completions on datacenter GPUs pre-optimization), VRAM-hungry (growing with prompt length; 24GB insufficient for SFT), no streaming read-along, no self-correction, boilerplate outputs — alongside genuine fascination ("randomly a god at sudoku"). The pain produced real tooling: mainline llama.cpp diffusion support with five decoding algorithms and a built-in terminal visualizer; diffusers' LLaDA2Pipeline; GGUF quants; a CPU engine (diffuse-cpp) that beats AR on few-step prompts and loses on math. The minimal-implementation wave (tiny-diffusion 365 lines, nanoLLaDA ~500, gumran <80, BERT-Chat) plus Karpathy's endorsement made the small build path broadly replicated practitioner knowledge — for text. JetBrains shipping a 0.1B local code-completion model in production grounds the tiny-specialist thesis. The single most calibrating datapoint remains hr-diffuse-1-nano: $500 of H100 time at 288M params bought real infilling wins, big repetition reduction, and six failed self-correction attempts — "small models don't doubt; they rationalize."

## Contradictions & Debates

1. **Data-constrained advantage attribution** — diffusion-specific implicit augmentation (CMU) vs generic stochastic regularization reproducible in AR (2510.04071). Unresolved; determines whether choosing diffusion for a small fixed corpus is scientifically justified or aesthetic. The build's AR controls answer it locally.
2. **Feasibility interpolation** — no positive or negative existence proof for laptop-budget from-scratch diffusion math; everything is interpolation between toy demos and datacenter runs.
3. **Absorbing vs uniform/hybrid at small vocab** — no head-to-head exists at laptop scale on arithmetic.
4. **Parallel-decode speed recovery for math at small scale** — dParallel/MED/Prophet succeed at 7–8B; information-theoretic arguments (ParallelBench) say math binds hardest; nothing tested below ~4B.
5. **GSM-Symbolic fragility** — Apple's collapse result vs a 2026 re-audit finding much of the effect disappears after removing ambiguous items; affects how honestly any small model can claim to "solve" word problems.
6. **Length generalization in bidirectional diffusion** — completely open; AR fixes unvalidated.
7. **The visualization paradox** — math-optimal decoding trends near-sequential (Flexibility Trap; PSC), potentially making the "watch it think in parallel" demo look like slow AR streaming; whether task/schedule design can make genuinely parallel math decoding visible without wrecking accuracy is open. The build's answer: infilling mode + honest framing + optional showcase mode.
8. **GSM1K contamination figure (2–7% drops)** — the number appears in a source whose title the devil's-advocate verified as an inference-method paper (RCD, arXiv 2601.22954); the contamination analysis may be a section within it, but the citation could not be cleanly confirmed. Treated as unverified; the GSM-Symbolic evidence stands independently.

## Failure Modes / Risks / Misconceptions

- **Gibberish risk (the headline risk):** both prior laptop attempts failed; coherence is milestone 1, gated before any math work.
- **EMA trap:** default 0.9999 decay evaluates a near-untrained network on short runs; rescale or skip.
- **Tokenizer digit-chunking:** BPE/WordPiece splits numbers inconsistently; use char-level or digit-atomic vocab for the math model.
- **Confidence miscalibration at tiny scale:** confidence-ordered unmasking may underperform random; ablate.
- **Frozen-commit incoherence:** early wrong commits propagate; external checker, generous steps, optional remasking later.
- **Windows toolchain:** no flash-attn natively (SDPA suffices at this scale); bf16 needs Ampere+; strip CUDA-extension deps from any ported code; thermals throttle sustained laptop training — expect wall-clock variance.
- **Benchmark self-deception:** templated in-task accuracy collapses under perturbation unless the eval set is built perturbed-by-construction; never quote a number without its eval config.
- **Misconceptions to keep out of all project text:** "diffusion is faster" (not locally, not for math), "it self-corrects" (not vanilla), "any-order is a reasoning advantage" (it trends left-to-right on math and can hurt), "64× tax" (continuous-route number, category error).

## Gaps & Limitations

The 2–7% GSM1K contamination figure could not be cleanly verified to its citation. Several 2026 venue attributions (ICML 2026, ICLR 2026) and post-cutoff arXiv IDs are preprint-level evidence. The ~16× training tax is single-sourced. The 4-vs-16-step CPU figures come from single-prompt community benchmarks. Source independence is thinner than raw counts suggest: three labs (ML-GSAI, Kuleshov-group/Cornell, HKUNLP) author most S-tier evidence; Aaron Lou's expository blog is SEDD's first author; SEDD/MDLM academics co-founded Inception Labs — intra-cluster agreement was not counted as replication. 317 findings collapse to ~85 unique URLs; repetition was never treated as corroboration. No laptop-hardware benchmark of any diffusion-LM training run exists, full stop — the project will generate the first one.

## Devil's Advocate

The strongest standing attack (portfolio-level, high severity): *no single point in (params, compute, task, UI) space is supported by all the evidence simultaneously* — capability lives at 85M+/datacenter, feasibility at 10M/no-math, and the two laptop attempts failed. The flagship configuration is an unsampled corner defended by citations that each support a different corner; the most probable outcome per the record is a slow-training model doing modest templated arithmetic with near-left-to-right decoding and no visible self-correction. Second high-severity attack: the "1–50M laptop envelope" is AR evidence never multiplied by the diffusion tax, and one documented failure already used the recommended recipe. Third: the data-constrained argument concedes AR wins below a compute crossover the laptop may never reach, and the data freeze is self-imposed when a generator exists. Fourth: math-optimal decoding may render the centerpiece visualization indistinguishable from AR streaming — infilling is the demo the evidence actually supports. These attacks were accepted and are reflected in the Bottom Line: gated experiment, AR twin + fresh-data controls, infilling mode, honest UI, coherence-first milestones.

## Actionable Takeaways (build spec inputs)

1. **Model:** bidirectional transformer, 5–30M params (start ~10M), RoPE, SDPA attention, no time embedding, one [MASK] token. Char-level or digit-atomic tokenizer (~100–2k vocab).
2. **Objective:** LLaDA GUIDELINES.md recipe verbatim; MDLM refinements (antithetic t-sampling, log-linear schedule option); ε floor 0.001; EMA 0.99–0.999 or none.
3. **Data:** procedural templated math generator (arithmetic → multi-digit with carries → linear equations → Countdown-style search), fixed answer formats, perturbed held-out eval by construction; fresh-sampling AND frozen-corpus arms.
4. **Controls:** AR twin (identical params/tokenizer/data/compute) trained alongside; regularized (dropout + weight decay) for the frozen-corpus comparison.
5. **Sampler:** MaskGIT-lineage loop; orderings random/confidence/margin/entropy behind one flag; temperature 0 for math; steps defaulting to ≈ canvas length; fixed short canvases.
6. **Verification:** external answer-checker (exact match / numeric equivalence); optional tiny critic head later; no self-correction claims.
7. **UI:** local inference server streaming per-step (token, state, confidence) frames over WebSocket/SSE; block-refinement rendering with confidence-binned colors; controls for steps/ordering/temperature/canvas; infilling mode; honest "committed = frozen" rendering; optional showcase mode.
8. **Milestone gates:** M1 coherent templated text (vs AR twin), M2 single-op arithmetic > 90% on perturbed eval, M3 multi-digit/carry, M4 equation solving, M5 UI polish + infilling demo. Each gate: go/pivot decision (pivot = encoder fine-tune fallback or scope reduction).
9. **Never claim:** speed superiority, self-correction, word-problem competence, length generalization.

## Methodology

- Mode: Exhaustive (supersearch). 16 aspects, ~110 targeted queries.
- Agents: 16 aspect researchers + source-auditor + contradiction-hunter + timeline + practitioner-reality + synthesis-prep + devil's-advocate + quality-gate = 23 agents, 711 tool uses, ~2.17M subagent tokens, ~40 minutes wall-clock.
- Corpus: 317 findings → ~85 unique URLs after dedup; ~30 defensibly S/A-tier.
- Quality gate: PASS. Scores — saturation 0.85, source diversity 0.65, tier quality 0.70, evidence depth 0.90, recency 0.90, contradiction coverage 0.90, practical usefulness 0.95, claim hygiene 0.65, uncertainty honesty 0.90.
- Corrections applied post-audit/devil: MMaDA figure retracted; GSM1K citation flagged unverified; CPU step-count figures corrected (4 arithmetic / 16 code); MGDM "laptop-trainable" framing corrected to "small-parameter, datacenter-budget"; EMA default flagged as scale trap; single-source claims labeled throughout.
- Known weaknesses: three-lab S-tier concentration; unreplicated key quantities (16× tax); post-cutoff 2026 citations at preprint confidence.

## Sources

Curated top sources (full 317-finding table with per-aspect rankings: `research/raw/sources-appendix.md`).

| # | Source | URL | Tier | Why It Matters |
|---|---|---|---|---|
| 1 | LLaDA (paper + GUIDELINES.md + generate.py) | arxiv.org/abs/2502.09992 · github.com/ML-GSAI/LLaDA | S | The canonical from-scratch recipe, copyable pseudocode, reference sampler |
| 2 | MDLM (paper + repo) | arxiv.org/abs/2406.07524 · github.com/kuleshov-group/mdlm | S | Canonical objective derivation + proven training defaults |
| 3 | MD4 (DeepMind) | arxiv.org/abs/2406.04329 | S | Independent simplification proof; schedule invariance |
| 4 | RADD | arxiv.org/abs/2406.03736 | S | Proof time conditioning is removable; caching implication |
| 5 | Zheng et al. time-agnostic | arxiv.org/abs/2409.02908 | S | Sharpest theoretical reduction + float32 Gumbel bug |
| 6 | D3PM | arxiv.org/abs/2107.03006 | S | Founding formalism; BERT-as-diffusion framing |
| 7 | SEDD | arxiv.org/abs/2310.16834 | S | Theory reference (not implementation target) |
| 8 | tiny-diffusion | github.com/nathan-barry/tiny-diffusion | S | Closest existing artifact: 365 lines, 10.7M, visualizer, AR twin |
| 9 | nanoLLaDA | github.com/Lukas-Xue/nanoLLaDA | B | Full small-scale lifecycle reference |
| 10 | gumran/language-diffusion | github.com/gumran/language-diffusion | B | <80-line DistilBERT fine-tune fallback |
| 11 | MaskGIT | CVPR 2022 paper | S | Ancestor of every confidence-based unmasking loop |
| 12 | Feng et al. theory | arxiv.org/abs/2502.09622 | S | Steps-scale-with-length theorem (math feasibility) |
| 13 | MGDM / Beyond Autoregression | arxiv.org/abs/2410.14157 | S | Constraint-task wins at small parameter counts |
| 14 | Diffusion-of-Thought | arxiv.org/abs/2402.07754 | S | Multiplication wins + GSM8K transfer failure |
| 15 | SMDM scaling | arxiv.org/abs/2410.18514 | S | ~16× tax estimate (single-source); reversal results |
| 16 | CMU data-constrained | arxiv.org/abs/2507.15857 | S | Multi-epoch crossover argument |
| 17 | Masking-as-regularization rebuttal | arxiv.org/html/2510.04071 | S | Attribution dispute; motivates AR controls |
| 18 | ReMDM | arxiv.org/abs/2503.00307 | S | Formalizes no-self-correction + remasking cure |
| 19 | GIDD | arxiv.org/abs/2503.04482 | S | Hybrid noise self-correction (stretch goal) |
| 20 | UDLM | arxiv.org/abs/2412.10193 | S | Uniform-noise fork; small-vocab evidence |
| 21 | BD3-LM block diffusion | arxiv.org/abs/2503.09573 | S | Variable length + caching (later milestone) |
| 22 | Fast-dLLM | arxiv.org/abs/2505.22618 | S | Confidence-thresholded parallel decoding + caching |
| 23 | The Flexibility Trap | hf.co/papers/2601.15165 | A | Any-order decoding hurts math; left-to-right optimal |
| 24 | TinyStories | arxiv.org/abs/2305.07759 | S | Domain restriction substitutes for scale |
| 25 | TinyGSM | arxiv.org/pdf/2312.09241 | S | Synthetic math data leverage (executor caveat) |
| 26 | Cramming | arxiv.org/abs/2212.14034 | S | 1-GPU-day MLM feasibility anchor |
| 27 | Dieleman: diffusion for text | sander.ai/2023/01/09/diffusion-language.html | A | Mechanistic why-diffusion-lags analysis |
| 28 | Aaron Lou blog | aaronlou.com/blog/2024/discrete-diffusion | A | Cleanest derivation chain (COI: SEDD author) |
| 29 | multimodalart LLaDA Space | hf.co/spaces/multimodalart/LLaDA (app.py) | S | Complete copyable visualization recipe |
| 30 | llama.cpp diffusion PR | github.com/ggml-org/llama.cpp/pull/14644 | S | Shipped terminal visualizer + local perf numbers |
| 31 | hr-diffuse-1-nano (HN) | news.ycombinator.com/item?id=48792131 | B | Best small-scale calibration datapoint |
| 32 | BERT-is-diffusion post + HN | nathan.rs/posts/roberta-diffusion · HN 45644328 | A/B | Encoder fine-tune path + replication cascade |
| 33 | Goedecke laptop attempt | seangoedecke.com/model-on-a-mbp | A | Documented laptop failure #1 |
| 34 | boesch.dev laptop attempt | boesch.dev/posts/simple-dlm | A | Documented laptop failure #2 (on-recipe) |
| 35 | r/LocalLLaMA LLaDA + Dream threads | reddit.com (1izfy2d, 1jptset) | B | Multi-user local-behavior evidence |
| 36 | LLaDA/Dream issue trackers | github.com (ML-GSAI/LLaDA, DreamLM/Dream issues) | S | Multi-user OOM/speed evidence |
| 37 | diffuse-cpp GGUF card | hf.co/diffuse-cpp/LLaDA-8B-Instruct-GGUF | B | Only CPU dLLM engine; math-is-worst-case datapoint |
| 38 | GSM-Symbolic (Apple) | machinelearning.apple.com/research/gsm-symbolic | S | Perturbation fragility; eval design mandate |
| 39 | MMaDA correction chain | arxiv.org/pdf/2510.02880 + NeurIPS camera-ready | S | Flagship wrong-number case study |
| 40 | modded-nanogpt | github.com/KellerJordan/modded-nanogpt | S | Efficiency stack + AR baseline bar |
| 41 | Survey (v3 2026-06) | arxiv.org/abs/2508.10875 | S | Field consensus + open problems |
| 42 | DiffusionGemma | deepmind.google/models/gemma/diffusiongemma | S | Vendor candor on quality trade |
| 43 | Nemotron-Labs-Diffusion | arxiv.org/abs/2607.05722 | S | AR/diffusion hybrid endgame signal |
| 44 | Cosmos/ARDM | arxiv.org/abs/2110.02037 | S | Original any-order equivalence |
| 45 | Grokking + PAIR explorable | arxiv.org/abs/2201.02177 · pair.withgoogle.com | S/A | Sub-1M arithmetic possibility + fragility |
