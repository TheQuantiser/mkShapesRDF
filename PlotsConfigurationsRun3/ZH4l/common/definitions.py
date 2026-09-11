"""Small explicit records and a lazy compiler to ordinary mkShapes dictionaries.

All objects are source-indexed. Configuration choices are Python, numerical
expressions are C++/RDF. No record performs input discovery or remote I/O.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
import math
import re
from .naming import public_name


def identifier(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid identifier {name!r}")
    return name


@dataclass(frozen=True)
class Column:
    name: str
    expression: str
    dependencies: tuple = ()
    data_expression: str | None = None
    after_weight: bool = False
    declarations: tuple = ()
    setup: tuple = ()

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Source:
    name: str
    kind: str
    fields: tuple
    lineage: str
    identity: str

    def __getitem__(self, field):
        try:
            return dict(self.fields)[field]
        except KeyError:
            raise ValueError(f"Source {self.name} does not retain {field!r}") from None


@dataclass(frozen=True)
class View:
    name: str
    source: Source
    indices: Column
    electron_wp: str | None = None
    muon_wp: str | None = None


@dataclass(frozen=True)
class Candidate:
    name: str
    view: View
    policy: str
    valid: Column
    observables: tuple = ()

    @property
    def indices(self):
        return self.view.indices

    @property
    def leptons(self):
        return self.view

    @property
    def mass(self):
        return dict(self.observables)["mass"]

    @property
    def pt(self):
        return dict(self.observables)["pt"]

    @property
    def eta(self):
        return dict(self.observables)["eta"]

    @property
    def phi(self):
        return dict(self.observables)["phi"]


@dataclass(frozen=True)
class Correction:
    name: str
    target: View
    component: str
    value: Column
    valid: Column
    calibration: str
    variations: tuple = ()


@dataclass(frozen=True)
class Weight:
    name: str
    value: Column
    valid: Column
    factors: tuple
    normalization: str


@dataclass(frozen=True)
class Region:
    name: str
    selection: Column
    weight: Weight | None = None
    parent: Region | None = None


class Analysis:
    """Compose independent definitions; compile only output dependencies.

    The returned aliases/variables/cuts are plain dictionaries. They work with
    common.runner and the normal configuration serialization/batch interface.
    """

    def __init__(self):
        self.columns = {}
        self.regions = {}
        self.outputs = {}
        self.output_dependencies = {}

    def column(
        self,
        name,
        expression,
        *,
        dependencies=(),
        data_expression=None,
        after_weight=False,
        declarations=(),
        setup=(),
    ):
        public_name(name)
        dependencies = tuple(dependencies)
        if any(
            not isinstance(dep, Column) or self.columns.get(dep.name) != dep
            for dep in dependencies
        ):
            raise ValueError(f"{name}: dependencies must belong to this analysis")
        column = Column(
            name,
            str(expression),
            dependencies,
            data_expression,
            after_weight or any(dep.after_weight for dep in dependencies),
            tuple(declarations),
            tuple(setup),
        )
        if name in self.columns and self.columns[name] != column:
            raise ValueError(f"Conflicting definition for {name}")
        self.columns[name] = column
        return column

    def source(self, name, kind, fields, *, lineage, identity=None):
        """Declare retained field meanings and producer/kinematic lineage."""
        if kind not in {"lepton", "electron", "muon", "jet", "met"}:
            raise ValueError(f"Unsupported source kind {kind!r}")
        if not lineage:
            raise ValueError("A source must declare its retained representation")

        def field_name(field):
            return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", field).lower()

        columns = tuple(
            (field, self.column(f"zh4l_internal_{name}_{field_name(field)}", expr))
            for field, expr in fields.items()
        )
        return Source(
            identifier(name), kind, columns, str(lineage), str(identity or name)
        )

    def _helper(self, name, expression, dependencies):
        return self.column(
            name,
            expression,
            dependencies=dependencies,
            declarations=(
                f'#include "{Path(__file__).resolve().parent / "macros/views.h"}"',
            ),
        )

    def view(
        self,
        name,
        source,
        mask=None,
        *,
        dependencies=(),
        order="source",
        electron_wp=None,
        muon_wp=None,
    ):
        if source.kind == "met":
            raise ValueError(
                "MET is an event-level source; consume its fields directly"
            )
        if isinstance(mask, Column):
            dependencies = (*dependencies, mask)
        if order not in {"source", "pt"}:
            raise ValueError("View ordering must be source or pt")
        pt = source["pt"]
        mask = mask if mask is not None else f"ROOT::RVecB({pt}.size(),true)"
        idx = self._helper(
            f"{name}_index",
            f"ZH4lViews::indices({pt},({mask}),{str(order == 'pt').lower()})",
            (pt, *dependencies),
        )
        return View(identifier(name), source, idx, electron_wp, muon_wp)

    def subset(self, name, view, indices):
        if not isinstance(indices, Column) or self.columns.get(indices.name) != indices:
            raise TypeError("Subset indices must be an explicit source-index column")
        return View(
            identifier(name), view.source, indices, view.electron_wp, view.muon_wp
        )

    def without(self, name, view, excluded):
        excluded = excluded.view if isinstance(excluded, Candidate) else excluded
        if view.source != excluded.source:
            raise ValueError("Cannot subtract objects from different sources")
        idx = self._helper(
            f"{name}_index",
            f"ZH4lViews::without({view.indices},{excluded.indices})",
            (view.indices, excluded.indices),
        )
        return self.subset(name, view, idx)

    def union(self, name, *views):
        views = tuple(v.view if isinstance(v, Candidate) else v for v in views)
        if not views or any(v.source != views[0].source for v in views):
            raise ValueError(
                "Union requires views of one source and kinematic representation"
            )
        expr = str(views[0].indices)
        for view in views[1:]:
            expr = f"ZH4lViews::unite({expr},{view.indices})"
        idx = self._helper(f"{name}_index", expr, tuple(v.indices for v in views))
        # A union of different WPs has no single efficiency definition.
        same_wp = len({(v.electron_wp, v.muon_wp) for v in views}) == 1
        return View(
            identifier(name),
            views[0].source,
            idx,
            views[0].electron_wp if same_wp else None,
            views[0].muon_wp if same_wp else None,
        )

    def take(self, name, view, field):
        view = view.view if isinstance(view, Candidate) else view
        value = view.source[field]
        return self._helper(
            name, f"ZH4lViews::take({value},{view.indices})", (value, view.indices)
        )

    def combine(self, name, *candidates):
        """Combine disjoint selected candidates without choosing new members."""
        if len(candidates) < 2 or any(not isinstance(c, Candidate) for c in candidates):
            raise ValueError("Combine requires at least two selected candidates")
        view = self.union(f"{name}_lepton", *candidates)
        guards = [str(c.valid) for c in candidates]
        for i, candidate in enumerate(candidates):
            guards.extend(
                f"ZH4lViews::disjoint({earlier.indices},{candidate.indices})"
                for earlier in candidates[:i]
            )
        valid = self._helper(
            f"{name}_is_valid",
            " && ".join(guards),
            tuple(v for c in candidates for v in (c.valid, c.indices)),
        )
        args = tuple(view.source[field] for field in ("pt", "eta", "phi", "pdg_id"))
        observables = tuple(
            (
                quantity,
                self._helper(
                    f"{name}_{quantity}",
                    f"{valid} ? ZH4lViews::momentum({view.indices},{','.join(map(str, args))}).{method}() : -999.0",
                    (valid, view.indices, *args),
                ),
            )
            for quantity, method in (
                ("mass", "M"),
                ("pt", "Pt"),
                ("eta", "Eta"),
                ("phi", "Phi"),
            )
        )
        return Candidate(identifier(name), view, "disjoint_union", valid, observables)

    def pair(
        self,
        name,
        view,
        *,
        policy="nearest_z",
        min_pt=(25.0, 10.0),
        min_pass=2,
        charge="opposite",
        flavor="same",
        exclude=None,
    ):
        if view.source.kind not in {"lepton", "electron", "muon"}:
            raise ValueError("Pair construction requires a lepton source")
        if policy not in {"nearest_z", "highest_pt"}:
            raise ValueError("Pair policy must be nearest_z or highest_pt")
        if (
            len(min_pt) != 2
            or any(not math.isfinite(p) for p in min_pt)
            or min_pt[0] < min_pt[1]
            or min_pt[1] < 0
            or min_pass not in (0, 1, 2)
        ):
            raise ValueError("Invalid pair pT or ID requirements")
        if charge not in {"opposite", "same", "any"} or flavor not in {
            "same",
            "different",
            "any",
        }:
            raise ValueError("Invalid pair charge/flavor requirement")
        source = view.source
        if not view.electron_wp or not view.muon_wp:
            raise ValueError("Pair lepton WPs must be explicit")
        ele = source[f"electron_{view.electron_wp}"]
        mu = source[f"muon_{view.muon_wp}"]
        pool = (
            self.without(f"zh4l_internal_{name}_remaining_pool", view, exclude)
            if exclude
            else view
        )
        args = [source[field] for field in ("pt", "eta", "phi", "pdg_id")]
        deps = (pool.indices, *args, ele, mu)
        charge_code = {"opposite": -1, "same": 1, "any": 0}[charge]
        flavor_code = {"same": 1, "different": -1, "any": 0}[flavor]
        expression = (
            f"ZH4lViews::pair({pool.indices},{','.join(map(str, args))},{ele},{mu},"
            f"{str(policy == 'nearest_z').lower()},{min_pass},{float(min_pt[0])},{float(min_pt[1])},"
            f"{charge_code},{flavor_code})"
        )
        if isinstance(exclude, Candidate):
            expression = f"{exclude.valid} ? {expression} : ROOT::RVecI{{-1,-1}}"
            deps += (exclude.valid,)
        idx = self._helper(f"{name}_lepton_index", expression, deps)
        valid = self._helper(
            f"{name}_is_valid",
            f"ZH4lViews::valid({idx},{source['pt']}.size()) && {idx}.size()==2",
            (idx, source["pt"]),
        )
        candidate = Candidate(
            identifier(name), self.subset(name, view, idx), policy, valid
        )
        return replace(
            candidate,
            observables=tuple(
                (
                    quantity,
                    self.pair_observable(f"{name}_{quantity}", candidate, quantity),
                )
                for quantity in ("mass", "pt", "eta", "phi")
            ),
        )

    def quartet(self, name, view):
        """Highest-pT eligible quartet, distinct from Z-first assignment."""
        pt = view.source["pt"]
        idx = self._helper(
            f"{name}_lepton_index",
            f"ZH4lViews::leading({view.indices},{pt},4)",
            (view.indices, pt),
        )
        return self.subset(name, view, idx)

    def pair_observable(self, name, candidate, quantity):
        methods = {
            "mass": "pairMass",
            "pt": "pairPt",
            "eta": "pairEta",
            "phi": "pairPhi",
        }
        if quantity not in methods:
            raise ValueError(f"Unsupported pair observable {quantity}")
        args = tuple(
            candidate.view.source[field] for field in ("pt", "eta", "phi", "pdg_id")
        ) + (candidate.indices,)
        return self._helper(
            name, f"FourLepton::{methods[quantity]}({','.join(map(str, args))})", args
        )

    def correction(
        self,
        name,
        target,
        component,
        expression,
        *,
        dependencies=(),
        valid="true",
        calibration,
        variations=(),
        setup=(),
        declarations=(),
    ):
        target = target.view if isinstance(target, Candidate) else target
        if variations:
            raise ValueError(
                "Variation evaluation is reserved for future nuisance integration"
            )
        if not component or not calibration:
            raise ValueError(
                "Corrections require a component and calibration definition"
            )
        value = self.column(
            name,
            expression,
            dependencies=dependencies,
            data_expression="1.f",
            setup=setup,
            declarations=declarations,
        )
        validity = self.column(
            f"{name}_is_valid",
            f"({valid}) && std::isfinite({value})",
            dependencies=(value, *dependencies),
            data_expression="true",
        )
        return Correction(
            identifier(name), target, component, value, validity, calibration
        )

    def lepton_sf(self, name, target):
        target = target.view if isinstance(target, Candidate) else target
        if not target.electron_wp or not target.muon_wp:
            raise ValueError(
                "A lepton SF requires one declared WP per flavor; correct different-WP views separately"
            )
        source = target.source
        ele, mu = (
            source[f"electron_sf_{target.electron_wp}"],
            source[f"muon_sf_{target.muon_wp}"],
        )
        pdg = source["pdg_id"]
        ele_pass, mu_pass = (
            source[f"electron_{target.electron_wp}"],
            source[f"muon_{target.muon_wp}"],
        )
        return self.correction(
            name,
            target,
            "lepton_total",
            f"ZH4lViews::leptonSF({pdg},{target.indices},{ele},{mu})",
            dependencies=(pdg, target.indices, ele, mu, ele_pass, mu_pass),
            valid=f"ZH4lViews::allPass({pdg},{target.indices},{ele_pass},{mu_pass})",
            calibration=f"{source.lineage}:{target.electron_wp}:{target.muon_wp}:TotSF",
            declarations=(
                f'#include "{Path(__file__).resolve().parent / "macros/views.h"}"',
            ),
        )

    def weight(
        self,
        name,
        *factors,
        base="weight",
        normalization="native sample weight including luminosity and component factors",
    ):
        """Build a total recipe. base='1.0' is a literal unnormalized count."""
        added_factors = factors
        if isinstance(base, Weight):
            factors = base.factors + factors
            normalization = base.normalization
        if any(not isinstance(factor, Correction) for factor in factors):
            raise TypeError(
                "Weight factors must be corrections with explicit targets/components"
            )
        if len({factor.name for factor in factors}) != len(factors):
            raise ValueError("A correction factor cannot be applied twice")
        if str(base) in {"1", "1.f", "1.0", "1."}:
            normalization = "literal count; no luminosity or sample normalization"
        deps, validity = [], []
        for i, factor in enumerate(factors):
            deps.extend((factor.value, factor.valid))
            validity.append(str(factor.valid))
            for earlier in factors[:i]:
                if (
                    earlier.component != factor.component
                    or earlier.target.source.identity != factor.target.source.identity
                ):
                    continue
                if (
                    factor.component.startswith("trigger")
                    or earlier.target.indices == factor.target.indices
                ):
                    raise ValueError(
                        f"Overlapping efficiency component {factor.component}"
                    )
                guard = self._helper(
                    f"{name}_disjoint_{i}_{earlier.name}",
                    f"ZH4lViews::disjoint({earlier.target.indices},{factor.target.indices})",
                    (earlier.target.indices, factor.target.indices),
                )
                deps.append(guard)
                validity.append(str(guard))
        if isinstance(base, Weight):
            deps.extend((base.value, base.valid))
            validity.append(str(base.valid))
            base = base.value
        if isinstance(base, Column):
            deps.append(base)
        expr = " * ".join(
            [f"({base})", *(str(factor.value) for factor in added_factors)]
        )
        validity.append(f"std::isfinite({expr})")
        valid = self.column(
            f"{name}_is_valid",
            " && ".join(validity),
            dependencies=deps,
            after_weight=True,
        )
        value = self.column(
            name,
            f"{valid} ? ({expr}) : std::numeric_limits<double>::quiet_NaN()",
            dependencies=(*deps, valid),
            after_weight=True,
            declarations=("#include <limits>",),
        )
        return Weight(identifier(name), value, valid, tuple(factors), normalization)

    def region(self, name, expression, *, dependencies=(), parent=None, weight=None):
        if isinstance(expression, Column):
            dependencies = (*dependencies, expression)
        if name in self.regions:
            raise ValueError(f"Duplicate region {name}")
        if parent is not None:
            expression = f"({parent.selection}) && ({expression})"
            dependencies = (parent.selection, *dependencies)
            weight = parent.weight if weight is None else weight
        selection = self.column(
            f"region_{name}_pass", expression, dependencies=dependencies
        )
        if selection.after_weight:
            raise ValueError("Region selection must not depend on an event weight")
        region = Region(identifier(name), selection, weight, parent)
        self.regions[name] = region
        return region

    def histogram(
        self,
        name,
        observable,
        edges,
        *,
        regions,
        weight=None,
        valid=None,
        title="",
        fold=0,
    ):
        regions = tuple(regions)
        if not regions or any(
            self.regions.get(region.name) != region for region in regions
        ):
            raise ValueError("Histogram regions must belong to this analysis")
        edges = tuple(float(edge) for edge in edges)
        if (
            len(edges) < 2
            or any(not math.isfinite(edge) for edge in edges)
            or any(b <= a for a, b in zip(edges, edges[1:]))
            or fold not in range(4)
        ):
            raise ValueError("Invalid histogram axis or flow policy")
        definition = {
            "name": str(observable),
            "range": (edges,),
            "xaxis": title,
            "fold": fold,
            "cuts": [r.name for r in regions],
        }
        roots = [observable]
        if valid is not None:
            definition["valid"] = str(valid)
            roots.append(valid)
        if weight is None:
            choices = {r.weight for r in regions}
            if len(choices) == 1:
                weight = next(iter(choices))
            else:
                definition["regionWeights"] = {
                    r.name: str(r.weight.value) if r.weight is not None else "weight"
                    for r in regions
                }
                roots.extend(
                    column
                    for r in regions
                    if r.weight is not None
                    for column in (r.weight.value, r.weight.valid)
                )
        if weight is not None:
            definition["weight"] = str(weight.value)
            roots.extend((weight.value, weight.valid))
        self._add_output(name, definition, roots)

    def tree(self, name, branches, *, regions, weight=None, tree_name="Events"):
        regions = tuple(regions)
        if not regions or any(
            self.regions.get(region.name) != region for region in regions
        ):
            raise ValueError("Tree regions must belong to this analysis")
        mapping = {}
        roots = []
        for group in branches if isinstance(branches, (list, tuple)) else [branches]:
            for field, value in group.items():
                if field in mapping:
                    raise ValueError(f"Duplicate tree field {field}")
                mapping[identifier(field)] = str(value)
                if isinstance(value, Column):
                    roots.append(value)
        if weight is not None:
            if "weight" in mapping:
                raise ValueError("Specify tree weight once")
            mapping["weight"] = str(weight.value)
            if "weight_is_valid" in mapping:
                raise ValueError("The chosen tree weight owns weight_is_valid")
            mapping["weight_is_valid"] = str(weight.valid)
            roots.extend((weight.value, weight.valid))
        elif any(region.weight is not None for region in regions):
            raise ValueError(
                "A tree spanning weighted regions must choose its exported weight explicitly"
            )
        self._add_output(
            name,
            {
                "tree": mapping,
                "cuts": [r.name for r in regions],
                "treeName": identifier(tree_name),
                "rowUnit": "event",
            },
            roots,
        )

    def _add_output(self, name, definition, roots):
        if name in self.outputs:
            raise ValueError(f"Duplicate output {name}")
        public_name(name)
        columns = tuple(root for root in roots if isinstance(root, Column))
        if any(self.columns.get(column.name) != column for column in columns):
            raise ValueError("Output dependencies must belong to this analysis")
        self.outputs[name] = definition
        self.output_dependencies[name] = columns

    # compile is the public graph-to-configuration API.
    def compile(self, *, mode="both", preselections="1"):  # noqa: A003
        if mode not in {"histograms", "trees", "both"}:
            raise ValueError("Output mode must be histograms, trees or both")
        variables = {
            name: deepcopy(cfg)
            for name, cfg in self.outputs.items()
            if mode == "both" or ("tree" in cfg) == (mode == "trees")
        }
        if not variables:
            raise ValueError(f"No {mode} outputs were requested")
        active = {cut for cfg in variables.values() for cut in cfg["cuts"]}
        if not active <= self.regions.keys():
            raise ValueError("An output references an unregistered region")
        # Explicit dependencies are the authoritative graph; output expressions
        # are names of registered columns, with raw tree pass-through permitted.
        roots = [
            self.regions[name].selection for name in self.regions if name in active
        ]
        if isinstance(preselections, Column):
            if (
                self.columns.get(preselections.name) != preselections
                or preselections.after_weight
            ):
                raise ValueError(
                    "Preselection must be an unweighted column from this analysis"
                )
            roots.append(preselections)
        for name, cfg in variables.items():
            roots.extend(self.output_dependencies[name])
            names = list(cfg.get("tree", {}).values()) + [
                cfg.get(key) for key in ("name", "valid", "weight")
            ]
            roots.extend(self.columns[name] for name in names if name in self.columns)
        ordered = {}

        def visit(column):
            if column.name in ordered:
                return
            for dep in column.dependencies:
                visit(dep)
            definition = {"expr": column.expression}
            if column.data_expression is not None:
                definition["dataExpr"] = column.data_expression
            if column.after_weight:
                definition["afterNuis"] = True
            if column.declarations:
                definition["linesToAdd"] = list(column.declarations)
            if column.setup:
                definition["linesToProcess"] = list(column.setup)
            ordered[column.name] = definition

        for column in roots:
            visit(column)
        return {
            "aliases": ordered,
            "cuts": {
                name: str(self.regions[name].selection)
                for name in self.regions
                if name in active
            },
            "preselections": str(preselections),
            "variables": variables,
            "nuisances": {},
        }
