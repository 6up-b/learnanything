"""FG1's composition: lanes, authoring, admission, the router decision, what Next reads.

Nothing below the sidecar and the CLI imports this package, so it may read every domain
package without a cycle. The leaf ``learnloop.followup_serve`` holds what those domain
packages themselves read: the switches, the workflow's record and the single-use identity.
"""
