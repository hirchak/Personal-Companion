# 2026-10-05 — M8E independent review fixes

Verified clean main/origin at published R `7a9f2c9839dfa9265780b75f59874fe9ab73178f`; owner verdict FIX_REQUIRED
for R01/N01/N02 only. C2 `5d50a724932b6f51f4cf0be6074c0c2c42150299` pins consent scope to the historical Deep
goal revision while checking current ACTIVE lifecycle, and fixes the primary unlock/loading button copy and top-level
Roadmap summary. C3 `6c2a828786757ca28b5427ac986615d4f50d09cf` updates the remaining unlock description; C4
`55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` adjusts its browser test locator only.

Synthetic regressions cover rev1→rev2 active edit, rev1 restart/resume and map/scope separation from new rev2,
and PAUSED fail-closed before persistence/provider fixture. Full Python802, Web51, build, browser unlock1, targeted
R01 tests2 and docs/context/privacy PASS. Provider calls0; real vault/account settings not inspected; M8D native
ledger4/4 unchanged. External controls NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER; human UA OPEN; phone gate unchanged.
M8E AWAITING_REVIEW; no release/deploy/next milestone.
