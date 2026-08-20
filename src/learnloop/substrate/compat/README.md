# Frozen compatibility code

This package contains old-vault activation and replay machinery preserved by
the 2026-07-19 compatibility decision.

**Policy:** kept green, not extended. Changes here require an explicit
compatibility decision, a fixture demonstrating the historical state being
supported, and replay/cutover tests that prove current vault behavior is
unchanged.

Live projection and replay code belongs in the parent `learnloop.substrate`
package. This directory is not a general home for deprecated code.
