# ZH4l naming contract

All ZH4l-defined columns use lowercase `snake_case`. Names identify the
object or domain first, then its property. Definitions, selections, correction
factors and composed event weights are separate concepts. Histogram and tree
projections use the same vocabulary.

| Meaning | Convention | Examples |
|---|---|---|
| Candidate or object property | `<object>_<property>` | `z_mass`, `x_pt`, `zx_min_pair_mass` |
| Constituent source indices | `<candidate>_<collection>_index` | `z_lepton_index`, `x_lepton_index`, `pairing_quartet_lepton_index` |
| View membership | `<view>_index` | `z_pool_index`, `accepted_jets_index` |
| Validity or classification | `<object>_is_<property>` | `z_is_valid`, `x_is_same_flavor` |
| Selection predicate | `<domain>_pass_<selection>` | `z_pass_ordered_pt`, `event_pass_b_veto` |
| Multiplicity | `<collection>_count` | `veto_lepton_count`, `extra_tight_lepton_count` |
| Scale-factor component | `sf_<component>_<domain>` | `sf_lepton_z`, `sf_lepton_zx`, `sf_trigger_zx` |
| Decision correction | `sf_<decision>` | `sf_b_veto` |
| Composed event weight | `weight_<recipe>` | `weight_raw`, `weight_nominal`, `weight_abs_nominal` |
| Internal column | `zh4l_internal_<meaning>` | `zh4l_internal_pairing_result` |

`z` and `x` denote selected candidates; `zx` denotes their union. A
quartet selected before pair assignment is `pairing_quartet`, because its
membership can differ from the Z-first union when extra leptons exist.
Use `mass`, `pt`, `eta`, `phi`, `delta_r`, `delta_phi`, `charge`, and
`abs_rapidity` consistently. Mass and momentum axes carry GeV in their labels;
the spelling does not introduce an implicit unit conversion.

An `index` column may be a vector. Its name states what collection it indexes,
and its definition fixes cardinality and order. `z_lepton_index` contains
original `Lepton` indices, ordered by the selected pair's pT. It does not
index a separately sorted electron, muon, or SF array. Explicitly retain the
native index maps when crossing collections.

For alternative definitions, prefix the object/domain consistently, for
example `loose_z_mass` and `sf_lepton_loose_z`. A prefix provides a readable
name; the source identity, kinematic lineage, membership, WPs and calibration
in the definition establish its meaning. Do not infer correction applicability
from the spelling of a region or sample.

Existing upstream branch names are preserved verbatim, including
`Lepton_pt`, `Lepton_pdgId`, `PuppiMET_pt`, `PV_npvsGood`, `XSWeight`,
`run`, `luminosityBlock`, and `event`. Direct pass-through histogram/tree
fields can retain those names. Preserve upstream WP identifiers, official
sample identifiers, environment variables, region labels, and existing C++
kernel/member names as well. The Python alias is the boundary between those
interfaces and ZH4l's public vocabulary. Region labels such as `ZZCR`,
`SR_XSF`, and `S0_ZZCR` remain stable.

The existing ZZCR nuisance route uses lower-case variation suffixes on
ZH4l aliases, such as `sf_lepton_zx_electron_up`. Upstream branch suffixes
and official nuisance/correlation identifiers retain their native spelling.
The new nominal tools reserve variation metadata but reject non-nominal
evaluation.

## Migration examples

| Previous ZH4l column | Current column |
|---|---|
| `Z_idx`, `X_idx` | `z_lepton_index`, `x_lepton_index` |
| `mZ`, `ptZ`, `mX`, `ptX` | `z_mass`, `z_pt`, `x_mass`, `x_pt` |
| `m4l`, `pt4l`, `minMll4l` | `zx_mass`, `zx_pt`, `zx_min_pair_mass` |
| `validZX`, `pass4lPt` | `zx_is_valid`, `zx_pass_ordered_pt` |
| `bVeto`, `bVetoSF` | `event_pass_b_veto`, `sf_b_veto` |
| `LepSF_ZX`, `TriggerSF_ZX` | `sf_lepton_zx`, `sf_trigger_zx` |
| `StudyRawWeight`, `StudySignedWeight` | `weight_raw`, `weight_nominal` |
| `PairingM4l` | `pairing_quartet_mass` |

The full historical column map in [common/naming.py](common/naming.py)
supports comparison tools and frozen expression tests. It does not install
duplicate runtime aliases. Recompile configurations after this migration;
old pickles retain old expressions and old histogram files retain old keys.
Current plotting and summary readers consume the new keys. Historical
reports and their stable summary JSON field names remain historical records.
