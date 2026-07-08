# Issues discovered during usage

## Java projects
- [x] Incorrectly assumed that transitive dependency is missing - then overgeneralized the solution based on this wrong assumption.
- [x] Failed to see Git-committed files, then ran in circles trying to understand the state of the codebase.
- [x] Replaced happy-path tests with new test logic - it is OK to consolidate repetitive tests, it is not OK to replace existing tests with new logic.
- [x] Hardcoded the exact strings/dates in the test, making the test brittle/system date dependent.
- [x] Struggled with escaping double quotes in JSON (the task was to have JSON content inside the string), proceeded to overcomplicate the solution by researching Jackson/internal JSON framework internals.
- [x] Repeated inspection of the same files when switching between Plan and Build mode in OpenCode.
- [x] Constant over-thinking/over-reaching when asked to implement X like Y when the task is simple enough.
