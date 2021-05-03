# Prototype repo to build demos for Nessie

This git repo is a temporary repo, which will eventually be retired and maybe deleted. The results
of this work will either go into the [Project Nessie repo](https://github.com/projectnessie/nessie/)
or a separate repo under [Project Nessie](https://github.com/projectnessie/).

## Scope

Build a framework for demos that run on [Google Colaboratory](https://colab.research.google.com/)
and [Katacoda](https://katacoda.com), and, as long as it is feasible and doesn't delay the work
for demos, have a base for production-like performance testing, which has the same or at least
similar restrictions/requirements as the demos.

Every demo must work, we want to eliminate manual testing, so all demos must be unit-testable.

## Version restrictions

Nessie and for example Apache Iceberg need to be compatible to each other and must be based
on released versions. This means, that for example Iceberg 0.11.1 requires
[Nessie 0.3.0](https://github.com/apache/iceberg/blob/apache-iceberg-0.11.1/versions.props#L21),
but Nessie 0.4.0 works as well.

It's very likely that we have to change the Nessie code base to adjust for example the pynessie
dependencies, because of dependency issues in the hosted runtime of Colaboratory notebooks.

## Build

Since demos must be unit-testable, we will need some build tool and GitHub workflows.

## Bumping versions of Nessie and Iceberg et al

Bumping versions should eventually work via a pull-request. I.e. a human changes the versions
used by the demos, submits a PR, CI runs against that PR, review, merge.

At least in the beginning, Nessie will evolve a lot, and we should expect a lot of changes
required to the demos for each version bump. For example, the current versions require a
"huge context switch" in the Demos: jumping from running Python code to executing binaries
and/or running SQL vs. executing binaries to perform tasks against Nessie.

It feels nicer to ensure that everything in the demos repo works against the "latest & greatest"
versions.

If someone wants to run demos against an older "set of versions":
* In Google Colaboratory it's as easy as opening a different URL.
* In Katakoda there seems to be no way to "just use a different URL/branch/tag".

We might either accept that certain environments just don't support "changing versions on the fly"
or we use a different strategy, if that's necessary. So the options are probably:
* Demos (in Katakoda) only work against the "latest set of versions"
* "Archive" certain, relevant demos in the demo-repo's "main" branch in separate directories

I suspect, this chapter requires some more "brain cycles".

### Preparing version bumps

It would be nice to prepare PRs for Nessie and Iceberg version bumps before those are actually
released.

Maybe we can prepare this convenient and "nice to have" ability.

It might also help to have this ability to run demos (and production-like perf tests) as a
"pre-release quality gate" to ensure that user-facing stuff works and there are no performance
regressions.

## Git history

The history in Git should work the same way as for [Project Nessie repo](https://github.com/projectnessie/nessie/),
i.e. a linear git history (no merges, no branches, PR-squash-and-merge).

## Compatibility Matrix

||Current  ||Nessie ||Apache Iceberg ||Notes
| **Yes** |0.4.0  | 0.11.1  | Iceberg declares Nessie 0.3.0, but there are no (REST)API changes between Nessie 0.3.0 and 0.4.0
| No |0.5.1  | (recent HEAD of `master` branch)
| No |(recent HEAD of `main` branch)  | n/a  | **incompatible**, would require a build from a developer's branch
