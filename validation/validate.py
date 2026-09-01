#!/usr/bin/env python3
"""
Lightweight, dependency-light consistency checks for the InfinityForge
Tracking Module repository.

This is NOT a full JSON Schema validator, and it is NOT wired into CI. It
exists to catch the most common mistakes before a pull request: duplicate
event or metric names, missing required documentation fields, examples that
don't match their event/metric definitions, and forbidden vendor/framework
terms leaking into the platform-independent contract.

Requires: pyyaml (`pip install pyyaml --break-system-packages`, or on the
user's own machine, whatever is already installed there).

Usage:
    python3 validation/validate.py
Exit code is non-zero if any check fails.
"""

import glob
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install it with `pip install pyyaml`.")
    sys.exit(2)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ALLOWED_TYPES = {"string", "integer", "number", "boolean", "timestamp", "enum", "object", "array"}
ALLOWED_ENVIRONMENTS = {"development", "preview", "production"}
ALLOWED_PLATFORMS = {"ios", "android", "web", "other"}
RESERVED_ENVELOPE_FIELDS = {
    "event", "schema_version", "timestamp", "app_id", "environment", "platform",
    "sdk_version", "sdk_name", "app_version", "user_id", "anonymous_id", "properties",
}
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")

# Metric-specific constants (schema/metric-envelope.yaml, schema/metric-dimensions.yaml,
# schema/common-types.yaml's metric_unit/metric_source $defs).
ALLOWED_DIMENSION_TYPES = {"string", "integer", "boolean", "enum"}
ALLOWED_METRIC_UNITS = {"currency", "count", "impression", "millisecond", "second", "other"}
ALLOWED_METRIC_SOURCES = {
    "application", "billing_system", "advertising_system", "operating_system",
    "network", "provider", "other",
}
RESERVED_METRIC_ENVELOPE_FIELDS = {
    "metric_name", "schema_version", "value", "unit", "currency", "source",
    "reference_id", "timestamp", "app_id", "environment", "platform",
    "sdk_version", "sdk_name", "app_version", "user_id", "anonymous_id", "dimensions",
}

# Terms that must never appear in the platform-independent contract. Checked
# case-insensitively against specification/, events/, metrics/, schema/, and
# examples/ — docs/implementation-guide.md is explicitly allowed to name
# providers, per specification/versioning.md and step 17 of the repository's
# design brief.
FORBIDDEN_TERMS = [
    "firebase", "crashlytics", "amplitude", "mixpanel", "posthog", "segment",
    "rudderstack", "expo-router", "expo router", "react navigation",
    "swiftui", "uikit", "jetpack compose",
    "admob", "revenuecat", "google analytics",
]
SCANNED_DIRS_FOR_FORBIDDEN_TERMS = ["specification", "events", "metrics", "schema", "examples"]

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def check_forbidden_terms():
    for d in SCANNED_DIRS_FOR_FORBIDDEN_TERMS:
        dir_path = os.path.join(REPO_ROOT, d)
        for root, _, files in os.walk(dir_path):
            for name in files:
                if not (name.endswith(".md") or name.endswith(".yaml") or name.endswith(".yml")):
                    continue
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                lower = text.lower()
                for term in FORBIDDEN_TERMS:
                    if term in lower:
                        fail(f"Forbidden vendor/framework term '{term}' found in {os.path.relpath(path, REPO_ROOT)} "
                             f"(specification/, events/, metrics/, schema/, and examples/ must remain "
                             f"platform- and vendor-independent)")


def check_event_files():
    event_files = sorted(glob.glob(os.path.join(REPO_ROOT, "events", "*.yaml")))
    if not event_files:
        fail("No event definition files found under events/")
        return {}, []

    all_names = {}
    all_events = []

    for path in event_files:
        rel = os.path.relpath(path, REPO_ROOT)
        try:
            data = load_yaml(path)
        except yaml.YAMLError as e:
            fail(f"{rel}: invalid YAML ({e})")
            continue

        if "category" not in data:
            fail(f"{rel}: missing top-level 'category'")
        if "events" not in data or not isinstance(data["events"], list):
            fail(f"{rel}: missing or invalid top-level 'events' list")
            continue

        for ev in data["events"]:
            name = ev.get("name")
            all_events.append((rel, ev))

            if not name:
                fail(f"{rel}: an event is missing 'name'")
                continue
            if not IDENTIFIER_RE.match(name):
                fail(f"{rel}: event name '{name}' is not snake_case")
            if name in all_names:
                fail(f"Duplicate event name '{name}' found in both {all_names[name]} and {rel}")
            else:
                all_names[name] = rel

            for required_field in ("description", "trigger", "purpose", "schema_version", "properties"):
                if required_field not in ev:
                    fail(f"{rel}: event '{name}' is missing required field '{required_field}'")

            if "schema_version" in ev and not isinstance(ev["schema_version"], int):
                fail(f"{rel}: event '{name}' schema_version must be an integer")

            for prop in ev.get("properties", []) or []:
                pname = prop.get("name")
                if not pname:
                    fail(f"{rel}: event '{name}' has a property with no 'name'")
                    continue
                if not IDENTIFIER_RE.match(pname):
                    fail(f"{rel}: event '{name}' property '{pname}' is not snake_case")
                if pname in RESERVED_ENVELOPE_FIELDS:
                    fail(f"{rel}: event '{name}' property '{pname}' collides with a reserved envelope field name")
                ptype = prop.get("type")
                if ptype not in ALLOWED_TYPES:
                    fail(f"{rel}: event '{name}' property '{pname}' has invalid type '{ptype}'")
                if ptype == "enum" and not prop.get("allowed_values"):
                    fail(f"{rel}: event '{name}' property '{pname}' is type 'enum' but has no 'allowed_values'")
                if ptype != "enum" and prop.get("allowed_values"):
                    fail(f"{rel}: event '{name}' property '{pname}' has 'allowed_values' but type is '{ptype}', not 'enum'")
                for bool_field in ("required", "common"):
                    if not isinstance(prop.get(bool_field), bool):
                        fail(f"{rel}: event '{name}' property '{pname}' field '{bool_field}' must be true/false")
                if "description" not in prop or not prop["description"]:
                    fail(f"{rel}: event '{name}' property '{pname}' is missing a description")

    return all_names, all_events


def check_examples(event_names):
    payload_dir = os.path.join(REPO_ROOT, "examples", "payloads")
    payload_files = sorted(glob.glob(os.path.join(payload_dir, "*.json")))

    covered = set()
    for path in payload_files:
        rel = os.path.relpath(path, REPO_ROOT)
        try:
            data = load_json(path)
        except json.JSONDecodeError as e:
            fail(f"{rel}: invalid JSON ({e})")
            continue

        for required_field in ("event", "schema_version", "timestamp", "app_id",
                                "environment", "platform", "sdk_version",
                                "app_version", "anonymous_id"):
            if required_field not in data:
                fail(f"{rel}: example payload is missing required envelope field '{required_field}'")

        ev_name = data.get("event")
        if ev_name:
            covered.add(ev_name)
            if ev_name not in event_names:
                fail(f"{rel}: 'event' value '{ev_name}' does not match any defined event in events/*.yaml")

        env = data.get("environment")
        if env and env not in ALLOWED_ENVIRONMENTS:
            fail(f"{rel}: environment '{env}' is not one of {sorted(ALLOWED_ENVIRONMENTS)}")

        plat = data.get("platform")
        if plat and plat not in ALLOWED_PLATFORMS:
            fail(f"{rel}: platform '{plat}' is not one of {sorted(ALLOWED_PLATFORMS)}")

    missing = set(event_names) - covered
    if missing:
        warn(f"No example payload found under examples/payloads/ for: {sorted(missing)}")


def check_metric_files():
    metric_files = sorted(glob.glob(os.path.join(REPO_ROOT, "metrics", "*.yaml")))
    if not metric_files:
        warn("No metric definition files found under metrics/")
        return {}, []

    all_names = {}
    all_metrics = []

    for path in metric_files:
        rel = os.path.relpath(path, REPO_ROOT)
        try:
            data = load_yaml(path)
        except yaml.YAMLError as e:
            fail(f"{rel}: invalid YAML ({e})")
            continue

        if "category" not in data:
            fail(f"{rel}: missing top-level 'category'")
        if "metrics" not in data or not isinstance(data["metrics"], list):
            fail(f"{rel}: missing or invalid top-level 'metrics' list")
            continue

        for metric in data["metrics"]:
            name = metric.get("name")
            all_metrics.append((rel, metric))

            if not name:
                fail(f"{rel}: a metric is missing 'name'")
                continue
            if not IDENTIFIER_RE.match(name):
                fail(f"{rel}: metric name '{name}' is not snake_case")
            if name in all_names:
                fail(f"Duplicate metric name '{name}' found in both {all_names[name]} and {rel}")
            else:
                all_names[name] = rel

            for required_field in ("description", "trigger", "purpose", "schema_version",
                                    "unit", "typical_source", "dimensions", "example"):
                if required_field not in metric:
                    fail(f"{rel}: metric '{name}' is missing required field '{required_field}'")

            if "schema_version" in metric and not isinstance(metric["schema_version"], int):
                fail(f"{rel}: metric '{name}' schema_version must be an integer")

            unit = metric.get("unit")
            if unit is not None and unit not in ALLOWED_METRIC_UNITS:
                fail(f"{rel}: metric '{name}' has invalid unit '{unit}' "
                     f"(must be one of {sorted(ALLOWED_METRIC_UNITS)})")

            typical_source = metric.get("typical_source")
            if typical_source is not None and typical_source not in ALLOWED_METRIC_SOURCES:
                fail(f"{rel}: metric '{name}' has invalid typical_source '{typical_source}' "
                     f"(must be one of {sorted(ALLOWED_METRIC_SOURCES)})")

            example_path = metric.get("example")
            if example_path and not os.path.isfile(os.path.join(REPO_ROOT, example_path)):
                fail(f"{rel}: metric '{name}' 'example' points to a nonexistent file: {example_path}")

            if "fixed_value" in metric and (
                not isinstance(metric["fixed_value"], (int, float))
                or isinstance(metric["fixed_value"], bool)
                or metric["fixed_value"] < 0
            ):
                fail(f"{rel}: metric '{name}' 'fixed_value' must be a non-negative number")

            for dim in metric.get("dimensions", []) or []:
                dname = dim.get("name")
                if not dname:
                    fail(f"{rel}: metric '{name}' has a dimension with no 'name'")
                    continue
                if not IDENTIFIER_RE.match(dname):
                    fail(f"{rel}: metric '{name}' dimension '{dname}' is not snake_case")
                if dname in RESERVED_METRIC_ENVELOPE_FIELDS:
                    fail(f"{rel}: metric '{name}' dimension '{dname}' collides with a reserved envelope field name")
                dtype = dim.get("type")
                if dtype not in ALLOWED_DIMENSION_TYPES:
                    fail(f"{rel}: metric '{name}' dimension '{dname}' has invalid type '{dtype}' "
                         f"(must be one of {sorted(ALLOWED_DIMENSION_TYPES)} — dimensions use a narrower "
                         f"type set than event properties)")
                if dtype == "enum" and not dim.get("allowed_values"):
                    fail(f"{rel}: metric '{name}' dimension '{dname}' is type 'enum' but has no 'allowed_values'")
                if dtype != "enum" and dim.get("allowed_values"):
                    fail(f"{rel}: metric '{name}' dimension '{dname}' has 'allowed_values' but type is '{dtype}', not 'enum'")
                if not isinstance(dim.get("required"), bool):
                    fail(f"{rel}: metric '{name}' dimension '{dname}' field 'required' must be true/false")
                if "description" not in dim or not dim["description"]:
                    fail(f"{rel}: metric '{name}' dimension '{dname}' is missing a description")

    return all_names, all_metrics


def check_metric_examples(metric_names, fixed_values=None):
    fixed_values = fixed_values or {}
    example_dir = os.path.join(REPO_ROOT, "examples", "metrics")
    example_files = sorted(glob.glob(os.path.join(example_dir, "*.json")))

    covered = set()
    for path in example_files:
        rel = os.path.relpath(path, REPO_ROOT)
        try:
            data = load_json(path)
        except json.JSONDecodeError as e:
            fail(f"{rel}: invalid JSON ({e})")
            continue

        for required_field in ("metric_name", "schema_version", "value", "unit", "source",
                                "timestamp", "app_id", "environment", "platform",
                                "sdk_version", "app_version", "anonymous_id"):
            if required_field not in data:
                fail(f"{rel}: example metric payload is missing required envelope field '{required_field}'")

        metric_name = data.get("metric_name")
        if metric_name:
            covered.add(metric_name)
            if metric_name not in metric_names:
                fail(f"{rel}: 'metric_name' value '{metric_name}' does not match any defined metric in metrics/*.yaml")

        unit = data.get("unit")
        if unit is not None and unit not in ALLOWED_METRIC_UNITS:
            fail(f"{rel}: unit '{unit}' is not one of {sorted(ALLOWED_METRIC_UNITS)}")

        currency = data.get("currency")
        if unit == "currency" and not currency:
            fail(f"{rel}: unit is 'currency' but 'currency' field is missing")
        if unit is not None and unit != "currency" and currency:
            fail(f"{rel}: unit is '{unit}' (not 'currency') but 'currency' field is present")

        value = data.get("value")
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
            fail(f"{rel}: 'value' must be a non-negative number, got {value!r}")
        elif metric_name in fixed_values and value != fixed_values[metric_name]:
            fail(f"{rel}: metric '{metric_name}' fixes value to {fixed_values[metric_name]!r} "
                 f"(metrics/*.yaml 'fixed_value'), but this example has value {value!r}")

        source = data.get("source")
        if source is not None and source not in ALLOWED_METRIC_SOURCES:
            fail(f"{rel}: source '{source}' is not one of {sorted(ALLOWED_METRIC_SOURCES)}")

        env = data.get("environment")
        if env and env not in ALLOWED_ENVIRONMENTS:
            fail(f"{rel}: environment '{env}' is not one of {sorted(ALLOWED_ENVIRONMENTS)}")

        plat = data.get("platform")
        if plat and plat not in ALLOWED_PLATFORMS:
            fail(f"{rel}: platform '{plat}' is not one of {sorted(ALLOWED_PLATFORMS)}")

        for dim_key in (data.get("dimensions") or {}):
            if dim_key in RESERVED_METRIC_ENVELOPE_FIELDS:
                fail(f"{rel}: dimension key '{dim_key}' collides with a reserved envelope field name")
            if not IDENTIFIER_RE.match(dim_key):
                fail(f"{rel}: dimension key '{dim_key}' is not snake_case")

    missing = set(metric_names) - covered
    if missing:
        warn(f"No example payload found under examples/metrics/ for: {sorted(missing)}")


def check_schema_files_parse():
    for path in sorted(glob.glob(os.path.join(REPO_ROOT, "schema", "*.yaml"))):
        rel = os.path.relpath(path, REPO_ROOT)
        try:
            load_yaml(path)
        except yaml.YAMLError as e:
            fail(f"{rel}: invalid YAML ({e})")


def main():
    check_forbidden_terms()
    check_schema_files_parse()
    event_names, _ = check_event_files()
    check_examples(event_names)
    metric_names, all_metrics = check_metric_files()
    fixed_values = {
        m.get("name"): m["fixed_value"]
        for _, m in all_metrics
        if "fixed_value" in m and m.get("name")
    }
    check_metric_examples(metric_names, fixed_values)

    print(f"Checked {len(event_names)} event definitions and {len(metric_names)} metric definitions.")

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  WARN: {w}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  ERROR: {e}")
        print("\nFAILED")
        sys.exit(1)

    print("\nOK — no errors found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
