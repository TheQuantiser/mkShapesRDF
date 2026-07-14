"""
Legacy ZZ_CR JDL hook intentionally disabled in the master migration.

Remote output is handled by mkShapesRDF.lib.remote_io through the framework
BatchSubmission path.  Keeping a runnable custom JDL here would reintroduce
the old stage-out shell logic, including stale-destination acceptance after a
failed xrdcp.  configuration.py therefore sets jdlconfigfile = "".
"""

raise RuntimeError(
    "ZZ_CR uses framework-managed remote_io stage-out; do not use jdl_dict_zzcr.py."
)
