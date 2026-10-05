## Hi, I'm Hrushikesh

I am a PhD candidate in Materials Science and Engineering at UC Berkeley and Lawrence Berkeley National Laboratory, in [Anubhav Jain's group](https://github.com/hackingmaterials).
I build high-throughput workflows for phonons and thermal properties, with DFT and machine-learned interatomic potentials.
Most of my code goes into [atomate2](https://github.com/materialsproject/atomate2) and the [Materials Project](https://next-gen.materialsproject.org).
My PhD work is the Materials Project's Harmonic Phonon Database ([preprint](https://doi.org/10.26434/chemrxiv.15004632/v1)).

### Workflows in atomate2

| Pull request | Status |
|---|---|
| [Lattice dynamics workflow using Pheasy](https://github.com/materialsproject/atomate2/pull/1063) | merged Sep 2026 |
| [Harmonic lattice dynamics workflow using hiPhive](https://github.com/materialsproject/atomate2/pull/1062) | merged Sep 2026 |
| [Thermal expansion workflow (CTEMaker)](https://github.com/materialsproject/atomate2/pull/1559) | merged Oct 2026 |
| [Finite-temperature phonon workflow](https://github.com/materialsproject/atomate2/pull/1560) | in review |

### New features

| Pull request | Status |
|---|---|
| [Force field Born charges and dielectric tensors with MACE-Field (atomate2)](https://github.com/materialsproject/atomate2/pull/1573) | approved |
| [JobStore document format as a pydantic model (jobflow)](https://github.com/materialsproject/jobflow/pull/424) | merged Oct 2023 |
| [Integration of Matbench Discovery (matbench)](https://github.com/materialsproject/matbench/pull/236) | merged Mar 2023 |
| ["Go to page" navigation in the web GUI (FireWorks)](https://github.com/materialsproject/fireworks/pull/572) | merged Mar 2026 |
| [New mock decorator and config update (alabos)](https://github.com/CederGroupHub/alabos/pull/49) | merged Feb 2024 |

### Bug fixes

| Pull request | Status |
|---|---|
| [Fix pheasy anharmonic fitting and add fit options (atomate2)](https://github.com/materialsproject/atomate2/pull/1558) | merged Oct 2026 |
| [Fix the acoustic sum rule in PhononBSDOSDoc (emmet)](https://github.com/materialsproject/emmet/pull/1447) | merged May 2026 |
| [Fix the Clarke thermal conductivity key between pymatgen and atomate2 (atomate2)](https://github.com/materialsproject/atomate2/pull/1448) | merged Mar 2026 |
| Pydantic v2 migration of atomate2 ([#558](https://github.com/materialsproject/atomate2/pull/558), [#565](https://github.com/materialsproject/atomate2/pull/565), [#566](https://github.com/materialsproject/atomate2/pull/566), [#567](https://github.com/materialsproject/atomate2/pull/567)) | merged Oct 2023 |
| [Use dumpfn as the default JSON writer (matbench)](https://github.com/materialsproject/matbench/pull/251) | merged Apr 2023 |

### Documentation and citations

- atomate2: [phonon database preprint in the pheasy docs](https://github.com/materialsproject/atomate2/pull/1551), [Zenodo DOI](https://github.com/materialsproject/atomate2/pull/1211), [ChemRxiv citation](https://github.com/materialsproject/atomate2/pull/1107)
- matbench: [scaled error formula for classification tasks](https://github.com/materialsproject/matbench/pull/257), [link to Matbench Discovery on the leaderboard](https://github.com/materialsproject/matbench/pull/253)
- alabos: [tooling to streamline the commit and PR flow](https://github.com/CederGroupHub/alabos/pull/37), [installation docs](https://github.com/CederGroupHub/alabos/pull/46)
