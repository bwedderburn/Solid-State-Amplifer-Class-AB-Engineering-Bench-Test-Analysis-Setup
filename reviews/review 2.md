# Code Review

## :x: Blocking Issue

### Progress callbacks are skipped on FY command failures
The new `sweep_scope_fixed` and `sweep_audio_kpis` helpers exit the current
iteration with `continue` whenever `fy_apply` raises. Because the `progress`
callback is only invoked after the measurement succeeds, those early `continue`
statements now bypass the progress update completely. In the GUI this leaves
`auto_prog` stuck at its previous value (often 0%) for the remainder of the run
as soon as the FY generator fails to respond, even though the sweep loop keeps
iterating. The legacy `UnifiedGUI` implementation always advanced the progress
bar per frequency step, regardless of FY errors, so this is a regression that
makes the automation tab appear hung during real hardware faults.

Please move the `progress(i + 1, n)` invocation into a `finally` block (or call
it before each `continue`) so that the UI keeps updating even when FY commands
fail. The same fix is needed in both sweep helpers.

* `amp_benchkit/automation.py`: lines 129-161 (`sweep_scope_fixed`)
* `amp_benchkit/automation.py`: lines 210-268 (`sweep_audio_kpis`)
