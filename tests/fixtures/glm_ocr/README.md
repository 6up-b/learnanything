# GLM-OCR answers used by `tests/test_glm_ocr.py`

## `arxiv_2302_11517_trimmed.json`: a recorded hosted answer

This is z.ai's `layout_parsing` answer for pages 1–5 of:

> Wei Tang, Kangning Cui, Raymond H. Chan, "Optimized Hard Exudate Detection with
> Supervised Contrastive Learning", arXiv:2302.11517v2,
> <https://arxiv.org/abs/2302.11517>. Licensed CC BY 4.0
> (<https://creativecommons.org/licenses/by/4.0/>).

It was recorded on 2026-10-14 during the owner-requested live check
(`docs/reviews/glm-ocr-quality.md`). It was trimmed, not modified:

- every top-level key and the `usage`, `data_info`, `id` and `request_id` values are
  as recorded;
- `layout_details` keeps all five pages but only some regions on each. The kept
  regions are byte-for-byte as recorded, including `index`, `label`, `native_label`,
  `bbox_2d`, `width`, `height` and `content`;
- `md_results` is cut to its first 600 characters. LearnLoop never reads it.

## `synthetic_book_window.json`: invented, not recorded

This answer is made up. It copies the *shapes* the hosted service gave on the
owner's textbooks:

- titles and captions wrapped in `<div align="center">`;
- every heading at `##`;
- split labels such as `1. 11 definition:`, then `1. 5` and `1. 6 (…)` after the
  label `1.4`, so the book's own numbering vouches for each;
- currency dollars in prose;
- `algorithm` regions that hold either boxed results or R code;
- `vision_footnote` credits;
- no footnote, page number or equation-number region.

All of its text is invented. No text from any book is in this repository.
